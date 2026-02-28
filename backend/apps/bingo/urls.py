from django.urls import path

from .views import CartelaListView, ClaimBingoView, JoinGameView, MySeatView, RoomListView, RoomSummaryView

urlpatterns = [
    path("rooms", RoomListView.as_view(), name="room-list"),
    path("cartelas", CartelaListView.as_view(), name="cartela-list"),
    path("my-seat", MySeatView.as_view(), name="my-seat"),
    path("summary", RoomSummaryView.as_view(), name="room-summary"),
    path("join", JoinGameView.as_view(), name="room-join"),
    path("claim", ClaimBingoView.as_view(), name="bingo-claim"),
]
