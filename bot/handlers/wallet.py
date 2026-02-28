import httpx
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from keyboards.main import BALANCE_BTN, DEPOSIT_BTN, HISTORY_BTN, WITHDRAW_BTN
from services.api_client import BackendClient
from services.auth import ensure_access_token

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
        token = await ensure_access_token(message.from_user)
        data = await client.get_balance(token)
    except Exception:
        await message.answer("Unable to fetch balance now. Please try again.")
        return
    await message.answer(f"Balance: {data['balance']} Birr")


@router.message(Command("balance"))
async def balance_cmd(message: Message):
    await _balance(message)


@router.message(F.text.casefold() == BALANCE_BTN.casefold())
async def balance_btn(message: Message):
    await _balance(message)


async def _deposit(message: Message):
    try:
        token = await ensure_access_token(message.from_user)
        info = await client.deposit_info(token)
    except Exception:
        await message.answer("Unable to load deposit instructions right now.")
        return
    await message.answer(
        "Send money to:\n"
        f"Telebirr Number: {info.get('telebirr_number', '0969146494')}\n"
        f"Account Name: {info.get('account_name', 'ፀዴ Bingo')}\n\n"
        "After sending, use /submit_deposit."
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
    await message.answer("Enter deposit amount (Birr):")


@router.message(DepositFlow.amount)
async def submit_deposit_amount(message: Message, state: FSMContext):
    await state.update_data(amount=(message.text or "").strip())
    await state.set_state(DepositFlow.reference)
    await message.answer("Enter Telebirr transaction reference:")


@router.message(DepositFlow.reference)
async def submit_deposit_reference(message: Message, state: FSMContext):
    await state.update_data(reference=(message.text or "").strip())
    await state.set_state(DepositFlow.sender_phone)
    await message.answer("Enter sender phone number:")


@router.message(DepositFlow.sender_phone)
async def submit_deposit_sender_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = str(data.get("amount", "")).strip()
    reference = str(data.get("reference", "")).strip()
    sender_phone = (message.text or "").strip()
    try:
        token = await ensure_access_token(message.from_user)
        req = await client.submit_deposit(token, amount=amount, telebirr_reference=reference, sender_phone=sender_phone)
        try:
            info = await client.deposit_info(token)
        except Exception:
            info = {}
        telebirr_number = info.get("telebirr_number", "0969146494")
        account_name = info.get("account_name", "ፀዴ Bingo")
        await message.answer(
            "Deposit submitted successfully.\n\n"
            "Telebirr message:\n"
            f"I sent {amount} Birr to {account_name} ({telebirr_number}).\n"
            f"Transaction Reference: {reference}\n"
            f"Sender Phone: {sender_phone}\n\n"
            f"Request status: {str(req.get('status', '')).upper()}.\n"
            "Admin will verify and approve/reject."
        )
    except httpx.HTTPStatusError as exc:
        detail = "Deposit submit failed."
        try:
            payload = exc.response.json()
            if isinstance(payload, dict) and payload.get("detail"):
                detail = str(payload["detail"])
        except Exception:
            pass
        await message.answer(detail)
    except Exception:
        await message.answer("Deposit submit failed. Please try again.")
    finally:
        await state.clear()


@router.message(Command("deposit_status"))
async def deposit_status(message: Message):
    try:
        token = await ensure_access_token(message.from_user)
        rows = await client.deposit_status(token)
    except Exception:
        await message.answer("Unable to load deposit status.")
        return
    if not rows:
        await message.answer("No deposit requests found.")
        return
    lines = ["Recent deposit requests:"]
    for r in rows[:10]:
        lines.append(
            f"- #{r['id']} | {r['amount']} Birr | {r['status'].upper()} | "
            f"Ref: {r.get('telebirr_reference', '-')}"
        )
    await message.answer("\n".join(lines))


async def _withdraw_start(message: Message, state: FSMContext):
    await state.set_state(WithdrawFlow.amount)
    await message.answer("Enter withdraw amount (Birr):")


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
    await message.answer("Enter Telebirr phone number to receive money:")


@router.message(WithdrawFlow.telebirr_phone)
async def withdraw_phone(message: Message, state: FSMContext):
    await state.update_data(telebirr_phone=(message.text or "").strip())
    await state.set_state(WithdrawFlow.account_holder_name)
    await message.answer("Enter account holder name:")


@router.message(WithdrawFlow.account_holder_name)
async def withdraw_holder_name(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = str(data.get("amount", "")).strip()
    phone = str(data.get("telebirr_phone", "")).strip()
    holder = (message.text or "").strip()
    try:
        token = await ensure_access_token(message.from_user)
        req = await client.submit_withdraw(token, amount=amount, telebirr_phone=phone, account_holder_name=holder)
        await message.answer(
            f"Withdraw submitted.\nRequest #{req['id']}\nStatus: {req['status']}\n"
            "Admin will process manually via Telebirr."
        )
    except httpx.HTTPStatusError as exc:
        detail = "Withdraw submit failed."
        try:
            payload = exc.response.json()
            if isinstance(payload, dict) and payload.get("detail"):
                detail = str(payload["detail"])
        except Exception:
            pass
        await message.answer(detail)
    except Exception:
        await message.answer("Withdraw submit failed. Please try again.")
    finally:
        await state.clear()


@router.message(Command("withdraw_status"))
async def withdraw_status(message: Message):
    try:
        token = await ensure_access_token(message.from_user)
        rows = await client.withdraw_status(token)
    except Exception:
        await message.answer("Unable to load withdraw status.")
        return
    if not rows:
        await message.answer("No withdraw requests found.")
        return
    lines = ["Recent withdraw requests:"]
    for r in rows[:10]:
        lines.append(
            f"- #{r['id']} | {r['amount']} Birr | {r['status'].upper()} | "
            f"Phone: {r.get('telebirr_phone', '-')}"
        )
    await message.answer("\n".join(lines))


async def _transactions(message: Message):
    try:
        token = await ensure_access_token(message.from_user)
        txns = await client.transactions(token)
    except Exception:
        await message.answer("Unable to load transaction history right now.")
        return

    if not txns:
        await message.answer("No transactions yet.")
        return

    rows = ["Recent transactions:"]
    for t in txns[:10]:
        txn_type = str(t.get("type", "")).upper()
        status = str(t.get("status", "")).upper()
        amount = t.get("amount", "0")
        created_at = str(t.get("created_at", ""))[:19].replace("T", " ")
        rows.append(f"- {created_at} | {txn_type} | {amount} Birr | {status}")

    await message.answer("\n".join(rows))


@router.message(Command(commands=["transactions", "history"]))
async def transactions_cmd(message: Message):
    await _transactions(message)


@router.message(F.text.casefold() == HISTORY_BTN.casefold())
async def transactions_btn(message: Message):
    await _transactions(message)
