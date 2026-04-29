from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Runtime configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    OPENAI_API_KEY: str | None = None
    SLACK_WEBHOOK_URL: str | None = None
    DELIVERY_MODE: Literal["console", "webhook"] = "console"
    ERROR_RATE_THRESHOLD: float = 0.05
    TOP_N_MODULES: int = 3
    LLM_MODEL: str = "gpt-5.4-nano-2026-03-17"
    LLM_TIMEOUT_SECONDS: float = 10.0
    WEBHOOK_TIMEOUT_SECONDS: float = 5.0
    DATA_DIR: Path = Path("data")
