from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
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
    jwt_secret: SecretStr = Field(
        default_factory=lambda: SecretStr("development-only-secret-change-before-use"),
        min_length=32,
        repr=False,
    )
    jwt_issuer: str = "processos-api"
    jwt_audience: str = "processos-app"
    access_token_minutes: int = Field(default=30, ge=5, le=120)
    cors_origins: list[AnyHttpUrl] = Field(default_factory=lambda: [AnyHttpUrl("http://localhost:3000")])

    @model_validator(mode="after")
    def reject_development_secret_in_production(self) -> "Settings":
        if (
            self.environment == "production"
            and self.jwt_secret.get_secret_value() == "development-only-secret-change-before-use"
        ):
            raise ValueError("PROCESSOS_JWT_SECRET must be set in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
