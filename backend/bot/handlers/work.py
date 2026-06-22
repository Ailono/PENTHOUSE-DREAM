import time
from datetime import datetime
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.crud import get_user, add_balance, update_happiness, get_user_inventory, create_business, get_user_businesses, remove_inventory_item
from database.database import get_db_session
from bot.keyboards import get_work_menu, get_main_menu
from game_logic.minigames import (
    RatHuntGame, CleaningGame, LotteryGame, AlchemyGame,
    NightClubGame, start_delivery, check_delivery,
    get_mining_income, get_mining_upgrade_cost,
    get_garden, MINING_BASE_RATE, MINING_PER_LEVEL,
    RAT_HUNT_ROUNDS,
)

router = Router()

WORK_EMOJI = {
    "rat_hunt": "🐀", "cleaning": "🧹", "gardening": "🌱",
    "lottery": "🎲", "alchemy": "⚗️", "delivery": "📦",
    "mining": "⛏️", "nightclub": "🎵", "photo_hunt": "📸",
}
WORK_NAMES = {
    "rat_hunt": "Охота на крысу", "cleaning": "Уборка комнаты",
    "gardening": "Садоводство", "lottery": "Лотерея",
    "alchemy": "Алхимия", "delivery": "Курьерские миссии",
    "mining": "Майнинг", "nightclub": "Ночной клуб",
    "photo_hunt": "Фотоохота",
}

_games: dict[int, RatHuntGame | CleaningGame | NightClubGame] = {}


@router.message(lambda msg: msg.text == "💼 Работа")
async def cmd_work(message: types.Message):
    await message.answer("💼 Выбери способ заработка:", reply_markup=get_work_menu())


# === BACK ===

@router.callback_query(F.data == "work_back")
async def back_to_menu(callback: types.CallbackQuery):
    _games.pop(callback.from_user.id, None)
    await callback.message.delete()
    await callback.message.answer("Главное меню:", reply_markup=get_main_menu())
    await callback.answer()


# === RAT HUNT ===

@router.callback_query(F.data == "work_rat_hunt")
async def start_rat_hunt(callback: types.CallbackQuery):
    game = RatHuntGame()
    _games[callback.from_user.id] = game
    await show_rat_board(callback.message, game)


async def show_rat_board(message: types.Message, game: RatHuntGame):
    builder = InlineKeyboardBuilder()
    for i in range(9):
        emoji = "🐀" if i == game.rat_pos else "⬜"
        builder.button(text=emoji, callback_data=f"rat_{i}")
    builder.adjust(3)
    text = (
        f"🐀 Охота на крысу! Раунд {game.round + 1}/{RAT_HUNT_ROUNDS}\n"
        f"Попаданий: {game.hits} | Промахов: {game.misses}"
    )
    await message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("rat_"))
async def rat_guess(callback: types.CallbackQuery):
    game = _games.get(callback.from_user.id)
    if not game or not isinstance(game, RatHuntGame):
        await callback.answer("Игра не найдена", show_alert=True)
        return

    pos = int(callback.data.split("_")[1])
    result = game.guess(pos)

    if result.get("game_over"):
        session = await get_db_session()
        try:
            user = await get_user(session, callback.from_user.id)
            if user:
                await add_balance(session, callback.from_user.id, result["total"])
                await update_happiness(session, callback.from_user.id, 2)
                await session.commit()
        finally:
            await session.close()

        bonus_text = f"\n🎯 Бонус без промахов: +{result['bonus']}!" if result.get("bonus") else ""
        await callback.message.edit_text(
            f"🐀 Охота завершена!\n\n"
            f"Попаданий: {result['hits']}/{RAT_HUNT_ROUNDS}\n"
            f"💰 Заработано: {result['total']} монет{bonus_text}",
            reply_markup=get_work_menu(),
        )
        _games.pop(callback.from_user.id, None)
        await callback.answer(f"✅ +{result['total']} монет!")
        return

    if result.get("hit"):
        await callback.answer(f"✅ +{result['coins']} монет!", show_alert=False)
    else:
        await callback.answer("❌ Мимо!", show_alert=False)

    await show_rat_board(callback.message, game)


# === CLEANING ===

