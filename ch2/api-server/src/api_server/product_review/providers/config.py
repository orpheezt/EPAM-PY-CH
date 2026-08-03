from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class HFSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    HF_TOKEN: str | None = None
    HF_SENTIMENT_API_URL: str = "https://router.huggingface.co/hf-inference/models/finiteautomata/beto-sentiment-analysis"
    HF_SUMMARIZER_API_URL: str = (
        "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
    )


@lru_cache
def get_hf_settings() -> HFSettings:
    return HFSettings()
