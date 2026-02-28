from django.urls import path

from .views import BotLoginView, MeView, RegisterPhoneView, TelegramLoginView

urlpatterns = [
    path("telegram-login", TelegramLoginView.as_view(), name="telegram-login"),
    path("bot-login", BotLoginView.as_view(), name="bot-login"),
    path("me", MeView.as_view(), name="me"),
    path("register-phone", RegisterPhoneView.as_view(), name="register-phone"),
]
