from sqlalchemy.ext.asyncio import AsyncSession
from database.crud import (
    get_user, get_user_inventory, get_roulette_stats,
    get_user_achievements, get_user_businesses,
    unlock_achievement, add_balance,
    get_pending_hunts,
)
from game_logic.achievements import check_achievements, ACHIEVEMENTS


async def check_and_unlock(user_id: int, db: AsyncSession, event_data: dict = None) -> list[dict]:
    user = await get_user(db, user_id)
    if not user:
        return []

    inv = await get_user_inventory(db, user_id)
    stats = await get_roulette_stats(db, user_id)
    achievements = await get_user_achievements(db, user_id)
    businesses = await get_user_businesses(db, user_id)
    pending_hunts = await get_pending_hunts(db, user_id)

    existing = {a.achievement_name for a in achievements}

    user_data = {
        "balance": user.balance,
        "room_level": user.room_level,
        "happiness": user.happiness,
        "inventory_count": len(inv),
        "games_played": stats.games_played if stats else 0,
        "biggest_win": stats.biggest_win if stats else 0,
        "business_count": len(businesses),
        "photo_hunts_done": 0,
        "works_done": 0,
        "rat_hunt_kills": 0,
    }

    if event_data:
        user_data.update(event_data)

    new_achievements = check_achievements(user_data, existing)
    result = []

    for ach in new_achievements:
        await unlock_achievement(db, user_id, ach["key"])

        if ach["reward"] > 0:
            await add_balance(db, user_id, ach["reward"])

        result.append(ach)

    if result:
        await db.commit()

    return result
