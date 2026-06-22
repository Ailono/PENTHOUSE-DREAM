from aiogram import Router, types, F
from database.crud import get_user, add_balance, create_photo_hunt, get_pending_hunts, complete_photo_hunt
from database.database import get_db_session
from bot.keyboards import get_main_menu

router = Router()

HUNT_TARGETS = [
    "кот", "собака", "чашка", "книга", "стул",
    "телефон", "бутылка", "часы", "растение", "мяч",
]


@router.message(lambda msg: msg.text == "📸 Фотоохота")
async def cmd_photo_hunt(message: types.Message):
    session = await get_db_session()
    try:
        pending = await get_pending_hunts(session, message.from_user.id)
        if pending:
            hunt = pending[0]
            await message.answer(
                f"📸 У тебя активное задание:\n"
                f"Найди и сфотографируй: {hunt.target_item}\n"
                f"Награда: {hunt.reward} 🪙\n\n"
                "Пришли фото как файл или отмени командой /cancel_hunt"
            )
            return

        import random
        target = random.choice(HUNT_TARGETS)
        reward = random.randint(100, 500)

        await create_photo_hunt(session, message.from_user.id, target, reward)
        await session.commit()

        await message.answer(
            f"📸 Задание на фотоохоту!\n\n"
            f"🔍 Найди и сфотографируй: {target}\n"
            f"💰 Награда: {reward} 🪙\n\n"
            "Пришли фото как файл!"
        )
    finally:
        await session.close()


@router.message(F.photo | F.document)
async def handle_photo(message: types.Message):
    session = await get_db_session()
    try:
        pending = await get_pending_hunts(session, message.from_user.id)
        if not pending:
            return

        hunt = pending[0]
        await complete_photo_hunt(session, hunt.id, success=True)
        await add_balance(session, message.from_user.id, hunt.reward)
        await session.commit()

        await message.answer(
            f"📸 Фото принято! ✅\n"
            f"💰 +{hunt.reward} монет!\n\n"
            "Реальное распознавание через YOLO будет добавлено позже."
        )
    finally:
        await session.close()
