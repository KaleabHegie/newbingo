import httpx
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from keyboards.main import BALANCE_BTN, DEPOSIT_BTN, HISTORY_BTN, WITHDRAW_BTN
from services.api_client import BackendClient
from services.auth import call_with_reauth

router = Router()
client = BackendClient()


class DepositFlow(StatesGroup):
    amount = State()
    reference = State()
    sender_phone = State()


class WithdrawFlow(StatesGroup):
    amount = State()
    telebirr_phone = State()
    account_holder_name = State()


async def _balance(message: Message):
    try:
        data = await call_with_reauth(message.from_user, client.get_balance)
    except Exception:
        await message.answer("አሁን ቀሪ ሂሳብ ማየት አልተቻለም። ቆይተው ድጋሚ ይሞክሩ።")
        return
    await message.answer(f"ቀሪ ሂሳብ: {data['balance']} ብር")


@router.message(Command("balance"))
async def balance_cmd(message: Message):
    await _balance(message)


@router.message(F.text.casefold() == BALANCE_BTN.casefold())
async def balance_btn(message: Message):
    await _balance(message)


async def _deposit(message: Message):
    try:
        info = await call_with_reauth(message.from_user, client.deposit_info)
    except Exception:
        await message.answer("አሁን የማስገቢያ መመሪያ ማሳየት አልተቻለም።")
        return
    await message.answer(
        "ገንዘብ ወደዚህ ይላኩ:\n"
        f"ቴሌብር ቁጥር: {info.get('telebirr_number', '0969146494')}\n"
        f"የአካውንት ስም: {info.get('account_name', 'ፀዴ Bingo')}\n\n"
        "ከላኩ በኋላ /submit_deposit ይጠቀሙ።"
    )


@router.message(Command("deposit"))
async def deposit_cmd(message: Message):
    await _deposit(message)


@router.message(F.text.casefold() == DEPOSIT_BTN.casefold())
async def deposit_btn(message: Message):
    await _deposit(message)


@router.message(Command("submit_deposit"))
async def submit_deposit_start(message: Message, state: FSMContext):
    await state.set_state(DepositFlow.amount)
    await message.answer("የሚያስገቡትን መጠን (ብር) ያስገቡ:")


@router.message(DepositFlow.amount)
async def submit_deposit_amount(message: Message, state: FSMContext):
    await state.update_data(amount=(message.text or "").strip())
    await state.set_state(DepositFlow.reference)
    await message.answer("የቴሌብር የግብይት መልዕክት ያስገቡ:")


@router.message(DepositFlow.reference)
async def submit_deposit_reference(message: Message, state: FSMContext):
    await state.update_data(reference=(message.text or "").strip())
    await state.set_state(DepositFlow.sender_phone)
    await message.answer("የላኪውን ስልክ ቁጥር ያስገቡ:")


@router.message(DepositFlow.sender_phone)
async def submit_deposit_sender_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = str(data.get("amount", "")).strip()
    reference = str(data.get("reference", "")).strip()
    sender_phone = (message.text or "").strip()
    try:
        req = await call_with_reauth(
            message.from_user,
            lambda token: client.submit_deposit(token, amount=amount, telebirr_reference=reference, sender_phone=sender_phone),
        )
        try:
            info = await call_with_reauth(message.from_user, client.deposit_info)
        except Exception:
            info = {}
        telebirr_number = info.get("telebirr_number", "0969146494")
        account_name = info.get("account_name", "ፀዴ Bingo")
        await message.answer(
            "የማስገቢያ ጥያቄዎ ተልኳል።\n\n"
            "የቴሌብር መረጃ:\n"
            f"{amount} ብር ወደ {account_name} ({telebirr_number}) ተልኳል።\n"
            f"የግብይት ማጣቀሻ: {reference}\n"
            f"የላኪ ስልክ: {sender_phone}\n\n"
            f"ሁኔታ: {str(req.get('status', '')).upper()}.\n"
            "አድሚን ያረጋግጣል።"
        )
    except httpx.HTTPStatusError as exc:
        detail = "የማስገቢያ ጥያቄ መላክ አልተቻለም።"
        try:
            payload = exc.response.json()
            if isinstance(payload, dict) and payload.get("detail"):
                detail = "የማስገቢያ ጥያቄ መላክ አልተቻለም። ድጋሚ ይሞክሩ።"
        except Exception:
            pass
        await message.answer(detail)
    except Exception:
        await message.answer("የማስገቢያ ጥያቄ መላክ አልተቻለም። ድጋሚ ይሞክሩ።")
    finally:
        await state.clear()


