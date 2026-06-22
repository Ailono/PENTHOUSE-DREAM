import random
import time
import math

RAT_HUNT_ROUNDS = 10
RAT_HUNT_COINS_PER_HIT = 10

LOTTERY_COST = 50
LOTTERY_TABLE = [
    (1, 50, 0, "💔"),
    (51, 80, 2, "🎉"),
    (81, 95, 5, "🎊"),
    (96, 99, 10, "🎆"),
    (100, 100, 50, "🏆"),
]

DELIVERY_OPTIONS = {
    "short": {"name": "Короткий", "time": 120, "reward": 50, "emoji": "📬"},
    "medium": {"name": "Средний", "time": 300, "reward": 120, "emoji": "📦"},
    "long": {"name": "Дальний", "time": 900, "reward": 300, "emoji": "🚚"},
}

MINING_BASE_RATE = 50
MINING_PER_LEVEL = 30
MINING_UPGRADE_COST_BASE = 500

ALCHEMY_RARITY_ORDER = ["common", "uncommon", "rare", "legendary"]

GARDEN_WATER_DECAY = 5
GARDEN_GROWTH_WATER = 10
GARDEN_GROWTH_FERTILIZE = 25
GARDEN_HARVEST_THRESHOLD = 100


class RatHuntGame:
    def __init__(self):
        self.round = 0
        self.hits = 0
        self.misses = 0
        self.rat_pos = random.randint(0, 8)
        self.active = True

    def guess(self, pos: int) -> dict:
        if not self.active:
            return {"error": "Game over"}

        self.round += 1
        hit = pos == self.rat_pos

        if hit:
            self.hits += 1
            coins = RAT_HUNT_COINS_PER_HIT + self.hits * 2
        else:
            self.misses += 1
            coins = 0

        self.rat_pos = random.randint(0, 8)
        game_over = self.round >= RAT_HUNT_ROUNDS

        if game_over:
            self.active = False
            total = self.hits * RAT_HUNT_COINS_PER_HIT + self.hits * (self.hits + 1)
            bonus = self.hits * 5 if self.misses == 0 else 0
            return {
                "hit": hit,
                "coins": coins,
                "total": total + bonus,
                "bonus": bonus,
                "round": self.round,
                "hits": self.hits,
                "misses": self.misses,
                "game_over": True,
                "rat_pos": self.rat_pos,
            }

        return {
            "hit": hit,
            "coins": coins,
            "round": self.round,
            "hits": self.hits,
            "misses": self.misses,
            "game_over": False,
            "rat_pos": self.rat_pos,
        }


class CleaningGame:
    def __init__(self):
        self.spots = []
        for i in range(6):
            self.spots.append({
                "id": i,
                "tough": random.random() < 0.3,
                "hits_needed": 2 if random.random() < 0.3 else 1,
                "hits_done": 0,
                "cleaned": False,
            })
        self.start_time = time.time()
        self.time_limit = 30
        self.active = True

    def clean(self, spot_id: int) -> dict:
        if not self.active:
            return {"error": "Game over"}
        if time.time() - self.start_time > self.time_limit:
            self.active = False
            return {"error": "Time up"}

        spot = next((s for s in self.spots if s["id"] == spot_id), None)
        if not spot or spot["cleaned"]:
            return {"error": "Already cleaned"}

        spot["hits_done"] += 1
        if spot["hits_done"] >= spot["hits_needed"]:
            spot["cleaned"] = True

        all_cleaned = all(s["cleaned"] for s in self.spots)
        time_left = max(0, self.time_limit - (time.time() - self.start_time))

        if all_cleaned:
            self.active = False
            bonus = 50 if time_left > 15 else 20
            return {
                "cleaned": True,
                "all_cleaned": True,
                "bonus": bonus,
                "total": 100 + bonus,
                "time_left": int(time_left),
            }

        return {
            "cleaned": spot["cleaned"],
            "all_cleaned": False,
            "hits_done": spot["hits_done"],
            "hits_needed": spot["hits_needed"],
            "time_left": int(time_left),
        }

    def get_board_state(self) -> list:
        return [
            {
                "id": s["id"],
                "cleaned": s["cleaned"],
                "tough": s["tough"],
                "progress": f"{s['hits_done']}/{s['hits_needed']}",
            }
            for s in self.spots
        ]


class GardenState:
    def __init__(self):
        self.water = 50
        self.health = 100
        self.growth = 0
        self.last_update = time.time()
        self.plant_type = "common"
        self.alive = True

    def update(self):
        elapsed = (time.time() - self.last_update) / 3600
        if elapsed < 0.01:
            return
        self.water = max(0, self.water - GARDEN_WATER_DECAY * elapsed)
        if self.water <= 0:
            self.health = max(0, self.health - 10 * elapsed)
        if self.health <= 0:
            self.alive = False
        self.last_update = time.time()

    def water_plant(self):
        self.update()
        self.water = min(100, self.water + 20)
        self.growth = min(GARDEN_HARVEST_THRESHOLD, self.growth + GARDEN_GROWTH_WATER)
        return {"water": int(self.water), "growth": int(self.growth)}

    def fertilize(self):
        self.update()
        self.growth = min(GARDEN_HARVEST_THRESHOLD, self.growth + GARDEN_GROWTH_FERTILIZE)
        return {"growth": int(self.growth)}

    def harvest(self) -> dict:
        self.update()
        if self.growth >= GARDEN_HARVEST_THRESHOLD:
            tier_mult = {"common": 1, "uncommon": 3, "rare": 8, "legendary": 25}
            reward = 100 * tier_mult.get(self.plant_type, 1)
            next_tier_idx = ALCHEMY_RARITY_ORDER.index(self.plant_type) + 1
            self.growth = 0
            self.water = 50
            if next_tier_idx < len(ALCHEMY_RARITY_ORDER):
                self.plant_type = ALCHEMY_RARITY_ORDER[next_tier_idx]
            return {
                "harvested": True,
                "reward": reward,
                "plant_type": self.plant_type,
            }
        return {"harvested": False, "growth": int(self.growth), "needed": GARDEN_HARVEST_THRESHOLD}

    def status(self) -> dict:
        self.update()
        growth_pct = int(self.growth / GARDEN_HARVEST_THRESHOLD * 100)
        return {
            "water": int(self.water),
            "health": int(self.health),
            "growth_pct": growth_pct,
            "plant_type": self.plant_type,
            "alive": self.alive,
        }


