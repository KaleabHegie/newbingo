from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import timedelta
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from apps.wallet.services import WalletError

from .deduction import calculate_prize
from .models import Cartela, GamePlayer, Room
from .serializers import ClaimBingoSerializer, JoinGameSerializer, RoomSerializer
from .services import GameServiceError, claim_bingo, get_or_create_waiting_game, join_game


class RoomListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.filter(is_active=True).order_by("bet_amount", "id")
        return Response(RoomSerializer(rooms, many=True).data)


class JoinGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = JoinGameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            gp = join_game(
                user_id=request.user.id,
                room_id=serializer.validated_data["room_id"],
                cartela_id=serializer.validated_data["cartela_id"],
            )
        except (GameServiceError, WalletError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"game_id": gp.game_id, "cartela_id": gp.cartela_id}, status=status.HTTP_201_CREATED)


class CartelaListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room_id = request.query_params.get("room_id")
        if not room_id:
            return Response({"detail": "room_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            room = Room.objects.get(id=room_id, is_active=True)
        except Room.DoesNotExist:
            return Response({"detail": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            game = get_or_create_waiting_game(room)
        except GameServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        taken_ids = set(GamePlayer.objects.filter(game=game).values_list("cartela_id", flat=True))
        cartelas = Cartela.objects.filter(room=room).order_by("id")

        data = [
            {
                "id": c.id,
                "display_number": idx + 1,
                "room_id": room.id,
                "numbers": c.numbers,
                "predefined": c.predefined,
                "is_taken": c.id in taken_ids,
            }
            for idx, c in enumerate(cartelas)
        ]
        return Response({"game_id": game.id, "cartelas": data})


class MySeatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room_id = request.query_params.get("room_id")
        if not room_id:
            return Response({"detail": "room_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            room = Room.objects.get(id=room_id, is_active=True)
        except Room.DoesNotExist:
            return Response({"detail": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        gp = (
            GamePlayer.objects.filter(
                user=request.user,
                game__room=room,
                game__status__in=["running", "waiting"],
                removed_for_fake_bingo=False,
            )
            .annotate(
                status_priority=Case(
                    When(game__status="running", then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("status_priority", "-game_id")
            .first()
        )

        if not gp:
            return Response({"game_id": None, "cartela_id": None})

        return Response({"game_id": gp.game_id, "cartela_id": gp.cartela_id})


class RoomSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room_id = request.query_params.get("room_id")
        if not room_id:
            return Response({"detail": "room_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            room = Room.objects.get(id=room_id, is_active=True)
        except Room.DoesNotExist:
            return Response({"detail": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        game = (
            room.games.annotate(
                status_priority=Case(
                    When(status="running", then=Value(0)),
                    When(status="waiting", then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )
            .order_by("status_priority", "-id")
            .first()
        )

        if not game:
            return Response(
                {
                    "game_id": None,
                    "status": "waiting",
                    "total_players": 0,
                    "total_win": "0.00",
                    "countdown_left": None,
                    "winner": None,
                }
            )

        prize, _ = calculate_prize(game.total_players, room.bet_amount)
        countdown_left = None
        if game.status == "waiting" and game.countdown_started_at:
            delta = (game.countdown_started_at + timedelta(seconds=15) - timezone.now()).total_seconds()
            countdown_left = max(0, int(delta))
        return Response(
            {
                "game_id": game.id,
                "status": game.status,
                "total_players": game.total_players,
                "total_win": str(prize),
                "countdown_left": countdown_left,
                "winner": game.winner.username if game.winner else None,
            }
        )


class ClaimBingoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClaimBingoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = claim_bingo(user_id=request.user.id, game_id=serializer.validated_data["game_id"])
        except GameServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)
