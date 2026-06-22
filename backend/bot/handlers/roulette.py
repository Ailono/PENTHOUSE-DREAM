from aiogram import Router, types, F
from database.crud import get_user, add_balance, update_roulette_stats
from database.database import get_db_session
from bot.keyboards import get_casino_menu, get_bet_amount_keyboard, get_roulette_value_keyboard, get_main_menu
from game_logic.roulette import spin, EUROPEAN_NUMBERS, TABLE_ROWS, STREET_STARTS, SIXLINE_STARTS
from game_logic.achievement_checker import check_and_unlock

router = Router()

_bet_states: dict[int, dict] = {}

BET_TYPE_NAMES = {
    "straight": "Прямая ставка (x36)",
    "split": "Сплит (x18)",
    "street": "Стрит (x12)",
    "corner": "Корнер (x9)",
    "sixline": "Сикслайн (x6)",
    "neighbors": "Соседи (x7)",
    "red_black": "Красное/Чёрное (x2)",
    "even_odd": "Чёт/Нечет (x2)",
    "low_high": "1-18 / 19-36 (x2)",
    "dozen": "Дюжина (x3)",
    "column": "Колонка (x3)",
}

TEXT_INPUT_TYPES = {"split", "corner", "neighbors"}


@router.message(lambda msg: msg.text == "🎰 Казино")
async def cmd_casino(message: types.Message):
    await message.answer(
        "🎰 Казино Penthouse Dream\n\n"
        "11 типов ставок — выбери свой стиль!",
        reply_markup=get_casino_menu(),
    )


@router.callback_query(F.data.startswith("roulette_"))
async def process_roulette_menu(callback: types.CallbackQuery):
    action = callback.data.replace("roulette_", "")

    if action == "back":
        await callback.message.delete()
        await callback.message.answer("Главное меню:", reply_markup=get_main_menu())
        await callback.answer()
        return

    _bet_states[callback.from_user.id] = {"bet_type": action}
    name = BET_TYPE_NAMES.get(action, action)
    description = _get_bet_description(action)

    await callback.message.edit_text(
        f"🎰 {name}\n{description}\nВыбери сумму ставки:",
        reply_markup=get_bet_amount_keyboard(action),
    )
    await callback.answer()


def _get_bet_description(bet_type: str) -> str:
    descs = {
        "straight": "Угадай точное число (0-36).",
        "split": "Угадай одно из двух чисел. Введи через запятую, например: 14,17",
        "street": "Угадай одно из трёх чисел в ряду.",
        "corner": "Угадай одно из четырёх чисел (квадрат). Введи через запятую: 1,2,4,5",
        "sixline": "Угадай одно из шести чисел (два ряда).",
        "neighbors": "Число + 2 соседа на колесе (всего 5 чисел). Введи центр: 17",
        "red_black": "Красное или чёрное.",
        "even_odd": "Чётное или нечётное.",
        "low_high": "1-18 (малое) или 19-36 (большое).",
        "dozen": "1-12, 13-24 или 25-36.",
        "column": "1 кол. (1,4,7…), 2 кол. (2,5,8…), 3 кол. (3,6,9…).",
    }
    return descs.get(bet_type, "")


@router.callback_query(F.data.startswith("bet_"))
async def process_bet_amount(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) < 3:
        return
    bet_type = parts[1]
    amount = int(parts[2])
    user_id = callback.from_user.id

    session = await get_db_session()
    try:
        user = await get_user(session, user_id)
        if not user or user.balance < amount:
            await callback.answer("❌ Недостаточно монет!", show_alert=True)
            return

        _bet_states[user_id] = {"bet_type": bet_type, "amount": amount}

        if bet_type in TEXT_INPUT_TYPES:
            hints = {
                "split": "Напиши два числа через запятую (например: 14,17)",
                "corner": "Напиши четыре числа через запятую (например: 1,2,4,5)",
                "neighbors": "Напиши центр (число от 0 до 36, например: 17)",
            }
            await callback.message.edit_text(
                f"🎰 {BET_TYPE_NAMES.get(bet_type, bet_type)}\n"
                f"Ставка: {amount} 🪙\n\n{hints.get(bet_type, 'Введи значение:')}",
                reply_markup=None,
            )
            await callback.answer()
        else:
            await callback.message.edit_text(
                f"🎰 {BET_TYPE_NAMES.get(bet_type, bet_type)}\n"
                f"Ставка: {amount} 🪙\nВыбери значение:",
                reply_markup=get_roulette_value_keyboard(bet_type, amount),
            )
            await callback.answer()
    finally:
        await session.close()


