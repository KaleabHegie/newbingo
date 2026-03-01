import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "channels",
    "apps.users",
    "apps.wallet",
    "apps.bingo",
    "apps.telegram_auth",
    "apps.realtime",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "bingo"),
        "USER": os.getenv("POSTGRES_USER", "bingo"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "bingo"),
        "HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULE = {
    "room-loop-all": {
        "task": "apps.bingo.tasks.room_game_loop_all",
        "schedule": 10.0,
    },
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_INITDATA_MAX_AGE_SECONDS = int(os.getenv("TELEGRAM_INITDATA_MAX_AGE_SECONDS", "3600"))
BOT_API_KEY = os.getenv("BOT_API_KEY", "")
WELCOME_BONUS_BIRR = os.getenv("WELCOME_BONUS_BIRR", "0")

TELEBIRR_NUMBER = os.getenv("TELEBIRR_NUMBER", "0969146494")
TELEBIRR_ACCOUNT_NAME = os.getenv("TELEBIRR_ACCOUNT_NAME", "ፀዴ Bingo")
MIN_WITHDRAW_BIRR = os.getenv("MIN_WITHDRAW_BIRR", "100")
DAILY_WITHDRAW_LIMIT_BIRR = os.getenv("DAILY_WITHDRAW_LIMIT_BIRR", "5000")
DAILY_WITHDRAW_REQUEST_COUNT = int(os.getenv("DAILY_WITHDRAW_REQUEST_COUNT", "3"))
SUSPICIOUS_WIN_WITHDRAW_MINUTES = int(os.getenv("SUSPICIOUS_WIN_WITHDRAW_MINUTES", "15"))