@router.callback_query(F.data == "work_cleaning")
async def start_cleaning(callback: types.CallbackQuery):
    game = CleaningGame()
    _games[callback.from_user.id] = game
    await show_cleaning_board(callback.message, game)


async def show_cleaning_board(message: types.Message, game: CleaningGame):
    board = game.get_board_state()
    builder = InlineKeyboardBuilder()
    for spot in board:
        if spot["cleaned"]:
            builder.button(text="✅", callback_data=f"clean_done")
        else:
            label = f"🧹 Пятно {spot['id'] + 1}"
            if spot["tough"]:
                label += f" ({spot['progress']})"
            builder.button(text=label, callback_data=f"clean_{spot['id']}")
    builder.adjust(2)
    await message.edit_text(
        f"🧹 Уборка комнаты!\nВремя: {game.time_limit - int(time.time() - game.start_time)}с\nЧисти пятна!",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("clean_"))
async def clean_spot(callback: types.CallbackQuery):
    if callback.data == "clean_done":
        await callback.answer()
        return

    spot_id = int(callback.data.split("_")[1])
    game = _games.get(callback.from_user.id)
    if not game or not isinstance(game, CleaningGame):
        await callback.answer("Игра не найдена", show_alert=True)
        return

    result = game.clean(spot_id)

    if isinstance(result, dict) and result.get("all_cleaned"):
        session = await get_db_session()
        try:
            user = await get_user(session, callback.from_user.id)
            if user:
                await add_balance(session, callback.from_user.id, result["total"])
                await update_happiness(session, callback.from_user.id, 1)
                await session.commit()
        finally:
            await session.close()

        await callback.message.edit_text(
            f"🧹 Вся комната чистая! ✨\n"
            f"💰 База: 100 + бонус: {result['bonus']} = {result['total']} монет",
            reply_markup=get_work_menu(),
        )
        _games.pop(callback.from_user.id, None)
        await callback.answer(f"✅ +{result['total']} монет!")
        return

    if isinstance(result, dict) and "error" in result:
        await callback.answer(result["error"], show_alert=True)
        return

    game = _games.get(callback.from_user.id)
    if game:
        await show_cleaning_board(callback.message, game)
    await callback.answer()


# === GARDENING ===

@router.callback_query(F.data == "work_gardening")
async def garden_menu(callback: types.CallbackQuery):
    garden = get_garden(callback.from_user.id)
    status = garden.status()
    builder = InlineKeyboardBuilder()
    builder.button(text="💧 Полить", callback_data="garden_water")
    builder.button(text="🌿 Удобрить", callback_data="garden_fertilize")
    builder.button(text="🌾 Собрать", callback_data="garden_harvest")
    builder.button(text="⬅️ Назад", callback_data="work_back")
    builder.adjust(2)

    if not status["alive"]:
        text = "🌱 Твой сад погиб... Начни заново с /start"
        garden.__init__()
    else:
        text = (
            f"🌱 Твой сад ({status['plant_type']})\n\n"
            f"💧 Вода: {status['water']}%\n"
            f"❤️ Здоровье: {status['health']}%\n"
            f"🌿 Рост: {status['growth_pct']}%\n"
            f"{'🌾 Готово к сбору!' if status['growth_pct'] >= 100 else ''}"
        )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "garden_water")
async def garden_water(callback: types.CallbackQuery):
    garden = get_garden(callback.from_user.id)
    result = garden.water_plant()
    await callback.answer(f"💧 Вода: {result['water']}%, Рост: {result['growth']}%")
    await garden_menu(callback)


@router.callback_query(F.data == "garden_fertilize")
async def garden_fertilize(callback: types.CallbackQuery):
    session = await get_db_session()
    try:
        user = await get_user(session, callback.from_user.id)
        if user and user.balance >= 30:
            await add_balance(session, callback.from_user.id, -30)
            await session.commit()
            garden = get_garden(callback.from_user.id)
            result = garden.fertilize()
            await callback.answer(f"🌿 Рост: {result['growth']}% (-30 монет)")
        else:
            await callback.answer("❌ Нужно 30 монет для удобрения", show_alert=True)
    finally:
        await session.close()
    await garden_menu(callback)


