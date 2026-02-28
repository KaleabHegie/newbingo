import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from apps.wallet.models import Transaction

from .serializers import BotLoginSerializer, RegisterPhoneSerializer, TelegramLoginSerializer
from .telegram import TelegramAuthError, extract_user_from_init_data, verify_init_data

User = get_user_model()


def _apply_welcome_bonus(user: User) -> None:
    bonus = Decimal(str(settings.WELCOME_BONUS_BIRR or "0"))
    if bonus <= 0:
        return
    if user.balance > 0:
        return
    if Transaction.objects.filter(user=user, reference__startswith="welcome-").exists():
        return

    user.balance = bonus
    user.save(update_fields=["balance"])
    Transaction.objects.create(
        user=user,
        amount=bonus,
        type="deposit",
        status="completed",
        reference=f"welcome-{user.id}-{uuid.uuid4().hex}",
    )


class TelegramLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TelegramLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        init_data = serializer.validated_data["init_data"]
        try:
            tg_user = verify_init_data(init_data)
        except TelegramAuthError as exc:
            if settings.DEBUG:
                fallback_user = extract_user_from_init_data(init_data)
                if fallback_user:
                    tg_user = fallback_user
                else:
                    return Response(
                        {"detail": f"{exc}. Debug fallback could not extract Telegram user."},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            else:
                return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        telegram_id = tg_user["id"]
        username = tg_user.get("username") or f"tg_{telegram_id}"
        user, _ = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": username[:150],
                "first_name": tg_user.get("first_name", ""),
                "last_name": tg_user.get("last_name", ""),
            },
        )
        _apply_welcome_bonus(user)

        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})


class BotLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        api_key = request.headers.get("X-BOT-API-KEY", "")
        if not settings.BOT_API_KEY or api_key != settings.BOT_API_KEY:
            return Response({"detail": "Unauthorized bot request"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = BotLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        telegram_id = payload["telegram_id"]
        username = payload.get("username") or f"tg_{telegram_id}"
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": username[:150],
                "first_name": payload.get("first_name", ""),
                "last_name": payload.get("last_name", ""),
            },
        )

        if not created:
            updates = []
            if payload.get("first_name") is not None and user.first_name != payload.get("first_name", ""):
                user.first_name = payload.get("first_name", "")
                updates.append("first_name")
            if payload.get("last_name") is not None and user.last_name != payload.get("last_name", ""):
                user.last_name = payload.get("last_name", "")
                updates.append("last_name")
            if payload.get("username") and user.username != payload.get("username"):
                user.username = payload["username"][:150]
                updates.append("username")
            if updates:
                user.save(update_fields=updates)

        _apply_welcome_bonus(user)
        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "id": request.user.id,
                "telegram_id": request.user.telegram_id,
                "username": request.user.username,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "phone_number": request.user.phone_number,
                "phone_registered": bool(request.user.phone_number),
            }
        )


class RegisterPhoneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RegisterPhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.phone_number = serializer.validated_data["phone_number"]
        try:
            request.user.save(update_fields=["phone_number"])
        except IntegrityError:
            return Response({"detail": "This phone number is already registered."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"phone_number": request.user.phone_number, "phone_registered": True})
