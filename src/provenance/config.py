from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    semantic_scholar_api_key: str = ""
    database_url: str = "postgresql://provenance:provenance@localhost:5432/provenance"

    arxiv_max_results: int = 20
    semantic_scholar_max_results: int = 20
    http_timeout_seconds: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
