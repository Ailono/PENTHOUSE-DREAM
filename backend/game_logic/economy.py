BUSINESS_INCOME = {
    "mine": {"base": 60, "per_level": 40},
    "farm": {"base": 40, "per_level": 25},
    "nightclub": {"base": 100, "per_level": 60},
    "delivery": {"base": 50, "per_level": 30},
}

WORK_REWARDS = {
    "rat_hunt": (15, 60),
    "cleaning": (25, 100),
    "gardening": (40, 120),
    "lottery": (0, 300),
    "alchemy": (60, 200),
    "delivery": (50, 150),
    "mining": (80, 250),
    "nightclub": (90, 300),
    "photo_hunt": (150, 600),
}

ROOM_LEVEL_COSTS = [
    0,
    500,
    1200,
    2500,
    5000,
    10000,
    20000,
    40000,
    80000,
    150000,
    300000,
    500000,
    750000,
    1000000,
    1500000,
    2000000,
]

ROOM_LEVEL_REWARDS = {
    5: 1000,
    10: 5000,
    15: 20000,
}

STARTING_BALANCE = 1000
ROULETTE_MIN_BET = 10
ROULETTE_MAX_BET = 100000
SHOP_MIN_ITEMS = 8
SHOP_MAX_ITEMS = 15
MYSTERY_BOX_COST = 500


def calculate_business_income(business_type: str, level: int) -> int:
    config = BUSINESS_INCOME.get(business_type)
    if not config:
        return 0
    return config["base"] + config["per_level"] * (level - 1)


def calculate_work_reward(work_type: str, happiness: int = 50) -> int:
    import random
    reward_range = WORK_REWARDS.get(work_type)
    if not reward_range:
        return 10
    base = random.randint(reward_range[0], reward_range[1])
    happiness_mult = 1.0 + (happiness - 50) / 200
    return max(1, int(base * happiness_mult))


def room_level_up_cost(current_level: int) -> int:
    if current_level < len(ROOM_LEVEL_COSTS):
        return ROOM_LEVEL_COSTS[current_level]
    return ROOM_LEVEL_COSTS[-1] * (current_level - len(ROOM_LEVEL_COSTS) + 2)


def room_max_level() -> int:
    return len(ROOM_LEVEL_COSTS) - 1