@router.callback_query(F.data == "garden_harvest")
async def garden_harvest(callback: types.CallbackQuery):
    garden = get_garden(callback.from_user.id)
    result = garden.harvest()
    if result["harvested"]:
        session = await get_db_session()
        try:
            user = await get_user(session, callback.from_user.id)
            if user:
                await add_balance(session, callback.from_user.id, result["reward"])
                await update_happiness(session, callback.from_user.id, 3)
                await session.commit()
        finally:
            await session.close()
        await callback.answer(f"🎉 Собран урожай! +{result['reward']} монет!", show_alert=True)
    else:
        await callback.answer(f"🌿 Рост: {result['growth']}/{result['needed']}", show_alert=True)
    await garden_menu(callback)


# === LOTTERY ===

@router.callback_query(F.data == "work_lottery")
async def lottery_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎟️ Купить билет (50 🪙)", callback_data="lottery_buy")
    builder.button(text="⬅️ Назад", callback_data="work_back")
    builder.adjust(1)

    text = (
        "🎲 Лотерея\n\n"
        "🎟️ Билет: 50 монет\n\n"
        "💔 1-50: ничего\n"
        "🎉 51-80: x2 (100🪙)\n"
        "🎊 81-95: x5 (250🪙)\n"
        "🎆 96-99: x10 (500🪙)\n"
        "🏆 100: x50 (2500🪙)"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "lottery_buy")
async def lottery_buy(callback: types.CallbackQuery):
    session = await get_db_session()
    try:
        user = await get_user(session, callback.from_user.id)
        if not user or user.balance < 50:
            await callback.answer("❌ Недостаточно монет! Нужно 50", show_alert=True)
            return

        await add_balance(session, callback.from_user.id, -50)
        result = LotteryGame.play()
        if result["win"]:
            await add_balance(session, callback.from_user.id, result["prize"])
        await update_happiness(session, callback.from_user.id, 1)
        await session.commit()

        text = (
            f"🎲 Лотерея\n\n"
            f"Твой бросок: {result['roll']}\n"
            f"{result['emoji']} "
            f"{'Выигрыш: ' + str(result['prize']) + ' 🪙' if result['win'] else 'Ничего 💔'}\n"
            f"💰 Баланс: {user.balance - 50 + (result['prize'] if result['win'] else 0)}"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="🎟️ Ещё билет", callback_data="lottery_buy")
        builder.button(text="⬅️ Назад", callback_data="work_back")
        builder.adjust(1)
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer(f"{result['emoji']} {'+' + str(result['prize']) if result['win'] else '0'} монет")
    finally:
        await session.close()


# === DELIVERY ===

@router.callback_query(F.data == "work_delivery")
async def delivery_menu(callback: types.CallbackQuery):
    existing = check_delivery(callback.from_user.id)

    if isinstance(existing, dict) and existing.get("pending"):
        await callback.answer(f"⏳ Осталось {existing['remaining']}с", show_alert=True)
        return

    if isinstance(existing, dict) and existing.get("ready"):
        session = await get_db_session()
        try:
            user = await get_user(session, callback.from_user.id)
            if user:
                await add_balance(session, callback.from_user.id, existing["reward"])
                await update_happiness(session, callback.from_user.id, 1)
                await session.commit()
        finally:
            await session.close()
        await callback.answer(f"✅ Получено {existing['reward']} монет!", show_alert=True)

    builder = InlineKeyboardBuilder()
    builder.button(text="📬 Короткий (2мин, 50🪙)", callback_data="delivery_start_short")
    builder.button(text="📦 Средний (5мин, 120🪙)", callback_data="delivery_start_medium")
    builder.button(text="🚚 Дальний (15мин, 300🪙)", callback_data="delivery_start_long")
    builder.button(text="⬅️ Назад", callback_data="work_back")
    builder.adjust(1)

    await callback.message.edit_text(
        "📦 Курьерские миссии\nВыбери доставку:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delivery_start_"))
