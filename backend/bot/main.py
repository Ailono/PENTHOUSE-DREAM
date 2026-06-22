import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import settings
from bot.handlers import start, balance, profile, shop, work, roulette, photo_hunt, inventory
from database.models import Base
from database.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=settings.bot_token)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(balance.router)
    dp.include_router(profile.router)
    dp.include_router(shop.router)
    dp.include_router(work.router)
    dp.include_router(roulette.router)
    dp.include_router(photo_hunt.router)
    dp.include_router(inventory.router)

    logger.info("Bot started polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
