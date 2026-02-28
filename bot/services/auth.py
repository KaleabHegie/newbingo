from aiogram.types import User as TgUser

from services.api_client import BackendClient
from services.auth_store import TOKENS

client = BackendClient()


async def ensure_access_token(tg_user: TgUser) -> str:
    cached = TOKENS.get(tg_user.id)
    if cached:
        return cached

    payload = {
        "telegram_id": tg_user.id,
        "username": tg_user.username or f"tg_{tg_user.id}",
        "first_name": tg_user.first_name or "",
        "last_name": tg_user.last_name or "",
    }
    tokens = await client.bot_login(payload)
    TOKENS[tg_user.id] = tokens["access"]
    return TOKENS[tg_user.id]
