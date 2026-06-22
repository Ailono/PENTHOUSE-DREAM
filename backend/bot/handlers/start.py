from aiogram import Router, types
from aiogram.filters import CommandStart
from database.crud import get_user, create_user
from bot.keyboards import get_main_menu
from database.database import get_db_session

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    session = await get_db_session()
    try:
        user = await get_user(session, message.from_user.id)
        if not user:
            user = await create_user(session, message.from_user.id, message.from_user.username)
            await session.commit()
            text = (
                "👋 Добро пожаловать в Penthouse Dream!\n\n"
                "🚀 Твоя задача — построить комнату мечты, "
                "заработать монеты и наслаждаться жизнью.\n\n"
                "Твой стартовый баланс: 1000 монет ✨"
            )
        else:
            text = (
                f"Привет, {message.from_user.full_name}! 👋\n"
                f"Твой баланс: {user.balance} 💰\n"
                f"Уровень комнаты: {user.room_level}"
            )
        await message.answer(text, reply_markup=get_main_menu())
    finally:
        await session.close()
