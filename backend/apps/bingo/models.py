from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Room(models.Model):
    bet_amount = models.PositiveIntegerField(unique=True)
    total_cartelas = models.PositiveIntegerField(default=200)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Room-{self.bet_amount}"


class Cartela(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="cartelas")
    numbers = models.JSONField()
    predefined = models.BooleanField(default=True)

    def clean(self):
        if not isinstance(self.numbers, list) or len(self.numbers) != 5:
            raise ValidationError("numbers must be 5x5 matrix")
        for row in self.numbers:
            if not isinstance(row, list) or len(row) != 5:
                raise ValidationError("each row must have 5 numbers")

        ranges = [
            range(1, 16),   # B
            range(16, 31),  # I
            range(31, 46),  # N
            range(46, 61),  # G
            range(61, 76),  # O
        ]
        seen: set[int] = set()
        for r in range(5):
            for c in range(5):
                value = self.numbers[r][c]
                if r == 2 and c == 2:
                    if value != "FREE":
                        raise ValidationError("center cell must be FREE")
                    continue
                if not isinstance(value, int):
                    raise ValidationError("all non-center values must be integers")
                if value not in ranges[c]:
                    raise ValidationError("cartela values must match B/I/N/G/O ranges")
                if value in seen:
                    raise ValidationError("duplicate numbers are not allowed in a cartela")
                seen.add(value)


class Game(models.Model):
    STATUS_CHOICES = [("waiting", "waiting"), ("running", "running"), ("finished", "finished")]

    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="games")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="waiting", db_index=True)
    total_players = models.PositiveIntegerField(default=0)
    prize_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    deduction_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    countdown_started_at = models.DateTimeField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    called_numbers = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["room", "status"])]


class GamePlayer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="game_players")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    cartela = models.ForeignKey(Cartela, on_delete=models.PROTECT)
    joined_at = models.DateTimeField(auto_now_add=True)
    bingo_claimed_at = models.DateTimeField(null=True, blank=True)
    removed_for_fake_bingo = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["game", "user"], name="uniq_user_per_game"),
            models.UniqueConstraint(fields=["game", "cartela"], name="uniq_cartela_per_game"),
        ]


class GameAuditLog(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
