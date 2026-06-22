import random
from datetime import date

RARITY_WEIGHTS = {
    "common": 50,
    "uncommon": 30,
    "rare": 15,
    "legendary": 5,
}

RARITY_PRICE_MULT = {
    "common": 1,
    "uncommon": 3,
    "rare": 8,
    "legendary": 25,
}

MYSTERY_BOX_COST = 500
MYSTERY_BOX_RARITY = {
    "common": 40,
    "uncommon": 35,
    "rare": 20,
    "legendary": 5,
}

HOT_DISCOUNT = 0.7

ITEM_TEMPLATES = [
    {"name": "Стул", "type": "chair"},
    {"name": "Стол", "type": "table"},
    {"name": "Лампа", "type": "lamp"},
    {"name": "Ковёр", "type": "carpet"},
    {"name": "Картина", "type": "painting"},
    {"name": "Аквариум", "type": "aquarium"},
    {"name": "Камин", "type": "fireplace"},
    {"name": "Диван", "type": "sofa"},
    {"name": "Книжный шкаф", "type": "bookshelf"},
    {"name": "Растение", "type": "plant"},
    {"name": "Торшер", "type": "floor_lamp"},
    {"name": "Журнальный столик", "type": "coffee_table"},
    {"name": "Зеркало", "type": "mirror"},
    {"name": "Часы", "type": "clock"},
    {"name": "Фонтан", "type": "fountain"},
]

_last_generation_date: date | None = None


def roll_rarity(weights: dict[str, int] = None) -> str:
    if weights is None:
        weights = RARITY_WEIGHTS
    total = sum(weights.values())
    roll = random.randint(1, total)
    cumulative = 0
    for rarity, weight in weights.items():
        cumulative += weight
        if roll <= cumulative:
            return rarity
    return "common"


def generate_shop_items(count: int = 12) -> list[dict]:
    used_types = set()
    items = []

    for _ in range(count):
        template = random.choice(ITEM_TEMPLATES)
        while template["type"] in used_types:
            template = random.choice(ITEM_TEMPLATES)
        used_types.add(template["type"])

        rarity = roll_rarity()
        base_price = 100
        price = base_price * RARITY_PRICE_MULT[rarity]

        is_hot = random.random() < 0.1
        stock = random.randint(1, 5)

        if is_hot:
            price = int(price * HOT_DISCOUNT)
            stock = random.randint(1, 2)

        if rarity == "legendary":
            stock = 1
        elif rarity == "rare":
            stock = random.randint(1, 3)

        items.append({
            "name": template["name"],
            "type": template["type"],
            "rarity": rarity,
            "price": price,
            "stock": stock,
            "is_hot": is_hot,
            "shop_date": date.today(),
        })

    return items


def open_mystery_box() -> dict:
    rarity = roll_rarity(MYSTERY_BOX_RARITY)
    template = random.choice(ITEM_TEMPLATES)
    base_price = 100
    price_value = base_price * RARITY_PRICE_MULT[rarity]

    return {
        "name": template["name"],
        "type": template["type"],
        "rarity": rarity,
        "value": price_value,
    }


def need_regeneration() -> bool:
    global _last_generation_date
    today = date.today()
    if _last_generation_date != today:
        _last_generation_date = today
        return True
    return False
