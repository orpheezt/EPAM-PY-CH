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

    PROVIDER: Provider = Provider.LITSERVE

    LITSERVE_URL: str = "http://localhost:8001/predict"

    MODAL_WEB_ENDPOINT_URL: str = ""

    HF_API_URL: str = "https://api-inference.huggingface.co/models/pysentimiento/robertuito-sentiment-analysis"
    HF_TOKEN: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_provider() -> Provider:
    settings = get_settings()
    return settings.PROVIDER
