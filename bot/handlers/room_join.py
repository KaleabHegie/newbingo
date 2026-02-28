from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
import httpx

from keyboards.main import JOIN_10_BTN, register_only_keyboard
from services.api_client import BackendClient
from services.auth import ensure_access_token

router = Router()
client = BackendClient()


async def _join(message: Message, bet_amount: int):
    try:
        token = await ensure_access_token(message.from_user)
        profile = await client.me(token)
        if not profile.get("phone_registered"):
            await message.answer(
                "Please register your phone first using the 'Register Phone' button.",
                reply_markup=register_only_keyboard(),
            )
            return
        rooms = await client.rooms(token)
        room = next((r for r in rooms if r["bet_amount"] == bet_amount), None)
        if not room:
            await message.answer("Room not available")
            return

        cartelas_payload = await client.cartelas(token, room_id=room["id"])
        available = [c for c in cartelas_payload.get("cartelas", []) if not c.get("is_taken")]
        if not available:
            await message.answer("No cartelas available right now. Please wait for the next game.")
            return

        selected = available[0]
        result = await client.join_room(token, room_id=room["id"], cartela_id=selected["id"])
    except httpx.HTTPStatusError as exc:
        detail = "Unable to join right now. Check balance and try again."
        try:
            payload = exc.response.json()
            if isinstance(payload, dict) and payload.get("detail"):
                detail = str(payload["detail"])
        except Exception:
            pass
        await message.answer(detail)
        return
    except Exception:
        await message.answer("Unable to join right now. Please try again.")
        return
    await message.answer(
        f"Joined {bet_amount} Birr room.\n"
        f"Game #{result['game_id']} | Cartela {selected['id']}\n"
        "Use the Open Mini App button to play."
    )


@router.message(Command("join10"))
async def join10_cmd(message: Message):
    await _join(message, 10)


@router.message(F.text.casefold() == JOIN_10_BTN.casefold())
async def join10_btn(message: Message):
    await _join(message, 10)
