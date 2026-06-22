CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(100),
    balance BIGINT DEFAULT 1000,
    room_level INTEGER DEFAULT 1,
    happiness INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shop_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    rarity VARCHAR(20),
    price INTEGER,
    image_url VARCHAR(255),
    stock INTEGER DEFAULT 0,
    shop_date DATE DEFAULT CURRENT_DATE,
    is_hot BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    item_id INTEGER REFERENCES shop_items(id),
    purchased_at TIMESTAMP DEFAULT NOW(),
    is_equipped BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS roulette_stats (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
    games_played INTEGER DEFAULT 0,
    games_won INTEGER DEFAULT 0,
    biggest_win INTEGER DEFAULT 0,
    favorite_number INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    achievement_name VARCHAR(100),
    unlocked_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS businesses (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    business_type VARCHAR(50),
    level INTEGER DEFAULT 1,
    income_per_hour INTEGER,
    last_income TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS photo_hunts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    target_item VARCHAR(100),
    status VARCHAR(20),
    reward INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id);
CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_businesses_user ON businesses(user_id);
CREATE INDEX IF NOT EXISTS idx_shop_date ON shop_items(shop_date);