@router.message(Command("deposit_status"))
async def deposit_status(message: Message):
    try:
        rows = await call_with_reauth(message.from_user, client.deposit_status)
    except Exception:
        await message.answer("የማስገቢያ ሁኔታ ማሳየት አልተቻለም።")
        return
    if not rows:
        await message.answer("የማስገቢያ ጥያቄ አልተገኘም።")
        return
    lines = ["የቅርብ ጊዜ የማስገቢያ ጥያቄዎች:"]
    for r in rows[:10]:
        lines.append(
            f"- #{r['id']} | {r['amount']} ብር | {r['status'].upper()} | "
            f"ማጣቀሻ: {r.get('telebirr_reference', '-')}"
        )
    await message.answer("\n".join(lines))


async def _withdraw_start(message: Message, state: FSMContext):
    await state.set_state(WithdrawFlow.amount)
    await message.answer("የሚያወጡትን መጠን (ብር) ያስገቡ:")


@router.message(Command("withdraw"))
async def withdraw_cmd(message: Message, state: FSMContext):
    await _withdraw_start(message, state)


@router.message(F.text.casefold() == WITHDRAW_BTN.casefold())
async def withdraw_btn(message: Message, state: FSMContext):
    await _withdraw_start(message, state)


@router.message(WithdrawFlow.amount)
async def withdraw_amount(message: Message, state: FSMContext):
    await state.update_data(amount=(message.text or "").strip())
    await state.set_state(WithdrawFlow.telebirr_phone)
    await message.answer("ገንዘብ የሚቀበል የቴሌብር ስልክ ቁጥር ያስገቡ:")


@router.message(WithdrawFlow.telebirr_phone)
async def withdraw_phone(message: Message, state: FSMContext):
    await state.update_data(telebirr_phone=(message.text or "").strip())
    await state.set_state(WithdrawFlow.account_holder_name)
    await message.answer("የአካውንት ባለቤት ስም ያስገቡ:")


@router.message(WithdrawFlow.account_holder_name)
async def withdraw_holder_name(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = str(data.get("amount", "")).strip()
    phone = str(data.get("telebirr_phone", "")).strip()
    holder = (message.text or "").strip()
    try:
        req = await call_with_reauth(
            message.from_user,
            lambda token: client.submit_withdraw(token, amount=amount, telebirr_phone=phone, account_holder_name=holder),
        )
        await message.answer(
            f"የማውጫ ጥያቄ ተልኳል።\nጥያቄ #{req['id']}\nሁኔታ: {req['status']}\n"
            "አድሚን በቴሌብር በእጅ ያስኬዳል።"
        )
    except httpx.HTTPStatusError as exc:
        detail = "የማውጫ ጥያቄ መላክ አልተቻለም።"
        try:
            payload = exc.response.json()
            if isinstance(payload, dict) and payload.get("detail"):
                detail = "የማውጫ ጥያቄ መላክ አልተቻለም። ድጋሚ ይሞክሩ።"
        except Exception:
            pass
        await message.answer(detail)
    except Exception:
        await message.answer("የማውጫ ጥያቄ መላክ አልተቻለም። ድጋሚ ይሞክሩ።")
    finally:
        await state.clear()


@router.message(Command("withdraw_status"))
async def withdraw_status(message: Message):
    try:
        rows = await call_with_reauth(message.from_user, client.withdraw_status)
    except Exception:
        await message.answer("የማውጫ ሁኔታ ማሳየት አልተቻለም።")
        return
    if not rows:
        await message.answer("የማውጫ ጥያቄ አልተገኘም።")
        return
    lines = ["የቅርብ ጊዜ የማውጫ ጥያቄዎች:"]
    for r in rows[:10]:
        lines.append(
            f"- #{r['id']} | {r['amount']} ብር | {r['status'].upper()} | "
            f"ስልክ: {r.get('telebirr_phone', '-')}"
        )
    await message.answer("\n".join(lines))


async def _transactions(message: Message):
    try:
        txns = await call_with_reauth(message.from_user, client.transactions)
    except Exception:
        await message.answer("አሁን የግብይት ታሪክ ማሳየት አልተቻለም።")
        return

    if not txns:
        await message.answer("እስካሁን ምንም ግብይት የለም።")
        return

    rows = ["የቅርብ ጊዜ ግብይቶች:"]
    for t in txns[:10]:
        txn_type = str(t.get("type", "")).upper()
        status = str(t.get("status", "")).upper()
        amount = t.get("amount", "0")
        created_at = str(t.get("created_at", ""))[:19].replace("T", " ")
        rows.append(f"- {created_at} | {txn_type} | {amount} ብር | {status}")

    await message.answer("\n".join(rows))


@router.message(Command(commands=["transactions", "history"]))
async def transactions_cmd(message: Message):
    await _transactions(message)


@router.message(F.text.casefold() == HISTORY_BTN.casefold())
async def transactions_btn(message: Message):
    await _transactions(message)
