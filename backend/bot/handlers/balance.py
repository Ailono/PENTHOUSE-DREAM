from aiogram import Router, types
from database.crud import get_user
from database.database import get_db_session

router = Router()


@router.message(lambda msg: msg.text == "💰 Баланс")
async def cmd_balance(message: types.Message):
    session = await get_db_session()
    try:
        user = await get_user(session, message.from_user.id)
        if user:
            await message.answer(f"💰 Твой баланс: {user.balance} монет")
        else:
            await message.answer("❌ Пользователь не найден. Напиши /start")
    finally:
        await session.close()
