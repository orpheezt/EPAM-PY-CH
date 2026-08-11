from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class SettingsSection(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = True
