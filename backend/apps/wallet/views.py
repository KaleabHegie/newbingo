from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DepositRequest, Transaction, WithdrawRequest
from .serializers import (
    DepositRequestCreateSerializer,
    DepositRequestSerializer,
    TransactionSerializer,
    WithdrawRequestCreateSerializer,
    WithdrawRequestSerializer,
)
from .services import (
    WalletError,
    submit_deposit_request,
    submit_withdraw_request,
)


class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"balance": str(request.user.balance)})


class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        txns = Transaction.objects.filter(user=request.user).order_by("-created_at")[:50]
        return Response(TransactionSerializer(txns, many=True).data)


class DepositInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "telebirr_number": getattr(settings, "TELEBIRR_NUMBER", "0969146494"),
                "account_name": getattr(settings, "TELEBIRR_ACCOUNT_NAME", "ፀዴ Bingo"),
                "instructions": "ገንዘቡን ወደ ቴሌብር ላኩ፣ ከዚያም የላኩትን መጠን፣ የክፍያ ማስረጃ (Reference) እና የላኪውን ስልክ ቁጥር ያስገቡ።",
            }
        )


class DepositSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            req = submit_deposit_request(
                user=request.user,
                amount=serializer.validated_data["amount"],
                telebirr_reference=serializer.validated_data["telebirr_reference"],
                sender_phone=serializer.validated_data["sender_phone"],
                request_ip=request.META.get("REMOTE_ADDR"),
            )
        except WalletError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(DepositRequestSerializer(req).data, status=201)


class DepositStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = DepositRequest.objects.filter(user=request.user).order_by("-created_at")[:20]
        return Response(DepositRequestSerializer(requests, many=True).data)


class WithdrawSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WithdrawRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            req = submit_withdraw_request(
                user=request.user,
                amount=serializer.validated_data["amount"],
                telebirr_phone=serializer.validated_data["telebirr_phone"],
                account_holder_name=serializer.validated_data["account_holder_name"],
                request_ip=request.META.get("REMOTE_ADDR"),
            )
        except WalletError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(WithdrawRequestSerializer(req).data, status=201)


class WithdrawStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = WithdrawRequest.objects.filter(user=request.user).order_by("-created_at")[:20]
        return Response(WithdrawRequestSerializer(requests, many=True).data)
