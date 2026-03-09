import random
from datetime import timedelta
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from channels.layers import get_channel_layer

from apps.wallet.services import WalletError
from apps.wallet.models import Transaction

from .deduction import calculate_prize
from .models import Cartela, Game, GameAuditLog, GamePlayer, Room

User = get_user_model()
COUNTDOWN_SECONDS = 30


def _broadcast(room_id: int, payload: dict):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"room_{room_id}_lobby",
        {
            "type": "game.event",
            "payload": payload,
        },
    )


class GameServiceError(Exception):
    pass


def get_or_create_waiting_game(room: Room) -> Game:
    running = Game.objects.filter(room=room, status="running").order_by("-id").first()
    if running:
        raise GameServiceError("Game is currently running. Wait for it to finish.")
    game = Game.objects.filter(room=room, status="waiting").order_by("-id").first()
    if game:
        return game
    return Game.objects.create(room=room, status="waiting")


def join_game(user_id: int, room_id: int, cartela_id: int) -> GamePlayer:
    with transaction.atomic():
        user = User.objects.select_for_update().get(id=user_id, is_active=True, is_banned=False)
        if not user.phone_number:
            raise GameServiceError("Complete registration with your phone number in Telegram bot before joining.")
        room = Room.objects.select_for_update().get(id=room_id, is_active=True)
        running_game = Game.objects.filter(room=room, status="running").order_by("-id").first()
        if running_game:
            removed = GamePlayer.objects.filter(game=running_game, user=user, removed_for_fake_bingo=True).exists()
            if removed:
                raise GameServiceError("You were removed from this round. Wait until current game ends.")
            raise GameServiceError("Game is running. Wait until it ends to join the next round.")

        game = Game.objects.filter(room=room, status="waiting").order_by("-id").first()
        if not game:
            game = Game.objects.create(room=room, status="waiting")

        if user.balance < Decimal(room.bet_amount):
            raise WalletError("Insufficient balance")

        user.balance = F("balance") - Decimal(room.bet_amount)
        user.save(update_fields=["balance"])
        Transaction.objects.create(
            user=user,
            amount=Decimal(room.bet_amount),
            type="bet",
            status="completed",
            reference=f"bet-{game.id}-{user.id}-{timezone.now().timestamp()}",
        )

        cartela = Cartela.objects.get(id=cartela_id, room=room)
        try:
            gp = GamePlayer.objects.create(user=user, game=game, cartela=cartela)
        except IntegrityError as exc:
            raise GameServiceError("User or cartela already used in this game") from exc

        Game.objects.filter(id=game.id).update(total_players=F("total_players") + 1)
        game = Game.objects.select_for_update().get(id=game.id)

        if can_start(game) and not game.countdown_started_at:
            game.countdown_started_at = timezone.now()
            game.save(update_fields=["countdown_started_at"])
            # Lazy import to avoid circular import with Celery task module.
            from .tasks import start_game_after_countdown

            start_game_after_countdown.apply_async(args=[game.id], countdown=COUNTDOWN_SECONDS)
            _broadcast(
                room.id,
                {
                    "event": "countdown_started",
                    "seconds": COUNTDOWN_SECONDS,
                    "starts_at": (game.countdown_started_at + timedelta(seconds=COUNTDOWN_SECONDS)).isoformat(),
                },
            )

        GameAuditLog.objects.create(
            room=room,
            game=game,
            user=user,
            action="join_game",
            payload={"cartela_id": cartela.id, "bet": room.bet_amount},
        )
        return gp


def can_start(game: Game) -> bool:
    return game.status == "waiting" and game.total_players >= 2


def start_game(game: Game) -> Game:
    game.status = "running"
    game.countdown_started_at = None
    game.start_time = timezone.now()
    game.called_numbers = []
    game.save(update_fields=["status", "countdown_started_at", "start_time", "called_numbers"])
    return game


def call_next_number(game: Game) -> int:
    if game.status != "running":
        raise GameServiceError("Game not running")
    called = set(game.called_numbers)
    remaining = [i for i in range(1, 76) if i not in called]
    if not remaining:
        raise GameServiceError("No numbers left")
    n = random.choice(remaining)
    game.called_numbers = [*game.called_numbers, n]
    game.save(update_fields=["called_numbers"])
    return n


def _is_marked(value: int | str, called_numbers: set[int]) -> bool:
    return value == "FREE" or (isinstance(value, int) and value in called_numbers)


def validate_cartela_win(cartela_numbers: list[list[int | str]], called_numbers: set[int]) -> bool:
    # rows
    for row in cartela_numbers:
        if all(_is_marked(num, called_numbers) for num in row):
            return True
    # columns
    for c in range(5):
        if all(_is_marked(cartela_numbers[r][c], called_numbers) for r in range(5)):
            return True
    # diagonals
    if all(_is_marked(cartela_numbers[i][i], called_numbers) for i in range(5)):
        return True
    if all(_is_marked(cartela_numbers[i][4 - i], called_numbers) for i in range(5)):
        return True
    # four corners: first/last on B and first/last on O
    corner_cells = (
        cartela_numbers[0][0],  # top-left (B)
        cartela_numbers[4][0],  # bottom-left (B)
        cartela_numbers[0][4],  # top-right (O)
        cartela_numbers[4][4],  # bottom-right (O)
    )
    if all(_is_marked(num, called_numbers) for num in corner_cells):
        return True
    return False

