from enum import StrEnum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Provider(StrEnum):
    LITSERVE = "litserve"
    MODAL = "modal"
    HF_API = "hf_api"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROVIDER: Provider = Provider.HF_API

    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600
    CACHE_MAX_SIZE: int = 1000

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_provider() -> Provider:
    settings = get_settings()
    return settings.PROVIDER
