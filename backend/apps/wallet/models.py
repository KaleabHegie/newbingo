from django.conf import settings
from django.db import models


class Transaction(models.Model):
    TYPE_CHOICES = [
        ("deposit", "deposit"),
        ("withdraw", "withdraw"),
        ("bet", "bet"),
        ("win", "win"),
    ]
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("completed", "completed"),
        ("failed", "failed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, db_index=True)
    reference = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user_id}:{self.type}:{self.amount}"


class DepositRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deposit_requests")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    telebirr_reference = models.CharField(max_length=64, unique=True, db_index=True)
    sender_phone = models.CharField(max_length=32)
    telegram_id_snapshot = models.BigIntegerField(db_index=True)
    request_ip = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", db_index=True)
    admin_note = models.TextField(blank=True, default="")
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="processed_deposit_requests",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class WithdrawRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("paid", "paid"),
        ("rejected", "rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="withdraw_requests")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    telebirr_phone = models.CharField(max_length=32)
    account_holder_name = models.CharField(max_length=128)
    telegram_id_snapshot = models.BigIntegerField(db_index=True)
    request_ip = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", db_index=True)
    admin_note = models.TextField(blank=True, default="")
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="processed_withdraw_requests",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    is_suspicious = models.BooleanField(default=False, db_index=True)
    suspicious_reason = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class WalletAuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict)
    request_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