async def delivery_start(callback: types.CallbackQuery):
    d_type = callback.data.replace("delivery_start_", "")
    result = start_delivery(callback.from_user.id, d_type)

    if "error" in result:
        await callback.answer(result["error"], show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="⏳ Проверить", callback_data="work_delivery")
    builder.button(text="⬅️ Назад", callback_data="work_back")
    builder.adjust(1)

    await callback.message.edit_text(
        f"🚚 {result['delivery_type']} доставка началась!\n"
        f"⏳ Жди {result['wait_time']}с\n"
        f"💰 Награда: {result['reward']}🪙",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


# === MINING ===

@router.callback_query(F.data == "work_mining")
async def mining_menu(callback: types.CallbackQuery):
    session = await get_db_session()
    try:
        user = await get_user(session, callback.from_user.id)
        businesses = await get_user_businesses(session, callback.from_user.id)
        mine = next((b for b in businesses if b.business_type == "mine"), None)

        if not mine:
            mine = await create_business(session, callback.from_user.id, "mine", MINING_BASE_RATE)
            await session.commit()

        rate = get_mining_income(mine.level)
        upgrade_cost = get_mining_upgrade_cost(mine.level)

        now = datetime.now()
        last = mine.last_income or now
        elapsed = (now - last).total_seconds()
        accumulated = int(elapsed / 3600 * rate) if elapsed > 0 else 0

        builder = InlineKeyboardBuilder()
        builder.button(text=f"⛏️ Собрать ({accumulated}🪙)", callback_data="mining_collect")
        builder.button(text=f"⬆️ Улучшить (ур.{mine.level} → {mine.level + 1}, {upgrade_cost}🪙)", callback_data="mining_upgrade")
        builder.button(text="⬅️ Назад", callback_data="work_back")
        builder.adjust(1)

        await callback.message.edit_text(
            f"⛏️ Майнинг\n\n"
            f"Уровень: {mine.level}\n"
            f"Доход в час: {rate}🪙\n"
            f"Накоплено: {accumulated}🪙",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
    finally:
        await session.close()


@router.callback_query(F.data == "mining_collect")
async def mining_collect(callback: types.CallbackQuery):
    session = await get_db_session()
    try:
        businesses = await get_user_businesses(session, callback.from_user.id)
        mine = next((b for b in businesses if b.business_type == "mine"), None)
        if not mine:
            await callback.answer("❌ Шахта не найдена", show_alert=True)
            return

        now = datetime.now()
        last = mine.last_income or now
        elapsed = (now - last).total_seconds()
        rate = get_mining_income(mine.level)
        accumulated = int(elapsed / 3600 * rate)

        if accumulated <= 0:
            await callback.answer("⏳ Ещё не накоплено. Жди!", show_alert=True)
            return

        await add_balance(session, callback.from_user.id, accumulated)
        mine.last_income = now
        await session.commit()

        await callback.answer(f"✅ +{accumulated} монет собрано!", show_alert=True)
    finally:
        await session.close()
    await mining_menu(callback)


@router.callback_query(F.data == "mining_upgrade")
async def mining_upgrade(callback: types.CallbackQuery):
    session = await get_db_session()
    try:
        user = await get_user(session, callback.from_user.id)
        businesses = await get_user_businesses(session, callback.from_user.id)
        mine = next((b for b in businesses if b.business_type == "mine"), None)

        if not mine:
            await callback.answer("❌ Шахта не найдена", show_alert=True)
            return

        cost = get_mining_upgrade_cost(mine.level)
        if user.balance < cost:
            await callback.answer(f"❌ Нужно {cost} монет", show_alert=True)
            return

        await add_balance(session, callback.from_user.id, -cost)
        mine.level += 1
        mine.income_per_hour = get_mining_income(mine.level)
        await session.commit()
        await callback.answer(f"⬆️ Уровень {mine.level}! Доход: {mine.income_per_hour}🪙/ч", show_alert=True)
    finally:
        await session.close()
    await mining_menu(callback)


# === ALCHEMY ===

@router.callback_query(F.data == "work_alchemy")
async def alchemy_menu(callback: types.CallbackQuery):
    session = await get_db_session()
    try:
        inventory = await get_user_inventory(session, callback.from_user.id)
        builder = InlineKeyboardBuilder()

        for rarity in ["common", "uncommon", "rare"]:
            count = sum(1 for item in inventory if item["rarity"] == rarity)
            can_craft = count >= 2
            label = f"{'✅' if can_craft else '❌'} {rarity} ({count}) → {next_rarity(rarity)}"
            builder.button(text=label, callback_data=f"alchemy_{rarity}" if can_craft else "alchemy_none")

        builder.button(text="⬅️ Назад", callback_data="work_back")
        builder.adjust(1)

        await callback.message.edit_text(
            "⚗️ Алхимия\nСоздай 2 предмета одного ранга → предмет следующего ранга\n\n"
            "2 common → 1 uncommon\n"
            "2 uncommon → 1 rare\n"
            "2 rare → 1 legendary",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
    finally:
        await session.close()


def next_rarity(rarity: str) -> str:
    order = ["common", "uncommon", "rare", "legendary"]
    idx = order.index(rarity) + 1
    return order[idx] if idx < len(order) else "—"


@router.callback_query(F.data.startswith("alchemy_"))
async def alchemy_craft(callback: types.CallbackQuery):
    rarity = callback.data.split("_")[1]
    if rarity == "none":
        await callback.answer("❌ Недостаточно предметов", show_alert=True)
        return

    session = await get_db_session()
    try:
        inventory = await get_user_inventory(session, callback.from_user.id)
        same_rarity = [item for item in inventory if item["rarity"] == rarity]

        if len(same_rarity) < 2:
            await callback.answer("❌ Нужно 2 предмета", show_alert=True)
            return

        ids_to_consume = [same_rarity[0]["id"], same_rarity[1]["id"]]
        result = AlchemyGame.craft(inventory, rarity, ids_to_consume)
        if "error" in result:
            await callback.answer(result["error"], show_alert=True)
            return

        for item_id in ids_to_consume:
            await remove_inventory_item(session, item_id)
        await session.commit()

        await callback.answer(f"⚗️ Создан {result['result_rarity']} предмет!", show_alert=True)
    finally:
        await session.close()
    await alchemy_menu(callback)


# === NIGHT CLUB ===

@router.callback_query(F.data == "work_nightclub")
async def start_nightclub(callback: types.CallbackQuery):
    game = NightClubGame()
    _games[callback.from_user.id] = game
    await show_nightclub_round(callback.message, game)


async def show_nightclub_round(message: types.Message, game: NightClubGame):
    seq_text = " ".join(game.sequence)
    builder = InlineKeyboardBuilder()
    for d in ["⬆️", "⬇️", "⬅️", "➡️"]:
        builder.button(text=d, callback_data=f"club_{d}")
    builder.adjust(4)
    await message.edit_text(
        f"🎵 Ночной клуб | Раунд {game.round + 1}/{game.max_rounds}\n"
        f"💰 Очки: {game.score}\n\n"
        f"Повтори: {seq_text}\n"
        f"Прогресс: {len(game.player_input)}/{len(game.sequence)}",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("club_"))
async def nightclub_input(callback: types.CallbackQuery):
    direction = callback.data.split("_")[1]
    game = _games.get(callback.from_user.id)
    if not game or not isinstance(game, NightClubGame):
        await callback.answer("Игра не найдена", show_alert=True)
        return

    result = game.input_direction(direction)

    if result.get("game_over"):
        session = await get_db_session()
        try:
            user = await get_user(session, callback.from_user.id)
            if user:
                total = result.get("score", 0)
                await add_balance(session, callback.from_user.id, total)
                await update_happiness(session, callback.from_user.id, 1)
                await session.commit()
        finally:
            await session.close()

        bonus_text = f"\n🏆 Бонус: +{result['bonus']}!" if result.get("bonus") else ""
        await callback.message.edit_text(
            f"🎵 Ночной клуб завершён!\n"
            f"💰 Заработано: {result['score']} монет{bonus_text}\n"
            f"Раундов пройдено: {result.get('total_rounds', game.round)}/{game.max_rounds}",
            reply_markup=get_work_menu(),
        )
        _games.pop(callback.from_user.id, None)
        await callback.answer(f"✅ +{result['score']} монет!")
        return

    if result.get("correct"):
        if result.get("round_complete"):
            await callback.answer(f"✅ Раунд {result['round']} пройден!")
        else:
            await callback.answer("✅")
        await show_nightclub_round(callback.message, game)
    else:
        await callback.answer("❌ Неправильно!", show_alert=True)


# === PHOTO HUNT (stub for now) ===

@router.callback_query(F.data == "work_photo_hunt")
async def photo_hunt_stub(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📸 Фотоохота\n\n"
        "Эта функция будет доступна после подключения YOLO.\n"
        "Пока можно попробовать через команду /photo в боте.",
        reply_markup=get_work_menu(),
    )
    await callback.answer()
