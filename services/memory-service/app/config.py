from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://chatbot:chatbot@localhost:5432/chatbot"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "chatbot_memory"
    jwt_secret: str = "change-me"
    internal_service_key: str = "dev-internal-key"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