_gardens: dict[int, GardenState] = {}


def get_garden(user_id: int) -> GardenState:
    if user_id not in _gardens:
        _gardens[user_id] = GardenState()
    return _gardens[user_id]


class LotteryGame:
    @staticmethod
    def play() -> dict:
        roll = random.randint(1, 100)
        for low, high, mult, emoji in LOTTERY_TABLE:
            if low <= roll <= high:
                prize = LOTTERY_COST * mult
                return {
                    "roll": roll,
                    "multiplier": mult,
                    "prize": prize,
                    "emoji": emoji,
                    "win": mult > 0,
                }
        return {"roll": roll, "multiplier": 0, "prize": 0, "emoji": "💔", "win": False}


class AlchemyGame:
    @staticmethod
    def can_craft(inventory: list, rarity: str) -> bool:
        count = sum(1 for item in inventory if item.get("rarity") == rarity)
        return count >= 2

    @staticmethod
    def craft(inventory: list, rarity: str, item_ids: list[int]) -> dict:
        rarity_idx = ALCHEMY_RARITY_ORDER.index(rarity)
        if rarity_idx >= len(ALCHEMY_RARITY_ORDER) - 1:
            return {"error": "Cannot upgrade legendary further"}

        next_rarity = ALCHEMY_RARITY_ORDER[rarity_idx + 1]
        items_to_use = [item for item in inventory if item["id"] in item_ids and item.get("rarity") == rarity]

        if len(items_to_use) < 2:
            return {"error": "Need 2 items of same rarity"}

        return {
            "success": True,
            "consumed": [item["name"] for item in items_to_use[:2]],
            "result_rarity": next_rarity,
        }


_deliveries: dict[int, dict] = {}


def start_delivery(user_id: int, delivery_type: str) -> dict:
    option = DELIVERY_OPTIONS.get(delivery_type)
    if not option:
        return {"error": "Invalid delivery type"}
    if user_id in _deliveries:
        remaining = _deliveries[user_id]["end_time"] - time.time()
        if remaining > 0:
            return {"error": f"Active mission. Wait {int(remaining)}s"}

    _deliveries[user_id] = {
        "type": delivery_type,
        "start_time": time.time(),
        "end_time": time.time() + option["time"],
        "reward": option["reward"],
        "collected": False,
    }
    return {
        "started": True,
        "delivery_type": delivery_type,
        "wait_time": option["time"],
        "reward": option["reward"],
    }


def check_delivery(user_id: int) -> dict:
    delivery = _deliveries.get(user_id)
    if not delivery:
        return {"error": "No active delivery"}

    remaining = delivery["end_time"] - time.time()
    if remaining > 0:
        return {"pending": True, "remaining": int(remaining)}

    if delivery["collected"]:
        return {"error": "Already collected"}

    _deliveries[user_id]["collected"] = True
    return {
        "ready": True,
        "reward": delivery["reward"],
    }


def get_mining_income(mine_level: int) -> int:
    return MINING_BASE_RATE + MINING_PER_LEVEL * (mine_level - 1)


def get_mining_upgrade_cost(mine_level: int) -> int:
    return MINING_UPGRADE_COST_BASE * mine_level


class NightClubGame:
    def __init__(self):
        self.directions = ["⬆️", "⬇️", "⬅️", "➡️"]
        self.sequence = []
        self.player_input = []
        self.round = 0
        self.max_rounds = 5
        self.score = 0
        self.active = True
        self.generate_round()

    def generate_round(self):
        length = 3 + self.round
        self.sequence = [random.choice(self.directions) for _ in range(length)]
        self.player_input = []

    def input_direction(self, direction: str) -> dict:
        if not self.active:
            return {"error": "Game over"}

        self.player_input.append(direction)
        idx = len(self.player_input) - 1

        if self.player_input[idx] != self.sequence[idx]:
            self.active = False
            return {
                "correct": False,
                "game_over": True,
                "score": self.score,
                "sequence": self.sequence,
            }

        if len(self.player_input) == len(self.sequence):
            self.score += len(self.sequence) * 10
            self.round += 1

            if self.round >= self.max_rounds:
                self.active = False
                bonus = 100 if self.round == self.max_rounds else 0
                return {
                    "correct": True,
                    "round_complete": True,
                    "game_over": True,
                    "score": self.score + bonus,
                    "bonus": bonus,
                    "total_rounds": self.round,
                }

            self.generate_round()
            return {
                "correct": True,
                "round_complete": True,
                "game_over": False,
                "score": self.score,
                "round": self.round,
                "next_sequence": self.sequence,
            }

        return {
            "correct": True,
            "round_complete": False,
            "game_over": False,
            "progress": f"{len(self.player_input)}/{len(self.sequence)}",
        }
