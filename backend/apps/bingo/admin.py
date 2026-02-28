from django.contrib import admin

from .models import Cartela, Game, GameAuditLog, GamePlayer, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "bet_amount", "total_cartelas", "is_active")


@admin.register(Cartela)
class CartelaAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "predefined")
    list_filter = ("room",)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "status", "total_players", "prize_amount", "winner")
    list_filter = ("room", "status")
    actions = ["force_end"]

    def force_end(self, request, queryset):
        queryset.update(status="finished")


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "user", "cartela", "removed_for_fake_bingo")


@admin.register(GameAuditLog)
class GameAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "game", "user", "action", "created_at")
    list_filter = ("room", "action")
