from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Base
from database.database import engine, get_db
from database import crud
from game_logic import roulette as roulette_logic
import time
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Penthouse Dream API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_LIMIT_DURATION = 60
RATE_LIMIT_MAX = 100
_request_times: dict[str, list[float]] = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    times = _request_times.get(client_ip, [])
    times = [t for t in times if now - t < RATE_LIMIT_DURATION]
    if len(times) >= RATE_LIMIT_MAX:
        return JSONResponse(
            status_code=429,
            content={"error": "Too many requests. Limit: 100/min"},
        )
    times.append(now)
    _request_times[client_ip] = times
    return await call_next(request)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
    logger.info("Engine disposed")


active_connections: dict[int, WebSocket] = {}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    active_connections[user_id] = websocket
    logger.info(f"User {user_id} connected via WebSocket")
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "roulette_result":
                logger.info(f"Roulette result from user {user_id}: {data}")
            elif msg_type == "room_update":
                logger.info(f"Room update from user {user_id}: {data}")
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        active_connections.pop(user_id, None)
        logger.error(f"WebSocket error for user {user_id}: {e}")


async def notify_user(user_id: int, event: dict):
    ws = active_connections.get(user_id)
    if ws:
        try:
            await ws.send_json(event)
        except Exception:
            active_connections.pop(user_id, None)


# --- API Endpoints ---

@app.get("/")
async def root():
    return {"message": "Penthouse Dream API is running"}


@app.get("/api/users/{user_id}")
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/users/")
async def create_new_user(user_id: int, username: str = None, db: AsyncSession = Depends(get_db)):
    existing = await crud.get_user(db, user_id)
    if existing:
        return existing
    user = await crud.create_user(db, user_id, username)
    return user


@app.get("/api/users/{user_id}/profile")
async def read_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    inventory_count = len(user.inventory) if user.inventory else 0
    achievements_count = len(user.achievements) if user.achievements else 0
    return {
        "user_id": user.user_id,
        "username": user.username,
        "balance": user.balance,
        "room_level": user.room_level,
        "happiness": user.happiness,
        "inventory_count": inventory_count,
        "achievements_count": achievements_count,
    }


@app.get("/api/users/{user_id}/inventory")
async def read_inventory(user_id: int, db: AsyncSession = Depends(get_db)):
    items = await crud.get_user_inventory(db, user_id)
    return items


@app.get("/api/users/{user_id}/stats")
async def read_stats(user_id: int, db: AsyncSession = Depends(get_db)):
    stats = await crud.get_roulette_stats(db, user_id)
    return stats or {"games_played": 0, "games_won": 0, "biggest_win": 0}


@app.post("/api/users/{user_id}/balance/add")
async def add_balance(user_id: int, amount: int, db: AsyncSession = Depends(get_db)):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    user = await crud.add_balance(db, user_id, amount)
    await notify_user(user_id, {"type": "balance_changed", "balance": user.balance})
    return {"balance": user.balance}


# --- Shop ---

@app.get("/api/shop")
async def get_shop(db: AsyncSession = Depends(get_db)):
    items = await crud.get_todays_shop(db)
    return items


@app.post("/api/shop/buy")
async def buy_item(user_id: int, item_id: int, db: AsyncSession = Depends(get_db)):
    result = await crud.purchase_item(db, user_id, item_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await notify_user(user_id, {
        "type": "balance_changed",
        "balance": result["balance"],
    })
    return result


# --- Roulette ---

@app.get("/api/roulette")
async def get_roulette_info():
    return {
        "numbers": roulette_logic.EUROPEAN_NUMBERS,
        "bets": roulette_logic.BET_TYPES,
    }


@app.post("/api/roulette/spin")
async def spin_roulette(user_id: int, bet_type: str, bet_amount: int, bet_value: str = None, db: AsyncSession = Depends(get_db)):
    if bet_amount <= 0:
        raise HTTPException(status_code=400, detail="Bet must be positive")

    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.balance < bet_amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    result = roulette_logic.spin(bet_type, bet_amount, bet_value)
    await crud.add_balance(db, user_id, result["payout"] - bet_amount)
    await crud.update_roulette_stats(
        db, user_id, 1,
        1 if result["win"] else 0,
        result["payout"] if result["win"] else 0,
        result["number"],
    )

    await notify_user(user_id, {
        "type": "roulette_result",
        "number": result["number"],
        "color": result["color"],
        "win": result["win"],
        "payout": result["payout"],
        "balance": user.balance + result["payout"] - bet_amount,
    })

    return result
