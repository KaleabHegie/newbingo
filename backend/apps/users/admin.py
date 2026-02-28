from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_id", "phone_number", "username", "balance", "is_active", "is_banned")
    search_fields = ("telegram_id", "phone_number", "username")
    list_filter = ("is_active", "is_banned")