def get_cartela_display_number(room_id: int, cartela_id: int) -> int:
    return Cartela.objects.filter(room_id=room_id, id__lte=cartela_id).count()


def claim_bingo(user_id: int, game_id: int) -> dict:
    with transaction.atomic():
        try:
            game = Game.objects.select_for_update().get(id=game_id)
        except Game.DoesNotExist as exc:
            raise GameServiceError("Game not found") from exc
        if game.status != "running":
            raise GameServiceError("Game is not running")
        try:
            gp = GamePlayer.objects.select_for_update().get(game=game, user_id=user_id)
        except GamePlayer.DoesNotExist as exc:
            raise GameServiceError("You are not in this running game") from exc
        if gp.bingo_claimed_at:
            raise GameServiceError("Bingo already claimed by this player")

        if gp.removed_for_fake_bingo:
            raise GameServiceError("Player already removed")

        called_set = set(game.called_numbers)
        gp.bingo_claimed_at = timezone.now()
        gp.save(update_fields=["bingo_claimed_at"])
        if not validate_cartela_win(gp.cartela.numbers, called_set):
            gp.removed_for_fake_bingo = True
            gp.save(update_fields=["removed_for_fake_bingo"])
            Game.objects.filter(id=game.id, total_players__gt=0).update(total_players=F("total_players") - 1)
            game.refresh_from_db(fields=["total_players", "status", "room_id"])
            GameAuditLog.objects.create(
                room=game.room,
                game=game,
                user_id=user_id,
                action="fake_bingo",
                payload={},
            )
            _broadcast(
                game.room_id,
                {
                    "event": "player_removed",
                    "user_id": user_id,
                    "reason": "Fake bingo",
                },
            )

            remaining_players = GamePlayer.objects.select_related("user").filter(
                game=game,
                removed_for_fake_bingo=False,
            )
            if game.status == "running" and remaining_players.count() == 1:
                winner_gp = remaining_players.first()
                winner = User.objects.select_for_update().get(id=winner_gp.user_id)
                winner_cartela_number = get_cartela_display_number(game.room_id, winner_gp.cartela_id)
                prize, deduction = calculate_prize(game.total_players, Decimal(game.room.bet_amount))
                winner.balance = F("balance") + prize
                winner.save(update_fields=["balance"])
                Transaction.objects.create(
                    user=winner,
                    amount=prize,
                    type="win",
                    status="completed",
                    reference=f"win-auto-{game.id}-{winner.id}-{timezone.now().timestamp()}",
                )

                game.status = "finished"
                game.winner = winner
                game.prize_amount = prize
                game.deduction_amount = deduction
                game.end_time = timezone.now()
                game.save(update_fields=["status", "winner", "prize_amount", "deduction_amount", "end_time"])

                GameAuditLog.objects.create(
                    room=game.room,
                    game=game,
                    user=winner,
                    action="auto_win_last_player",
                    payload={"prize": str(prize), "deduction": str(deduction)},
                )

                _broadcast(
                    game.room_id,
                    {
                        "event": "game_finished",
                        "winner": winner.username,
                        "winner_id": winner.id,
                        "winner_cartela_number": winner_cartela_number,
                        "prize": str(prize),
                        "called_numbers": game.called_numbers,
                        "reason": "Last remaining player",
                    },
                )

                from .tasks import open_next_waiting_game

                open_next_waiting_game.apply_async(args=[game.room_id], countdown=30)
                return {
                    "valid": False,
                    "reason": "Fake bingo. Player removed.",
                    "auto_winner": winner.username,
                    "prize": str(prize),
                }

            return {"valid": False, "reason": "Fake bingo. Player removed."}

        prize, deduction = calculate_prize(game.total_players, Decimal(game.room.bet_amount))
        winner_cartela_number = get_cartela_display_number(game.room_id, gp.cartela_id)
        winner = User.objects.select_for_update().get(id=user_id)
        winner.balance = F("balance") + prize
        winner.save(update_fields=["balance"])
        Transaction.objects.create(
            user=winner,
            amount=prize,
            type="win",
            status="completed",
            reference=f"win-{game.id}-{winner.id}-{timezone.now().timestamp()}",
        )

        game.status = "finished"
        game.winner = winner
        game.prize_amount = prize
        game.deduction_amount = deduction
        game.end_time = timezone.now()
        game.save(update_fields=["status", "winner", "prize_amount", "deduction_amount", "end_time"])

        GameAuditLog.objects.create(
            room=game.room,
            game=game,
            user=winner,
            action="bingo_win",
            payload={"prize": str(prize), "deduction": str(deduction)},
        )

        _broadcast(
            game.room_id,
            {
                "event": "game_finished",
                "winner": winner.username,
                "winner_id": winner.id,
                "winner_cartela_number": winner_cartela_number,
                "prize": str(prize),
                "called_numbers": game.called_numbers,
                "reason": "Bingo claimed",
            },
        )
        from .tasks import open_next_waiting_game

        open_next_waiting_game.apply_async(args=[game.room_id], countdown=30)
        return {"valid": True, "prize": str(prize)}
