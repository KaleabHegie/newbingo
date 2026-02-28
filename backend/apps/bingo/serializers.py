from rest_framework import serializers

from .models import Cartela, Game, GamePlayer, Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ("id", "bet_amount", "total_cartelas", "is_active")


class JoinGameSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    cartela_id = serializers.IntegerField()


class ClaimBingoSerializer(serializers.Serializer):
    game_id = serializers.IntegerField()


class CartelaSerializer(serializers.ModelSerializer):
    is_taken = serializers.BooleanField()

    class Meta:
        model = Cartela
        fields = ("id", "room_id", "numbers", "predefined", "is_taken")


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = (
            "id",
            "room_id",
            "status",
            "total_players",
            "prize_amount",
            "deduction_amount",
            "winner_id",
            "start_time",
            "end_time",
            "called_numbers",
        )


class GamePlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GamePlayer
        fields = ("id", "user_id", "game_id", "cartela_id", "joined_at", "removed_for_fake_bingo")
