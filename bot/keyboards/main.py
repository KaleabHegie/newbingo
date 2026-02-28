from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

BALANCE_BTN = "Balance"
REGISTER_PHONE_BTN = "Register Phone"
JOIN_10_BTN = "Join 10 Birr"
DEPOSIT_BTN = "Deposit"
WITHDRAW_BTN = "Withdraw"
HISTORY_BTN = "History"
MINI_APP_BTN = "Open Mini App"


def register_only_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=REGISTER_PHONE_BTN)]],
        resize_keyboard=True,
        is_persistent=True,
    )


def main_menu_keyboard(miniapp_url: str | None = None) -> ReplyKeyboardMarkup:
    menu_rows: list[list[KeyboardButton]] = [
        [KeyboardButton(text=BALANCE_BTN), KeyboardButton(text=HISTORY_BTN)],
    ]
    if miniapp_url:
        menu_rows.append([KeyboardButton(text=MINI_APP_BTN, web_app=WebAppInfo(url=miniapp_url))])
    menu_rows.append([KeyboardButton(text=DEPOSIT_BTN), KeyboardButton(text=WITHDRAW_BTN)])

    return ReplyKeyboardMarkup(
        keyboard=menu_rows,
        resize_keyboard=True,
        is_persistent=True,
    )


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Share Phone Number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def miniapp_keyboard(miniapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open Bingo Mini App", web_app=WebAppInfo(url=miniapp_url))]
        ]
    )
