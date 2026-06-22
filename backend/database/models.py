from sqlalchemy import Column, BigInteger, String, Integer, Boolean, Date, DateTime, ForeignKey, text, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(100), nullable=True)
    balance = Column(BigInteger, default=1000)
    room_level = Column(Integer, default=1)
    happiness = Column(Integer, default=50)
    created_at = Column(DateTime, server_default=func.now())

    inventory = relationship("InventoryItem", back_populates="user")
    roulette_stats = relationship("RouletteStats", back_populates="user", uselist=False)
    achievements = relationship("Achievement", back_populates="user")
    businesses = relationship("Business", back_populates="user")
    photo_hunts = relationship("PhotoHunt", back_populates="user")


class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    item_id = Column(Integer, ForeignKey("shop_items.id"))
    purchased_at = Column(DateTime, server_default=func.now())
    is_equipped = Column(Boolean, default=False)

    user = relationship("User", back_populates="inventory")
    item = relationship("ShopItem", back_populates="inventory")


class ShopItem(Base):
    __tablename__ = "shop_items"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    rarity = Column(String(20))
    price = Column(Integer)
    image_url = Column(String(255), nullable=True)
    stock = Column(Integer, default=0)
    shop_date = Column(Date, server_default=func.current_date())
    is_hot = Column(Boolean, default=False)

    inventory = relationship("InventoryItem", back_populates="item")


class RouletteStats(Base):
    __tablename__ = "roulette_stats"

    user_id = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    biggest_win = Column(Integer, default=0)
    favorite_number = Column(Integer, default=0)

    user = relationship("User", back_populates="roulette_stats")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    achievement_name = Column(String(100))
    unlocked_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="achievements")


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    business_type = Column(String(50))
    level = Column(Integer, default=1)
    income_per_hour = Column(Integer)
    last_income = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="businesses")


class PhotoHunt(Base):
    __tablename__ = "photo_hunts"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    target_item = Column(String(100))
    status = Column(String(20))
    reward = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="photo_hunts")
