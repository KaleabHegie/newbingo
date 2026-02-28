from decimal import Decimal

from rest_framework import serializers

from .models import DepositRequest, Transaction, WithdrawRequest


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ("id", "amount", "type", "status", "reference", "created_at")


class DepositRequestCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("1"))
    telebirr_reference = serializers.CharField(max_length=64)
    sender_phone = serializers.CharField(max_length=32)


class WithdrawRequestCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("1"))
    telebirr_phone = serializers.CharField(max_length=32)
    account_holder_name = serializers.CharField(max_length=128)


class DepositRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositRequest
        fields = (
            "id",
            "amount",
            "telebirr_reference",
            "sender_phone",
            "status",
            "admin_note",
            "processed_at",
            "created_at",
        )


class WithdrawRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawRequest
        fields = (
            "id",
            "amount",
            "telebirr_phone",
            "account_holder_name",
            "status",
            "admin_note",
            "is_suspicious",
            "suspicious_reason",
            "processed_at",
            "created_at",
        )
