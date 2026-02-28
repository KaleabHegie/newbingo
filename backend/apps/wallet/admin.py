from django.contrib import admin

from .models import DepositRequest, Transaction, WalletAuditLog, WithdrawRequest
from .services import (
    WalletError,
    approve_deposit_request,
    mark_withdraw_paid,
    reject_deposit_request,
    reject_withdraw_request,
)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "type", "status", "created_at")
    list_filter = ("type", "status")
    search_fields = ("reference", "user__username", "user__telegram_id")


@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "telebirr_reference", "status", "created_at", "processed_at")
    list_filter = ("status", "created_at")
    search_fields = ("telebirr_reference", "sender_phone", "user__telegram_id", "user__username")
    actions = ("approve_selected", "reject_selected")

    @admin.action(description="Approve selected deposits")
    def approve_selected(self, request, queryset):
        ok = 0
        for req in queryset:
            try:
                approve_deposit_request(request_id=req.id, admin_user=request.user, note="Approved from admin action")
                ok += 1
            except WalletError:
                continue
        self.message_user(request, f"Approved {ok} deposit request(s).")

    @admin.action(description="Reject selected deposits")
    def reject_selected(self, request, queryset):
        ok = 0
        for req in queryset:
            try:
                reject_deposit_request(request_id=req.id, admin_user=request.user, note="Rejected from admin action")
                ok += 1
            except WalletError:
                continue
        self.message_user(request, f"Rejected {ok} deposit request(s).")


@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "telebirr_phone", "status", "is_suspicious", "created_at", "processed_at")
    list_filter = ("status", "is_suspicious", "created_at")
    search_fields = ("telebirr_phone", "account_holder_name", "user__telegram_id", "user__username")
    actions = ("mark_paid_selected", "reject_selected")

    @admin.action(description="Mark selected withdraws as paid")
    def mark_paid_selected(self, request, queryset):
        ok = 0
        for req in queryset:
            try:
                mark_withdraw_paid(request_id=req.id, admin_user=request.user, note="Marked paid from admin action")
                ok += 1
            except WalletError:
                continue
        self.message_user(request, f"Marked {ok} withdraw request(s) as paid.")

    @admin.action(description="Reject selected withdraws")
    def reject_selected(self, request, queryset):
        ok = 0
        for req in queryset:
            try:
                reject_withdraw_request(request_id=req.id, admin_user=request.user, note="Rejected from admin action")
                ok += 1
            except WalletError:
                continue
        self.message_user(request, f"Rejected {ok} withdraw request(s).")


@admin.register(WalletAuditLog)
class WalletAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "user", "request_ip", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("action", "user__telegram_id", "user__username")
