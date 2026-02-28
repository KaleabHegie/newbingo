import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from handlers import room_join, start, wallet


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(wallet.router)
    dp.include_router(room_join.router)
    return dp


async def main() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = create_dispatcher()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
