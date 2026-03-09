import os
import re

import httpx
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.filters.state import StateFilter
from aiogram.types import Message

from keyboards.main import (
    MINI_APP_BTN,
    REGISTER_PHONE_BTN,
    main_menu_keyboard,
    miniapp_keyboard,
    phone_request_keyboard,
    register_only_keyboard,
)
from services.api_client import BackendClient
from services.auth import call_with_reauth

router = Router()
MINI_APP_URL = os.getenv("MINI_APP_URL", "")
client = BackendClient()


@router.message(CommandStart())
async def start_cmd(message: Message):
    try:
        profile = await call_with_reauth(message.from_user, client.me)
        is_registered = bool(profile.get("phone_registered"))
    except Exception:
        is_registered = False

    if not is_registered:
        await message.answer(
            "እንኳን ወደ ቢንጎ ኢትዮጵያ በደህና መጡ።\nመጀመሪያ ስልክ ቁጥርዎን ይመዝግቡ።",
            reply_markup=register_only_keyboard(),
        )
        return

    await message.answer(
        "እንኳን ወደ ፀዴ ቢንጎ በደህና መጡ።",
        reply_markup=main_menu_keyboard(MINI_APP_URL if MINI_APP_URL else None),
    )
    if MINI_APP_URL:
        await message.answer("የጨዋታ ገጹን ለመክፈት ይጫኑ:", reply_markup=miniapp_keyboard(MINI_APP_URL))


@router.message(Command("chatid"))
async def chat_id_cmd(message: Message):
    chat = message.chat
    await message.answer(f"የቻት መለያ: {chat.id}\nየቻት አይነት: {chat.type}\nርዕስ: {chat.title or '-'}")


@router.message(F.text.casefold() == MINI_APP_BTN.casefold())
async def open_miniapp_btn(message: Message):
    if not MINI_APP_URL:
        await message.answer("የሚኒ አፕ ሊንክ ገና አልተዘጋጀም።")
        return
    await message.answer("የጨዋታ ገጹን ለመክፈት ይጫኑ:", reply_markup=miniapp_keyboard(MINI_APP_URL))


async def _ask_phone(message: Message):
    await message.answer(
        "ምዝገባውን ለማጠናቀቅ ስልክ ቁጥርዎን ያጋሩ ወይም በእጅ ይፃፉ።\n"
        "ምሳሌ: 0912345678 ወይም +251912345678",
        reply_markup=phone_request_keyboard(),
    )


@router.message(Command("register_phone"))
async def register_phone_cmd(message: Message):
    await _ask_phone(message)


@router.message(F.text.casefold() == REGISTER_PHONE_BTN.casefold())
async def register_phone_btn(message: Message):
    await _ask_phone(message)


def _normalize_et_phone(raw: str) -> tuple[str | None, str | None]:
    digits = re.sub(r"\D", "", (raw or "").strip())
    if not digits:
        return None, "እባክዎ የትክክለኛ ስልክ ቁጥር ያስገቡ። ምሳሌ: 0912345678"

    if digits.startswith("251"):
        local = digits[3:]
    elif digits.startswith("0"):
        local = digits[1:]
    else:
        local = digits

    if len(local) != 9 or local[0] not in {"9", "7"}:
        return None, (
            "የስልክ ቁጥር ቅርጸት ትክክል አይደለም።\n"
            "እባክዎ እነዚህን ቅርጸቶች ይጠቀሙ: 09XXXXXXXX, 07XXXXXXXX, +2519XXXXXXXX"
        )

    return f"+251{local}", None


async def _register_phone(message: Message, raw_phone: str):
    phone_number, validation_error = _normalize_et_phone(raw_phone)
    if validation_error or not phone_number:
        await message.answer(validation_error or "የስልክ ቁጥር ማረጋገጥ አልተሳካም።")
        return

    try:
        data = await call_with_reauth(
            message.from_user,
            lambda token: client.register_phone(token, phone_number),
        )
        await message.answer(
            f"ስልክ ቁጥር ተመዝግቧል: {data.get('phone_number')}\nአሁን ጨዋታ መግባት ይችላሉ።",
            reply_markup=main_menu_keyboard(MINI_APP_URL if MINI_APP_URL else None),
        )
    except httpx.HTTPStatusError as exc:
        detail = "ስልክ ቁጥር መመዝገብ አልተቻለም።"
        try:
            payload = exc.response.json()
            if isinstance(payload, dict):
                if payload.get("phone_number"):
                    detail = "የስልክ ቁጥር ቅርጸት ትክክል አይደለም። ምሳሌ: +251912345678"
                elif payload.get("detail"):
                    detail = "ይህ ስልክ ቁጥር ቀድሞ ተመዝግቧል ወይም መመዝገብ አልተቻለም።"
        except Exception:
            pass
        await message.answer(detail)
    except Exception:
        await message.answer("አሁን ስልክ ቁጥር መመዝገብ አልተቻለም። ቆይተው ድጋሚ ይሞክሩ።")


@router.message(F.contact)
async def save_shared_contact(message: Message):
    if not message.contact:
        await message.answer("ኮንታክት አልተገኘም። እንደገና ይሞክሩ።")
        return
    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        await message.answer("እባክዎ የራስዎን ኮንታክት ብቻ ያጋሩ።")
        return
    await _register_phone(message, message.contact.phone_number or "")


@router.message(StateFilter(None), F.text.regexp(r".*[0-9]{9,}.*"))
async def save_manual_phone(message: Message):
    text = (message.text or "").strip()
    if not text or text.startswith("/"):
        return
    if text.casefold() == REGISTER_PHONE_BTN.casefold():
        return
    await _register_phone(message, text)
