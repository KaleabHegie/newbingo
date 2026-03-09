import uuid
from datetime import timedelta
from decimal import Decimal
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone

from .models import DepositRequest, Transaction, WalletAuditLog, WithdrawRequest

User = get_user_model()
log = logging.getLogger(__name__)


class WalletError(Exception):
    pass


def create_transaction(user: User, amount: Decimal, txn_type: str, status: str = "completed") -> Transaction:
    return Transaction.objects.create(
        user=user,
        amount=amount,
        type=txn_type,
        status=status,
        reference=str(uuid.uuid4()),
    )


def create_transaction_with_reference(
    user: User,
    amount: Decimal,
    txn_type: str,
    reference: str,
    status: str = "completed",
) -> Transaction:
    return Transaction.objects.create(
        user=user,
        amount=amount,
        type=txn_type,
        status=status,
        reference=reference,
    )


def apply_balance_delta(user_id: int, delta: Decimal) -> User:
    with transaction.atomic():
        user = User.objects.select_for_update().get(id=user_id, is_active=True, is_banned=False)
        new_balance = user.balance + delta
        if new_balance < Decimal("0"):
            raise WalletError("በቂ ቀሪ ሂሳብ የለም።")
        user.balance = F("balance") + delta
        user.save(update_fields=["balance"])
        user.refresh_from_db(fields=["balance"])
        return user


def _audit(action: str, payload: dict, user: User | None = None, request_ip: str | None = None) -> None:
    WalletAuditLog.objects.create(
        user=user,
        action=action,
        payload=payload,
        request_ip=request_ip,
    )


