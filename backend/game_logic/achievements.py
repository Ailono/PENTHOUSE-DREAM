ACHIEVEMENTS = {
    "first_purchase": {
        "name": "Первая покупка",
        "description": "Купи первый предмет в магазине",
        "icon": "🛍️",
        "reward": 100,
    },
    "millionaire": {
        "name": "Миллионер",
        "description": "Накопи 1 000 000 монет",
        "icon": "💰",
        "reward": 50000,
    },
    "room_level_5": {
        "name": "Дизайнер интерьера",
        "description": "Достигни 5 уровня комнаты",
        "icon": "🏠",
        "reward": 1000,
    },
    "room_level_10": {
        "name": "Архитектор",
        "description": "Достигни 10 уровня комнаты",
        "icon": "🏛️",
        "reward": 5000,
    },
    "roulette_10": {
        "name": "Завсегдатай казино",
        "description": "Сыграй 10 игр в рулетку",
        "icon": "🎰",
        "reward": 500,
    },
    "roulette_win_big": {
        "name": "Крупный куш",
        "description": "Выиграй 10 000 монет за одну ставку",
        "icon": "💎",
        "reward": 2000,
    },
    "collector_10": {
        "name": "Коллекционер",
        "description": "Собери 10 предметов в инвентаре",
        "icon": "🎒",
        "reward": 500,
    },
    "collector_25": {
        "name": "Коллекционер-эксперт",
        "description": "Собери 25 предметов в инвентаре",
        "icon": "🏆",
        "reward": 2000,
    },
    "business_owner": {
        "name": "Предприниматель",
        "description": "Открой свой первый бизнес",
        "icon": "🏢",
        "reward": 1000,
    },
    "photo_hunter": {
        "name": "Фотоохотник",
        "description": "Выполни первое фото-задание",
        "icon": "📸",
        "reward": 300,
    },
    "happiness_100": {
        "name": "Счастливчик",
        "description": "Достигни 100% счастья",
        "icon": "😊",
        "reward": 1000,
    },
    "work_50": {
        "name": "Трудоголик",
        "description": "Выполни 50 работ",
        "icon": "💼",
        "reward": 1500,
    },
    "rat_hunt_master": {
        "name": "Крысолов",
        "description": "Поймай 50 крыс",
        "icon": "🐀",
        "reward": 800,
    },
}

ACHIEVEMENT_IDS = {k: i for i, k in enumerate(ACHIEVEMENTS)}


def check_achievements(user_data: dict, existing: set[str]) -> list[dict]:
    unlocked = []
    checks = {
        "first_purchase": user_data.get("inventory_count", 0) >= 1,
        "millionaire": user_data.get("balance", 0) >= 1_000_000,
        "room_level_5": user_data.get("room_level", 0) >= 5,
        "room_level_10": user_data.get("room_level", 0) >= 10,
        "roulette_10": user_data.get("games_played", 0) >= 10,
        "roulette_win_big": user_data.get("biggest_win", 0) >= 10_000,
        "collector_10": user_data.get("inventory_count", 0) >= 10,
        "collector_25": user_data.get("inventory_count", 0) >= 25,
        "business_owner": user_data.get("business_count", 0) >= 1,
        "photo_hunter": user_data.get("photo_hunts_done", 0) >= 1,
        "happiness_100": user_data.get("happiness", 0) >= 100,
        "work_50": user_data.get("works_done", 0) >= 50,
        "rat_hunt_master": user_data.get("rat_hunt_kills", 0) >= 50,
    }

    for key, condition in checks.items():
        if key not in existing and condition:
            info = ACHIEVEMENTS.get(key, {})
            unlocked.append({
                "key": key,
                "name": info.get("name", key),
                "icon": info.get("icon", "🏅"),
                "reward": info.get("reward", 0),
            })

    return unlocked