@router.callback_query(F.data.startswith("value_"))
async def process_roulette_value(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    if len(parts) < 4:
        return

    if parts[1] == "text":
        await callback.answer("Используй текстовый ввод!", show_alert=True)
        return

    bet_type = parts[1]
    value = parts[2]
    amount = int(parts[3])

    session = await get_db_session()
    try:
        result = spin(bet_type, amount, value)
        await _finish_bet(callback, session, result)
    finally:
        await session.close()


async def _finish_bet(callback: types.CallbackQuery, session, result: dict):
    user = await get_user(session, callback.from_user.id)

    ach_text = ""
    if user:
        net = result["payout"] - result["bet_amount"]
        await add_balance(session, callback.from_user.id, net)
        await update_roulette_stats(
            session, callback.from_user.id,
            1, 1 if result["win"] else 0,
            result["payout"] if result["win"] else 0,
            result["number"],
        )

        new_ach = await check_and_unlock(callback.from_user.id, session, {
            "games_played": 1,
            "biggest_win": result["payout"],
        })
        if new_ach:
            ach_text = "\n\n🏆 " + new_ach[0]["icon"] + " " + new_ach[0]["name"] + "! +" + str(new_ach[0]["reward"]) + "🪙"

        await session.commit()

    color_emoji = {"red": "🔴", "black": "⚫", "green": "🟢"}.get(result["color"], "⚪")
    text = (
        f"🎰 Результат: {result['number']} {color_emoji}\n\n"
        f"{'🎉 Ты выиграл!' if result['win'] else '😔 Проигрыш'}\n"
        f"{'💰 Выигрыш: +' + str(result['payout']) + ' 🪙' if result['win'] else ''}\n"
        f"💳 Баланс: {user.balance + result['payout'] - result['bet_amount'] if user else '?'} 🪙"
        f"{ach_text}"
    )
    await callback.message.edit_text(text, reply_markup=get_casino_menu())
    await callback.answer(
        f"{'🎉 +' + str(result['payout']) + ' монет!' if result['win'] else '😔 Повезёт в следующий раз'}",
        show_alert=True,
    )


@router.message(lambda msg: msg.text and msg.from_user.id in _bet_states)
async def process_text_bet(message: types.Message):
    state = _bet_states.get(message.from_user.id)
    if not state:
        return

    bet_type = state["bet_type"]
    if bet_type not in TEXT_INPUT_TYPES:
        if bet_type == "straight":
            pass
        else:
            return

    text = message.text.strip()
    amount = state["amount"]

    if bet_type == "straight":
        if not text.isdigit() or int(text) < 0 or int(text) > 36:
            await message.answer("❌ Введи число от 0 до 36")
            return
        value = text

    elif bet_type == "split":
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            await message.answer("❌ Введи два числа через запятую (например: 14,17)")
            return
        nums = [int(p) for p in parts]
        if any(n < 0 or n > 36 for n in nums):
            await message.answer("❌ Числа должны быть от 0 до 36")
            return
        value = f"{nums[0]},{nums[1]}"

    elif bet_type == "corner":
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 4 or not all(p.isdigit() for p in parts):
            await message.answer("❌ Введи 4 числа через запятую (например: 1,2,4,5)")
            return
        nums = [int(p) for p in parts]
        if any(n < 0 or n > 36 for n in nums):
            await message.answer("❌ Числа должны быть от 0 до 36")
            return
        value = f"{nums[0]},{nums[1]},{nums[2]},{nums[3]}"

    elif bet_type == "neighbors":
        if not text.isdigit() or int(text) < 0 or int(text) > 36:
            await message.answer("❌ Введи число от 0 до 36")
            return
        value = text

    else:
        return

    session = await get_db_session()
    try:
        result = spin(bet_type, amount, value)
        user = await get_user(session, message.from_user.id)

        ach_text = ""
        if user:
            net = result["payout"] - amount
            await add_balance(session, message.from_user.id, net)
            await update_roulette_stats(
                session, message.from_user.id,
                1, 1 if result["win"] else 0,
                result["payout"] if result["win"] else 0,
                result["number"],
            )

            new_ach = await check_and_unlock(message.from_user.id, session, {
                "games_played": 1,
                "biggest_win": result["payout"],
            })
            if new_ach:
                ach_text = "\n\n🏆 " + new_ach[0]["icon"] + " " + new_ach[0]["name"] + "! +" + str(new_ach[0]["reward"]) + "🪙"

            await session.commit()

        color_emoji = {"red": "🔴", "black": "⚫", "green": "🟢"}.get(result["color"], "⚪")
        text = (
            f"🎰 Результат: {result['number']} {color_emoji}\n\n"
            f"{'🎉 Ты выиграл!' if result['win'] else '😔 Проигрыш'}\n"
            f"{'💰 Выигрыш: +' + str(result['payout']) + ' 🪙' if result['win'] else ''}\n"
            f"💳 Баланс: {user.balance + result['payout'] - amount if user else '?'} 🪙"
            f"{ach_text}"
        )
        await message.answer(text, reply_markup=get_casino_menu())
    finally:
        await session.close()
