import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import settings
from bot.handlers import start, balance, profile, shop, work, roulette, photo_hunt, inventory

logger = logging.getLogger(__name__)

bot = Bot(token=settings.bot_token)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(balance.router)
dp.include_router(profile.router)
dp.include_router(shop.router)
dp.include_router(work.router)
dp.include_router(roulette.router)
dp.include_router(photo_hunt.router)
dp.include_router(inventory.router)


async def process_update(data: dict) -> None:
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)


async def set_webhook(url: str) -> None:
    await bot.set_webhook(url)
    info = await bot.get_webhook_info()
    logger.info(f"Webhook set to {info.url}")


async def delete_webhook() -> None:
    await bot.delete_webhook()
    logger.info("Webhook deleted")
