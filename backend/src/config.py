from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    log_level: str = "INFO"
    metadata_db_path: str = ":memory:"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()
