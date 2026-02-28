import os

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters import CommandStart
from aiogram.types import Message
import httpx

from keyboards.main import (
    MINI_APP_BTN,
    REGISTER_PHONE_BTN,
    main_menu_keyboard,
    miniapp_keyboard,
    phone_request_keyboard,
    register_only_keyboard,
)
from services.api_client import BackendClient
from services.auth import ensure_access_token

router = Router()
MINI_APP_URL = os.getenv("MINI_APP_URL", "")
client = BackendClient()


@router.message(CommandStart())
async def start_cmd(message: Message):
    try:
        token = await ensure_access_token(message.from_user)
        profile = await client.me(token)
        is_registered = bool(profile.get("phone_registered"))
    except Exception:
        is_registered = False

    if not is_registered:
        await message.answer(
            "Welcome to Bingo Ethiopia.\nPlease register your phone number first.",
            reply_markup=register_only_keyboard(),
        )
        return

    await message.answer(
        "Welcome to Bingo Ethiopia.\nUse the buttons below to manage wallet and join rooms.",
        reply_markup=main_menu_keyboard(MINI_APP_URL if MINI_APP_URL else None),
    )
    if MINI_APP_URL:
        await message.answer("Tap to open the game interface:", reply_markup=miniapp_keyboard(MINI_APP_URL))


@router.message(F.text.casefold() == MINI_APP_BTN.casefold())
async def open_miniapp_btn(message: Message):
    if not MINI_APP_URL:
        await message.answer("Mini app URL is not configured yet.")
        return
    await message.answer("Tap to open the game interface:", reply_markup=miniapp_keyboard(MINI_APP_URL))


async def _ask_phone(message: Message):
    await message.answer(
        "Please share your phone number to complete registration.",
        reply_markup=phone_request_keyboard(),
    )


@router.message(Command("register_phone"))
async def register_phone_cmd(message: Message):
    await _ask_phone(message)


@router.message(F.text.casefold() == REGISTER_PHONE_BTN.casefold())
async def register_phone_btn(message: Message):
    await _ask_phone(message)


@router.message(F.contact)
async def save_shared_contact(message: Message):
    if not message.contact:
        await message.answer("No contact found. Please try again.")
        return
    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        await message.answer("Please share your own Telegram contact.")
        return
    try:
        token = await ensure_access_token(message.from_user)
        data = await client.register_phone(token, message.contact.phone_number)
        await message.answer(
            f"Phone registered: {data.get('phone_number')}\nYou can now join games.",
            reply_markup=main_menu_keyboard(MINI_APP_URL if MINI_APP_URL else None),
        )
    except httpx.HTTPStatusError as exc:
        detail = "Unable to register phone."
        try:
            payload = exc.response.json()
            if isinstance(payload, dict) and payload.get("detail"):
                detail = str(payload["detail"])
        except Exception:
            pass
        await message.answer(detail)
    except Exception:
        await message.answer("Unable to register phone right now. Please try again.")
