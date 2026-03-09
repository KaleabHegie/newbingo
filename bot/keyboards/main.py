from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

BALANCE_BTN = "ቀሪ ሂሳብ"
REGISTER_PHONE_BTN = "ስልክ ቁጥር መመዝገብ"
JOIN_10_BTN = "10 ብር ሩም ግባ"
DEPOSIT_BTN = "ገንዘብ አስገባ"
WITHDRAW_BTN = "ገንዘብ አውጣ"
HISTORY_BTN = "ታሪክ"
MINI_APP_BTN = "ሚኒ አፕ ክፈት"


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
    menu_rows.append([KeyboardButton(text=DEPOSIT_BTN), KeyboardButton(text=WITHDRAW_BTN)])

    return ReplyKeyboardMarkup(
        keyboard=menu_rows,
        resize_keyboard=True,
        is_persistent=True,
    )


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="ስልክ ቁጥሬን አጋራ", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def miniapp_keyboard(miniapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ወደ ቢንጎ ሚኒ አፕ ግባ", web_app=WebAppInfo(url=miniapp_url))]
        ]
    )
