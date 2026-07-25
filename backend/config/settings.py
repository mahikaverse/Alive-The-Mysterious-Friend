"""Application settings.

Loads and validates configuration from environment variables
using Pydantic Settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-level configuration loaded from environment variables."""

    app_name: str = "Alive"
    debug: bool = False
    log_level: str = "INFO"

    openai_api_key: str = ""
    gemini_api_key: str = ""

    database_url: str = ""

    max_tokens: int = 300
    temperature: float = 0.7

    model_name: str = "alive-v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
