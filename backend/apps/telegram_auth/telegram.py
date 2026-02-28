import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from django.conf import settings


class TelegramAuthError(Exception):
    pass


def _build_data_check_string(data: dict) -> str:
    pairs = []
    for k, v in data.items():
        if k == "hash":
            continue
        pairs.append(f"{k}={v}")
    return "\n".join(sorted(pairs))


def verify_init_data(init_data: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    data_hash = parsed.get("hash")
    if not data_hash:
        raise TelegramAuthError("Missing hash")

    data_check_string = _build_data_check_string(parsed)
    secret_key = hmac.new(b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated, data_hash):
        raise TelegramAuthError("Invalid initData signature")

    auth_date = int(parsed.get("auth_date", "0"))
    now = int(time.time())
    if now - auth_date > settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS:
        raise TelegramAuthError("initData expired")

    user_json = parsed.get("user")
    if not user_json:
        raise TelegramAuthError("Missing user payload")
    return json.loads(user_json)


def extract_user_from_init_data(init_data: str) -> dict | None:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    user_json = parsed.get("user")
    if not user_json:
        return None
    try:
        return json.loads(user_json)
    except json.JSONDecodeError:
        return None
