from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret: str = "change-me"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "openai/gpt-4o-mini"
    openrouter_embedding_model: str = "openai/text-embedding-3-small"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme123"
    vector_backend: str = "faiss"
    faiss_index_dir: str = "./data/faiss"
    chroma_persist_dir: str = "./data/chroma"
    rag_top_k: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 120
    internal_service_key: str = "dev-internal-key"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
