import time
from datetime import timedelta
import json
import urllib.request
import urllib.error

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Game, Room
from .services import COUNTDOWN_SECONDS, can_start, call_next_number, get_or_create_waiting_game, start_game


def _broadcast(room_id: int, payload: dict):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"room_{room_id}_lobby",
        {
            "type": "game.event",
            "payload": payload,
        },
    )


def _send_player_notification(telegram_id: int, text: str):
    token = str(getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    if not token:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": int(telegram_id), "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=8).read()
    except (urllib.error.URLError, ValueError, OSError):
        # Notification failures should never block game flow.
        pass


def _notify_game_started_players(game: Game):
    players = (
        game.players.select_related("user")
        .filter(removed_for_fake_bingo=False)
        .exclude(user__telegram_id__isnull=True)
    )
    room_bet = game.room.bet_amount
    for gp in players:
        _send_player_notification(
            int(gp.user.telegram_id),
            f"ጨዋታ #{game.id} ተጀምሯል። ሩም: {room_bet} ብር። ወደ ሚኒ አፕ ይግቡ እና ይጫወቱ።",
        )


@shared_task
def start_game_after_countdown(game_id: int):
    game = Game.objects.select_related("room").filter(id=game_id).first()
    if not game:
        return
    if game.status != "waiting" or game.total_players < 2:
        return
    if not game.countdown_started_at:
        return
    if timezone.now() < game.countdown_started_at + timedelta(seconds=COUNTDOWN_SECONDS):
        return

    start_game(game)
    _notify_game_started_players(game)
    _broadcast(
        game.room_id,
        {
            "event": "game_started",
            "game_id": game.id,
            "started_at": game.start_time.isoformat() if game.start_time else None,
        },
    )
    run_game_calls.delay(game.id)


@shared_task
def open_next_waiting_game(room_id: int):
    with transaction.atomic():
        room = Room.objects.select_for_update().filter(id=room_id).first()
        if not room:
            return
        running_exists = Game.objects.filter(room=room, status="running").exists()
        waiting_exists = Game.objects.filter(room=room, status="waiting").exists()
        if not running_exists and not waiting_exists:
            Game.objects.create(room=room, status="waiting")


@shared_task
def run_game_calls(game_id: int):
    game = Game.objects.select_related("room").filter(id=game_id).first()
    if not game:
        return
    if game.status != "running":
        return

    while True:
        game.refresh_from_db()
        if game.status != "running":
            break

        # Keep game alive until a valid bingo claim finishes it.
        # Call each number at most once.
        if len(game.called_numbers) >= 75:
            time.sleep(1)
            continue

        number = call_next_number(game)
        _broadcast(
            game.room_id,
            {"event": "number_called", "number": number, "called_numbers": game.called_numbers},
        )
        time.sleep(2)


@shared_task
def room_game_loop(room_id: int):
    room = Room.objects.filter(id=room_id, is_active=True).first()
    if not room:
        return
    game = Game.objects.filter(room=room, status="running").order_by("-id").first()
    if game:
        return
    game = get_or_create_waiting_game(room)

    if game.status == "waiting" and can_start(game):
        if not game.countdown_started_at:
            game.countdown_started_at = timezone.now()
            game.save(update_fields=["countdown_started_at"])
            start_game_after_countdown.apply_async(args=[game.id], countdown=COUNTDOWN_SECONDS)
            _broadcast(
                room.id,
                {
                    "event": "countdown_started",
                    "seconds": COUNTDOWN_SECONDS,
                    "starts_at": (game.countdown_started_at + timedelta(seconds=COUNTDOWN_SECONDS)).isoformat(),
                },
            )
        elif timezone.now() >= game.countdown_started_at + timedelta(seconds=COUNTDOWN_SECONDS):
            start_game(game)
            _notify_game_started_players(game)
            _broadcast(
                room.id,
                {
                    "event": "game_started",
                    "game_id": game.id,
                    "started_at": game.start_time.isoformat() if game.start_time else None,
                },
            )
            run_game_calls.delay(game.id)


@shared_task
def room_game_loop_all():
    for room_id in Room.objects.filter(is_active=True).values_list("id", flat=True):
        room_game_loop(room_id)
