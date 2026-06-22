from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.crud import get_user_inventory, equip_item
from database.database import get_db_session

router = Router()


@router.message(lambda msg: msg.text == "🎒 Инвентарь")
async def cmd_inventory(message: types.Message):
    session = await get_db_session()
    try:
        items = await get_user_inventory(session, message.from_user.id)
        if not items:
            await message.answer("🎒 Инвентарь пуст. Купи что-нибудь в магазине!")
            return

        builder = InlineKeyboardBuilder()
        for item in items:
            emoji = {"common": "🟢", "uncommon": "🔵", "rare": "🟣", "legendary": "🟠"}.get(item["rarity"], "⬜")
            equipped = " ✅" if item["equipped"] else ""
            label = f"{emoji} {item['name']}{equipped}"
            builder.button(text=label, callback_data=f"inv_{item['id']}")
        builder.adjust(1, repeat=True)

        await message.answer(
            "🎒 Твой инвентарь:\n"
            "Нажми на предмет чтобы экипировать",
            reply_markup=builder.as_markup(),
        )
    finally:
        await session.close()


@router.callback_query(lambda c: c.data.startswith("inv_"))
async def process_equip(callback: types.CallbackQuery):
    inv_id = int(callback.data.split("_")[1])
    session = await get_db_session()
    try:
        success = await equip_item(session, callback.from_user.id, inv_id)
        await session.commit()
        if success:
            await callback.answer("✅ Предмет экипирован!", show_alert=True)
        else:
            await callback.answer("❌ Предмет не найден", show_alert=True)
    finally:
        await session.close()
