from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
import httpx

from keyboards.main import JOIN_10_BTN, register_only_keyboard
from services.api_client import BackendClient
from services.auth import call_with_reauth

router = Router()
client = BackendClient()


async def _join(message: Message, bet_amount: int):
    try:
        profile = await call_with_reauth(message.from_user, client.me)
        if not profile.get("phone_registered"):
            await message.answer(
                "እባክዎ መጀመሪያ ስልክ ቁጥርዎን ይመዝግቡ።",
                reply_markup=register_only_keyboard(),
            )
            return
        rooms = await call_with_reauth(message.from_user, client.rooms)
        room = next((r for r in rooms if r["bet_amount"] == bet_amount), None)
        if not room:
            await message.answer("ሩሙ አልተገኘም።")
            return

        cartelas_payload = await call_with_reauth(
            message.from_user,
            lambda token: client.cartelas(token, room_id=room["id"]),
        )
        available = [c for c in cartelas_payload.get("cartelas", []) if not c.get("is_taken")]
        if not available:
            await message.answer("አሁን የሚገኙ ካርቴላዎች የሉም። ቀጣዩን ጨዋታ ይጠብቁ።")
            return

        selected = available[0]
        result = await call_with_reauth(
            message.from_user,
            lambda token: client.join_room(token, room_id=room["id"], cartela_id=selected["id"]),
        )
    except httpx.HTTPStatusError as exc:
        detail = "አሁን መቀላቀል አልተቻለም። ቀሪ ሂሳብዎን ያረጋግጡ።"
        try:
            payload = exc.response.json()
            if isinstance(payload, dict) and payload.get("detail"):
                detail = "መቀላቀል አልተቻለም። ቆይተው ድጋሚ ይሞክሩ።"
        except Exception:
            pass
        await message.answer(detail)
        return
    except Exception:
        await message.answer("አሁን መቀላቀል አልተቻለም። ቆይተው ድጋሚ ይሞክሩ።")
        return
    await message.answer(
        f"{bet_amount} ብር ሩም ገብተዋል።\n"
        f"ጨዋታ #{result['game_id']} | ካርቴላ {selected['id']}\n"
        "ለመጫወት የሚኒ አፕ ሊንኩን ይጠቀሙ።"
    )


@router.message(Command("join10"))
async def join10_cmd(message: Message):
    await _join(message, 10)


@router.message(F.text.casefold() == JOIN_10_BTN.casefold())
async def join10_btn(message: Message):
    await _join(message, 10)
