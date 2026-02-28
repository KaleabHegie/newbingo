from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    telegram_id = models.BigIntegerField(unique=True, db_index=True, null=True, blank=True)
    phone_number = models.CharField(max_length=32, unique=True, null=True, blank=True, db_index=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    is_banned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return f"{self.username or self.telegram_id}"
