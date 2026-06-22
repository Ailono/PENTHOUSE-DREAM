from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.crud import get_user, get_user_inventory, get_user_achievements
from database.database import get_db_session
from game_logic.achievements import ACHIEVEMENTS
from game_logic.economy import room_level_up_cost, room_max_level
from game_logic.achievement_checker import check_and_unlock

router = Router()


@router.message(lambda msg: msg.text == "📊 Статистика")
async def cmd_stats(message: types.Message):
    session = await get_db_session()
    try:
        user = await get_user(session, message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден.")
            return

        inv = await get_user_inventory(session, message.from_user.id)
        ach = await get_user_achievements(session, message.from_user.id)

        text = (
            f"📊 Статистика игрока\n\n"
            f"💰 Баланс: {user.balance:,}\n"
            f"🏠 Уровень комнаты: {user.room_level}\n"
            f"😊 Счастье: {user.happiness}%\n"
            f"🎒 Предметов: {len(inv)}\n"
            f"🏆 Достижений: {len(ach)}\n"
            f"📅 Зарегистрирован: {user.created_at.date() if user.created_at else 'сегодня'}"
        )

        builder = InlineKeyboardBuilder()
        builder.button(text="🏆 Достижения", callback_data="profile_achievements")
        builder.button(text="🏠 Улучшить комнату", callback_data="profile_room_upgrade")
        builder.adjust(1)

        await message.answer(text, reply_markup=builder.as_markup())
    finally:
        await session.close()


@router.callback_query(F.data == "profile_achievements")
async def show_achievements(callback: types.CallbackQuery):
    session = await get_db_session()
    try:
        achievements = await get_user_achievements(session, callback.from_user.id)
        unlocked_names = {a.achievement_name for a in achievements}

        text_parts = ["🏆 Достижения\n"]
        unlocked_count = len(unlocked_names)
        total = len(ACHIEVEMENTS)
        text_parts.append(f"Прогресс: {unlocked_count}/{total}\n\n")

        for key, info in ACHIEVEMENTS.items():
            icon = info.get("icon", "🏅")
            name = info.get("name", key)
            desc = info.get("description", "")
            reward = info.get("reward", 0)
            unlocked = key in unlocked_names
            status = "✅" if unlocked else "🔒"
            text_parts.append(f"{status} {icon} {name} — {reward}🪙\n  {desc}\n")

        await callback.message.edit_text(
            "\n".join(text_parts),
            reply_markup=None,
        )
        await callback.answer()
    finally:
        await session.close()


@router.callback_query(F.data == "profile_room_upgrade")
async def upgrade_room(callback: types.CallbackQuery):
    session = await get_db_session()
    try:
        user = await get_user(session, callback.from_user.id)
        if not user:
            await callback.answer("❌ Не найден", show_alert=True)
            return

        current_level = user.room_level
        if current_level >= room_max_level():
            await callback.answer("🏠 Максимальный уровень!", show_alert=True)
            return

        cost = room_level_up_cost(current_level)
        if user.balance < cost:
            await callback.answer(f"❌ Нужно {cost:,} монет (есть {user.balance:,})", show_alert=True)
            return

        user.balance -= cost
        user.room_level += 1
        await session.commit()

        await check_and_unlock(callback.from_user.id, session, {"room_level": user.room_level})

        await callback.answer(f"🏠 Комната улучшена до {user.room_level} уровня! -{cost}🪙", show_alert=True)

        new_text = (
            f"🏠 Комната улучшена!\n\n"
            f"Уровень: {user.room_level}\n"
            f"💰 Баланс: {user.balance:,}"
        )
        await callback.message.edit_text(new_text)
    finally:
        await session.close()
