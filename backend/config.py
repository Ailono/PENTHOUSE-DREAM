from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    db_type: str = "sqlite"
    db_user: str = "postgres"
    db_pass: str = "postgres"
    db_host: str = "localhost"
    db_port: str = "5432"
    db_name: str = "penthouse_dream"
    database_url: str = ""

    bot_token: str = ""

    redis_host: str = "localhost"
    redis_port: int = 6379

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_type == "sqlite":
            return "sqlite+aiosqlite:///./penthouse_dream.db"
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
