from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.crud import get_todays_shop, purchase_item, get_user, add_balance
from database.database import get_db_session
from bot.keyboards import get_shop_menu, get_main_menu
from game_logic.shop import open_mystery_box, need_regeneration, generate_shop_items, MYSTERY_BOX_COST
from game_logic.achievement_checker import check_and_unlock

router = Router()

RARITY_EMOJI = {
    "common": "🟢",
    "uncommon": "🔵",
    "rare": "🟣",
    "legendary": "🟠",
}

RARITY_NAMES = {
    "common": "Обычный",
    "uncommon": "Необычный",
    "rare": "Редкий",
    "legendary": "Легендарный",
}


@router.message(lambda msg: msg.text == "🏪 Магазин")
async def cmd_shop(message: types.Message):
    session = await get_db_session()
    try:
        if need_regeneration():
            pass

        items = await get_todays_shop(session)

        if not items:
            await message.answer(
                "🏪 Магазин сегодня пуст! Загляни завтра 👀",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            return

        builder = InlineKeyboardBuilder()
        for item in items:
            emoji = RARITY_EMOJI.get(item.rarity, "⬜")
            hot_mark = " 🔥" if item.is_hot else ""
            label = f"{emoji} {item.name} — {item.price}🪙{hot_mark}"
            builder.button(text=label, callback_data=f"buy_{item.id}")
        builder.button(text="🎁 Чёрный ящик (500🪙)", callback_data="shop_mystery_box")
        builder.button(text="⬅️ Закрыть", callback_data="shop_close")
        builder.adjust(1, repeat=True)

        await message.answer(
            "🏪 Магазин\n"
            "🟢 Обычный  🔵 Необычный  🟣 Редкий  🟠 Легендарный  🔥 Горячий (-30%)",
            reply_markup=builder.as_markup(),
        )
    finally:
        await session.close()


@router.callback_query(lambda c: c.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    session = await get_db_session()
    try:
        result = await purchase_item(session, callback.from_user.id, item_id)
        await session.commit()

        if "error" in result:
            await callback.answer(f"❌ {result['error']}", show_alert=True)
        else:
            new_ach = await check_and_unlock(callback.from_user.id, session)
            await session.commit()

            ach_text = ""
            if new_ach:
                ach_text = "\n\n🏆 Достижение: " + new_ach[0]["icon"] + " " + new_ach[0]["name"]

            await callback.answer(
                f"✅ Куплено: {result['item_name']}!",
                show_alert=True,
            )
            await callback.message.edit_text(
                f"✅ Ты купил {result['item_name']}!\n"
                f"💰 Остаток: {result['balance']} монет"
                f"{ach_text}"
            )
    finally:
        await session.close()


@router.callback_query(F.data == "shop_mystery_box")
async def process_mystery_box(callback: types.CallbackQuery):
    session = await get_db_session()
    try:
        user = await get_user(session, callback.from_user.id)
        if not user or user.balance < MYSTERY_BOX_COST:
            await callback.answer(f"❌ Нужно {MYSTERY_BOX_COST} монет!", show_alert=True)
            return

        await add_balance(session, callback.from_user.id, -MYSTERY_BOX_COST)
        result = open_mystery_box()
        await session.commit()

        emoji = RARITY_EMOJI.get(result["rarity"], "📦")
        rarity_name = RARITY_NAMES.get(result["rarity"], "")

        text = (
            f"🎁 Чёрный ящик открыт!\n\n"
            f"{emoji} {result['name']}\n"
            f"📊 Редкость: {rarity_name}\n"
            f"💎 Стоимость: ~{result['value']} 🪙\n\n"
            f"💰 Баланс: {user.balance - MYSTERY_BOX_COST}"
        )
        await callback.message.edit_text(text)
        await callback.answer(
            f"{emoji} {result['name']} ({rarity_name})",
            show_alert=True,
        )
    finally:
        await session.close()


@router.callback_query(lambda c: c.data == "shop_close")
async def close_shop(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Магазин закрыт")