def _send_telegram_notification(message: str) -> None:
    token = str(getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    chat_id = str(getattr(settings, "TELEGRAM_NOTIFY_CHAT_ID", "") or "").strip()
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urlencode({"chat_id": chat_id, "text": message, "disable_web_page_preview": "true"}).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urlopen(req, timeout=8) as resp:
            if getattr(resp, "status", 200) >= 400:
                log.warning("telegram notify failed with status %s", getattr(resp, "status", "unknown"))
    except Exception as exc:
        log.warning("telegram notify failed: %s", exc)


def debit_for_bet(user_id: int, amount: Decimal) -> User:
    with transaction.atomic():
        user = apply_balance_delta(user_id=user_id, delta=-amount)
        create_transaction(user=user, amount=amount, txn_type="bet")
        return user


def credit_winnings(user_id: int, amount: Decimal) -> User:
    with transaction.atomic():
        user = apply_balance_delta(user_id=user_id, delta=amount)
        create_transaction(user=user, amount=amount, txn_type="win")
        return user


def _is_reference_used(reference: str) -> bool:
    return (
        DepositRequest.objects.filter(telebirr_reference=reference).exists()
        or Transaction.objects.filter(reference=reference).exists()
    )


def submit_deposit_request(
    *,
    user: User,
    amount: Decimal,
    telebirr_reference: str,
    sender_phone: str,
    request_ip: str | None,
) -> DepositRequest:
    with transaction.atomic():
        reference = telebirr_reference.strip()
        if _is_reference_used(reference):
            raise WalletError("ይህ የክፍያ ማስረጃ (Reference) አስቀድሞ ተጠቅመዋል።")
        req = DepositRequest.objects.create(
            user=user,
            amount=amount,
            telebirr_reference=reference,
            sender_phone=sender_phone.strip(),
            telegram_id_snapshot=user.telegram_id,
            request_ip=request_ip,
            status="pending",
        )
        _audit(
            "deposit_request_submitted",
            {"deposit_request_id": req.id, "amount": str(amount), "reference": reference},
            user=user,
            request_ip=request_ip,
        )
        _send_telegram_notification(
            f"የገንዘብ ግቢ ጥያቄ ተልኳል\n"
            f"ተጠቃሚ: {user.username}\n"
            f"Telegram ID: {user.telegram_id}\n"
            f"መጠን: {amount} ብር\n"
            f"Request ID: {req.id}\n"
            f"ሁኔታ: በመጠባበቅ ላይ"
        )
        return req


def approve_deposit_request(*, request_id: int, admin_user: User, note: str = "") -> DepositRequest:
    with transaction.atomic():
        req = DepositRequest.objects.select_for_update().select_related("user").get(id=request_id)
        if req.status != "pending":
            raise WalletError("የገንዘብ ግቢ ጥያቄው አስቀድሞ ተከናውኗል።")
        req.status = "approved"
        req.processed_by = admin_user
        req.processed_at = timezone.now()
        req.admin_note = note
        req.save(update_fields=["status", "processed_by", "processed_at", "admin_note", "updated_at"])
        apply_balance_delta(user_id=req.user_id, delta=req.amount)
        create_transaction_with_reference(
            user=req.user,
            amount=req.amount,
            txn_type="deposit",
            reference=f"dep-{req.id}",
            status="completed",
        )
        _audit(
            "deposit_request_approved",
            {"deposit_request_id": req.id, "amount": str(req.amount)},
            user=req.user,
            request_ip=req.request_ip,
        )
        _send_telegram_notification(
            f"የገንዘብ ግቢ ጥያቄ ጸድቋል\n"
            f"ተጠቃሚ: {req.user.username}\n"
            f"Telegram ID: {req.user.telegram_id}\n"
            f"መጠን: {req.amount} ብር\n"
            f"Request ID: {req.id}"
        )
        return req


def reject_deposit_request(*, request_id: int, admin_user: User, note: str = "") -> DepositRequest:
    with transaction.atomic():
        req = DepositRequest.objects.select_for_update().get(id=request_id)
        if req.status != "pending":
            raise WalletError("የገንዘብ ግቢ ጥያቄው አስቀድሞ ተከናውኗል።")
        req.status = "rejected"
        req.processed_by = admin_user
        req.processed_at = timezone.now()
        req.admin_note = note
        req.save(update_fields=["status", "processed_by", "processed_at", "admin_note", "updated_at"])
        _audit(
            "deposit_request_rejected",
            {"deposit_request_id": req.id, "amount": str(req.amount)},
            user=req.user,
            request_ip=req.request_ip,
        )
        _send_telegram_notification(
            f"የገንዘብ ግቢ ጥያቄ ተከልክሏል\n"
            f"ተጠቃሚ: {req.user.username}\n"
            f"Telegram ID: {req.user.telegram_id}\n"
            f"መጠን: {req.amount} ብር\n"
            f"Request ID: {req.id}"
        )
        return req


def validate_withdraw_request(*, user: User, amount: Decimal) -> None:
    min_withdraw = Decimal(str(getattr(settings, "MIN_WITHDRAW_BIRR", "100")))
    if amount < min_withdraw:
        raise WalletError(f"አነስተኛ ማውጫ መጠን {min_withdraw} ብር ነው።")
    if user.balance < amount:
        raise WalletError("በቂ ቀሪ ሂሳብ የለም።")

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    requests_today = WithdrawRequest.objects.filter(user=user, created_at__gte=today_start).count()
    max_count = int(getattr(settings, "DAILY_WITHDRAW_REQUEST_COUNT", 3))
    if requests_today >= max_count:
        raise WalletError("የቀን የማውጫ ጥያቄ ገደብ ተደርሷል።")

    daily_limit = Decimal(str(getattr(settings, "DAILY_WITHDRAW_LIMIT_BIRR", "5000")))
    total_today = (
        WithdrawRequest.objects.filter(user=user, created_at__gte=today_start, status__in=["pending", "paid"])
        .aggregate(total=models.Sum("amount"))
        .get("total")
        or Decimal("0")
    )
    if total_today + amount > daily_limit:
        raise WalletError(f"የቀን የማውጫ ገደብ {daily_limit} ብር ነው።")


def _detect_suspicious_withdraw(user: User) -> tuple[bool, str]:
    lookback_minutes = int(getattr(settings, "SUSPICIOUS_WIN_WITHDRAW_MINUTES", 15))
    lookback = timezone.now() - timedelta(minutes=lookback_minutes)
    recent_win = Transaction.objects.filter(user=user, type="win", created_at__gte=lookback).exists()
    if recent_win:
        return True, "ፈጣን ድል ተከትሎ የማውጫ እንቅስቃሴ ተገኝቷል"
    return False, ""


def submit_withdraw_request(
    *,
    user: User,
    amount: Decimal,
    telebirr_phone: str,
    account_holder_name: str,
    request_ip: str | None,
) -> WithdrawRequest:
    with transaction.atomic():
        validate_withdraw_request(user=user, amount=amount)
        suspicious, reason = _detect_suspicious_withdraw(user)
        req = WithdrawRequest.objects.create(
            user=user,
            amount=amount,
            telebirr_phone=telebirr_phone.strip(),
            account_holder_name=account_holder_name.strip(),
            telegram_id_snapshot=user.telegram_id,
            request_ip=request_ip,
            status="pending",
            is_suspicious=suspicious,
            suspicious_reason=reason,
        )
        _audit(
            "withdraw_request_submitted",
            {"withdraw_request_id": req.id, "amount": str(amount), "suspicious": suspicious, "reason": reason},
            user=user,
            request_ip=request_ip,
        )
        _send_telegram_notification(
            f"የገንዘብ ማውጫ ጥያቄ ተልኳል\n"
            f"ተጠቃሚ: {user.username}\n"
            f"Telegram ID: {user.telegram_id}\n"
            f"መጠን: {amount} ብር\n"
            f"Request ID: {req.id}\n"
            f"ሁኔታ: በመጠባበቅ ላይ"
        )
        return req


def mark_withdraw_paid(*, request_id: int, admin_user: User, note: str = "") -> WithdrawRequest:
    with transaction.atomic():
        req = WithdrawRequest.objects.select_for_update().select_related("user").get(id=request_id)
        if req.status != "pending":
            raise WalletError("የገንዘብ ማውጫ ጥያቄው አስቀድሞ ተከናውኗል።")
        apply_balance_delta(user_id=req.user_id, delta=-req.amount)
        create_transaction_with_reference(
            user=req.user,
            amount=req.amount,
            txn_type="withdraw",
            reference=f"wd-{req.id}-{uuid.uuid4().hex[:10]}",
            status="completed",
        )
        req.status = "paid"
        req.processed_by = admin_user
        req.processed_at = timezone.now()
        req.admin_note = note
        req.save(update_fields=["status", "processed_by", "processed_at", "admin_note", "updated_at"])
        _audit(
            "withdraw_request_paid",
            {"withdraw_request_id": req.id, "amount": str(req.amount)},
            user=req.user,
            request_ip=req.request_ip,
        )
        _send_telegram_notification(
            f"የገንዘብ ማውጫ ተከፍሏል\n"
            f"ተጠቃሚ: {req.user.username}\n"
            f"Telegram ID: {req.user.telegram_id}\n"
            f"መጠን: {req.amount} ብር\n"
            f"Request ID: {req.id}"
        )
        return req


def reject_withdraw_request(*, request_id: int, admin_user: User, note: str = "") -> WithdrawRequest:
    with transaction.atomic():
        req = WithdrawRequest.objects.select_for_update().get(id=request_id)
        if req.status != "pending":
            raise WalletError("የገንዘብ ማውጫ ጥያቄው አስቀድሞ ተከናውኗል።")
        req.status = "rejected"
        req.processed_by = admin_user
        req.processed_at = timezone.now()
        req.admin_note = note
        req.save(update_fields=["status", "processed_by", "processed_at", "admin_note", "updated_at"])
        _audit(
            "withdraw_request_rejected",
            {"withdraw_request_id": req.id, "amount": str(req.amount)},
            user=req.user,
            request_ip=req.request_ip,
        )
        _send_telegram_notification(
            f"የገንዘብ ማውጫ ጥያቄ ተከልክሏል\n"
            f"ተጠቃሚ: {req.user.username}\n"
            f"Telegram ID: {req.user.telegram_id}\n"
            f"መጠን: {req.amount} ብር\n"
            f"Request ID: {req.id}"
        )
        return req