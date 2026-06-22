from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="💰 Баланс")
    builder.button(text="🏪 Магазин")
    builder.button(text="💼 Работа")
    builder.button(text="🎰 Казино")
    builder.button(text="📸 Фотоохота")
    builder.button(text="🎒 Инвентарь")
    builder.button(text="📊 Статистика")
    builder.button(text="🏠 Комната")
    builder.adjust(2, repeat=True)
    return builder.as_markup(resize_keyboard=True)


def get_work_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🐀 Охота на крысу", callback_data="work_rat_hunt")
    builder.button(text="🧹 Уборка", callback_data="work_cleaning")
    builder.button(text="🌱 Садоводство", callback_data="work_gardening")
    builder.button(text="🎲 Лотерея", callback_data="work_lottery")
    builder.button(text="⚗️ Алхимия", callback_data="work_alchemy")
    builder.button(text="📦 Курьер", callback_data="work_delivery")
    builder.button(text="⛏️ Майнинг", callback_data="work_mining")
    builder.button(text="🎵 Ночной клуб", callback_data="work_nightclub")
    builder.button(text="📸 Фотоохота", callback_data="work_photo_hunt")
    builder.button(text="⬅️ Назад", callback_data="work_back")
    builder.adjust(2, repeat=True)
    return builder.as_markup()


def get_casino_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="1️⃣ Прямая (x36)", callback_data="roulette_straight")
    builder.button(text="2️⃣ Сплит (x18)", callback_data="roulette_split")
    builder.button(text="3️⃣ Стрит (x12)", callback_data="roulette_street")
    builder.button(text="4️⃣ Корнер (x9)", callback_data="roulette_corner")
    builder.button(text="5️⃣ Сикслайн (x6)", callback_data="roulette_sixline")
    builder.button(text="6️⃣ Соседи (x7)", callback_data="roulette_neighbors")
    builder.button(text="🔴 Красное/Чёрное (x2)", callback_data="roulette_red_black")
    builder.button(text="2️⃣/3️⃣ Чёт/Нечет (x2)", callback_data="roulette_even_odd")
    builder.button(text="1-18 / 19-36 (x2)", callback_data="roulette_low_high")
    builder.button(text="5️⃣ Дюжина (x3)", callback_data="roulette_dozen")
    builder.button(text="6️⃣ Колонка (x3)", callback_data="roulette_column")
    builder.button(text="⬅️ Выйти", callback_data="roulette_back")
    builder.adjust(2, repeat=True)
    return builder.as_markup()


def get_bet_amount_keyboard(bet_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amount in [10, 50, 100, 500, 1000, 5000]:
        builder.button(
            text=f"{amount} 🪙",
            callback_data=f"bet_{bet_type}_{amount}",
        )
    builder.adjust(3, repeat=True)
    return builder.as_markup()


def get_roulette_value_keyboard(bet_type: str, amount: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if bet_type == "red_black":
        builder.button(text="🔴 Красное", callback_data=f"value_{bet_type}_red_{amount}")
        builder.button(text="⚫ Чёрное", callback_data=f"value_{bet_type}_black_{amount}")

    elif bet_type == "even_odd":
        builder.button(text="2️⃣ Чёт", callback_data=f"value_{bet_type}_even_{amount}")
        builder.button(text="3️⃣ Нечет", callback_data=f"value_{bet_type}_odd_{amount}")

    elif bet_type == "low_high":
        builder.button(text="1️⃣ 1-18", callback_data=f"value_{bet_type}_low_{amount}")
        builder.button(text="2️⃣ 19-36", callback_data=f"value_{bet_type}_high_{amount}")

    elif bet_type == "dozen":
        builder.button(text="1-12", callback_data=f"value_{bet_type}_1_{amount}")
        builder.button(text="13-24", callback_data=f"value_{bet_type}_2_{amount}")
        builder.button(text="25-36", callback_data=f"value_{bet_type}_3_{amount}")

    elif bet_type == "column":
        builder.button(text="1 кол.", callback_data=f"value_{bet_type}_1_{amount}")
        builder.button(text="2 кол.", callback_data=f"value_{bet_type}_2_{amount}")
        builder.button(text="3 кол.", callback_data=f"value_{bet_type}_3_{amount}")

    elif bet_type == "street":
        labels = ["1-3", "4-6", "7-9", "10-12", "13-15", "16-18", "19-21", "22-24", "25-27", "28-30", "31-33", "34-36"]
        for i, start in enumerate([1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]):
            builder.button(text=labels[i], callback_data=f"value_{bet_type}_{start}_{amount}")
        builder.adjust(3, repeat=True)

    elif bet_type == "sixline":
        labels = ["1-6", "7-12", "13-18", "19-24", "25-30", "31-36"]
        for label, start in zip(labels, [1, 7, 13, 19, 25, 31]):
            builder.button(text=label, callback_data=f"value_{bet_type}_{start}_{amount}")
        builder.adjust(3, repeat=True)

    elif bet_type == "split":
        builder.button(text="🔢 Введи 2 числа через запятую", callback_data="split_text_input")
        builder.adjust(1)

    elif bet_type == "corner":
        builder.button(text="🔢 Введи 4 числа через запятую", callback_data="corner_text_input")
        builder.adjust(1)

    elif bet_type == "neighbors":
        builder.button(text="🔢 Введи центр (0-36)", callback_data="neighbors_text_input")
        builder.adjust(1)

    builder.button(text="⬅️ Назад", callback_data="roulette_back")
    if bet_type not in ("split", "corner", "neighbors"):
        builder.adjust(2, repeat=True)
    return builder.as_markup()


def get_shop_menu(has_box: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Товары", callback_data="shop_items")
    if has_box:
        builder.button(text="🎁 Чёрный ящик (500🪙)", callback_data="shop_mystery_box")
    builder.button(text="⬅️ Закрыть", callback_data="shop_close")
    builder.adjust(1)
    return builder.as_markup()
