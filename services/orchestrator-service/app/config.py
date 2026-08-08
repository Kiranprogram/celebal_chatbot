from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://chatbot:chatbot@localhost:5432/chatbot"
    jwt_secret: str = "change-me"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "openai/gpt-4o-mini"
    # Comma-separated: OPENROUTER_FALLBACK_MODELS=model-a,model-b
    openrouter_fallback_models: str = "openrouter/auto,google/gemma-4-31b-it:free"
    knowledge_service_url: str = "http://localhost:8003"
    memory_service_url: str = "http://localhost:8004"
    internal_service_key: str = "dev-internal-key"
    tavily_api_key: str = ""
    tool_http_timeout_seconds: int = 20
    log_level: str = "INFO"

    def fallback_models(self) -> list[str]:
        return [m.strip() for m in self.openrouter_fallback_models.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
