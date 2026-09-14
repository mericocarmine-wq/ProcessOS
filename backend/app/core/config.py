from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration loaded from PROCESSOS_* variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PROCESSOS_",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "ProcessOS API"
    environment: Literal["development", "test", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str = Field(
        default="postgresql+asyncpg://processos:processos@localhost:5432/processos",
        repr=False,
    )
    cors_origins: list[AnyHttpUrl] = Field(default_factory=lambda: [AnyHttpUrl("http://localhost:3000")])


@lru_cache
def get_settings() -> Settings:
    return Settings()

