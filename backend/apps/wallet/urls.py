from django.urls import path

from .views import (
    BalanceView,
    DepositInfoView,
    DepositStatusView,
    DepositSubmitView,
    TransactionHistoryView,
    WithdrawStatusView,
    WithdrawSubmitView,
)

urlpatterns = [
    path("balance", BalanceView.as_view(), name="balance"),
    path("transactions", TransactionHistoryView.as_view(), name="transactions"),
    path("deposit/info", DepositInfoView.as_view(), name="deposit-info"),
    path("deposit/submit", DepositSubmitView.as_view(), name="deposit-submit"),
    path("deposit/status", DepositStatusView.as_view(), name="deposit-status"),
    path("withdraw/submit", WithdrawSubmitView.as_view(), name="withdraw-submit"),
    path("withdraw/status", WithdrawStatusView.as_view(), name="withdraw-status"),
]
