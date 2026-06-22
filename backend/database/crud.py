from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import date
from database.models import (
    User, InventoryItem, ShopItem, RouletteStats,
    Achievement, Business, PhotoHunt,
)


# --- User ---

async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_id: int, username: str = None) -> User:
    user = User(user_id=user_id, username=username)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def add_balance(db: AsyncSession, user_id: int, amount: int) -> User:
    user = await get_user(db, user_id)
    if not user:
        raise ValueError("User not found")
    user.balance += amount
    await db.flush()
    await db.refresh(user)
    return user


async def update_room_level(db: AsyncSession, user_id: int, level: int) -> User:
    user = await get_user(db, user_id)
    if not user:
        raise ValueError("User not found")
    user.room_level = level
    await db.flush()
    await db.refresh(user)
    return user


async def update_happiness(db: AsyncSession, user_id: int, delta: int) -> User:
    user = await get_user(db, user_id)
    if not user:
        raise ValueError("User not found")
    user.happiness = max(0, min(100, user.happiness + delta))
    await db.flush()
    await db.refresh(user)
    return user


# --- Inventory ---

async def get_user_inventory(db: AsyncSession, user_id: int) -> list[dict]:
    result = await db.execute(
        select(InventoryItem, ShopItem.name, ShopItem.rarity, ShopItem.image_url)
        .join(ShopItem, InventoryItem.item_id == ShopItem.id)
        .where(InventoryItem.user_id == user_id)
    )
    rows = result.all()
    return [
        {
            "id": row.InventoryItem.id,
            "item_id": row.InventoryItem.item_id,
            "name": row.name,
            "rarity": row.rarity,
            "image_url": row.image_url,
            "equipped": row.InventoryItem.is_equipped,
            "purchased_at": row.InventoryItem.purchased_at.isoformat() if row.InventoryItem.purchased_at else None,
        }
        for row in rows
    ]


async def equip_item(db: AsyncSession, user_id: int, inventory_id: int) -> bool:
    item = await db.execute(
        select(InventoryItem).where(
            InventoryItem.id == inventory_id,
            InventoryItem.user_id == user_id,
        )
    )
    item = item.scalar_one_or_none()
    if not item:
        return False
    await db.execute(
        update(InventoryItem)
        .where(InventoryItem.user_id == user_id)
        .values(is_equipped=False)
    )
    item.is_equipped = True
    await db.flush()
    return True


# --- Shop ---

async def get_todays_shop(db: AsyncSession) -> list[ShopItem]:
    result = await db.execute(
        select(ShopItem).where(ShopItem.shop_date == date.today())
    )
    return result.scalars().all()


async def purchase_item(db: AsyncSession, user_id: int, item_id: int) -> dict:
    shop_item = await db.execute(select(ShopItem).where(ShopItem.id == item_id))
    shop_item = shop_item.scalar_one_or_none()
    if not shop_item:
        return {"error": "Item not found"}

    user = await get_user(db, user_id)
    if not user:
        return {"error": "User not found"}

    if user.balance < shop_item.price:
        return {"error": "Insufficient balance"}

    if shop_item.stock <= 0:
        return {"error": "Out of stock"}

    user.balance -= shop_item.price
    shop_item.stock -= 1

    inv_item = InventoryItem(user_id=user_id, item_id=item_id)
    db.add(inv_item)

    await db.flush()
    return {
        "success": True,
        "item_name": shop_item.name,
        "balance": user.balance,
    }


async def remove_inventory_item(db: AsyncSession, item_id: int) -> bool:
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        return False
    await db.delete(item)
    await db.flush()
    return True


# --- Roulette Stats ---

async def get_roulette_stats(db: AsyncSession, user_id: int) -> RouletteStats | None:
    result = await db.execute(
        select(RouletteStats).where(RouletteStats.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_roulette_stats(
    db: AsyncSession, user_id: int,
    games_played: int = 0, games_won: int = 0,
    biggest_win: int = 0, favorite_number: int = 0,
):
    stats = await get_roulette_stats(db, user_id)
    if not stats:
        stats = RouletteStats(user_id=user_id)
        db.add(stats)
    stats.games_played += games_played
    stats.games_won += games_won
    if biggest_win > stats.biggest_win:
        stats.biggest_win = biggest_win
    if favorite_number != 0:
        stats.favorite_number = favorite_number
    await db.flush()


# --- Achievements ---

async def unlock_achievement(
    db: AsyncSession, user_id: int, achievement_name: str
) -> Achievement:
    achievement = Achievement(user_id=user_id, achievement_name=achievement_name)
    db.add(achievement)
    await db.flush()
    await db.refresh(achievement)
    return achievement


async def get_user_achievements(db: AsyncSession, user_id: int) -> list[Achievement]:
    result = await db.execute(
        select(Achievement)
        .where(Achievement.user_id == user_id)
        .order_by(Achievement.unlocked_at)
    )
    return result.scalars().all()


# --- Businesses ---

async def create_business(
    db: AsyncSession, user_id: int, business_type: str,
    income_per_hour: int,
) -> Business:
    business = Business(
        user_id=user_id, business_type=business_type,
        income_per_hour=income_per_hour,
    )
    db.add(business)
    await db.flush()
    await db.refresh(business)
    return business


async def get_user_businesses(db: AsyncSession, user_id: int) -> list[Business]:
    result = await db.execute(
        select(Business).where(Business.user_id == user_id)
    )
    return result.scalars().all()


async def collect_business_income(db: AsyncSession, business_id: int) -> int:
    result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = result.scalar_one_or_none()
    if not business:
        return 0
    income = business.income_per_hour
    business.last_income = date.today()
    await db.flush()
    return income


# --- Photo Hunts ---

async def create_photo_hunt(
    db: AsyncSession, user_id: int, target_item: str, reward: int
) -> PhotoHunt:
    hunt = PhotoHunt(
        user_id=user_id, target_item=target_item,
        status="pending", reward=reward,
    )
    db.add(hunt)
    await db.flush()
    await db.refresh(hunt)
    return hunt


async def complete_photo_hunt(
    db: AsyncSession, hunt_id: int, success: bool
) -> PhotoHunt | None:
    result = await db.execute(
        select(PhotoHunt).where(PhotoHunt.id == hunt_id)
    )
    hunt = result.scalar_one_or_none()
    if not hunt:
        return None
    hunt.status = "success" if success else "failed"
    await db.flush()
    await db.refresh(hunt)
    return hunt


async def get_pending_hunts(db: AsyncSession, user_id: int) -> list[PhotoHunt]:
    result = await db.execute(
        select(PhotoHunt)
        .where(PhotoHunt.user_id == user_id, PhotoHunt.status == "pending")
    )
    return result.scalars().all()
