"""Application settings.

Loads and validates configuration from environment variables
using Pydantic Settings. Supports development, staging,
and production profiles.
"""

import logging

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

REQUIRED_IN_PRODUCTION = [
    "openai_api_key",
    "database_url",
]


class Settings(BaseSettings):
    """Application-level configuration loaded from environment variables."""

    # --- environment ---
    environment: str = Field(default="development", description="Runtime environment: development, staging, or production")
    debug: bool = Field(default=False, description="Enable debug mode and hot-reload")
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")

    # --- server ---
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    shutdown_timeout: int = Field(default=30, ge=1, description="Graceful shutdown timeout in seconds")

    # --- api keys ---
    openai_api_key: str = Field(default="", description="OpenAI API key")
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    deepseek_api_key: str = Field(default="", description="DeepSeek API key")
    nvidia_api_key: str = Field(default="", description="NVIDIA NIM API key")
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    grok_api_key: str = Field(default="", description="xAI Grok API key")
    api_key: str = Field(default="", description="Optional API key for request authentication")

    # --- database ---
    database_url: str = Field(default="", description="PostgreSQL connection string")

    # --- llm provider (Person 2) ---
    llm_provider: str = Field(default="deepseek", description="Primary LLM backend: openai, gemini, deepseek, nvidia, openrouter, or grok")
    llm_fallback_order: str = Field(default="nvidia,openrouter,grok", description="Comma-separated fallback providers used after the primary is exhausted")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    gemini_model: str = Field(default="gemini-1.5-flash", description="Gemini model name")
    deepseek_model: str = Field(default="deepseek-chat", description="DeepSeek model name")
    nvidia_model: str = Field(default="meta/llama-3.3-70b-instruct", description="NVIDIA NIM model name")
    openrouter_model: str = Field(default="deepseek/deepseek-chat", description="OpenRouter model name")
    grok_model: str = Field(default="grok-2-latest", description="xAI Grok model name")

    # --- model defaults ---
    model_name: str = Field(default="alive-v1", description="Default model identifier")
    max_tokens: int = Field(default=300, ge=1, le=4096, description="Default max tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Default temperature")

    # --- cors ---
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")

    # --- trusted hosts ---
    trusted_hosts: list[str] = Field(default=["*"], description="Allowed Host header values")

    # --- memory & embeddings (Person 3) ---
    embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model name")
    embedding_dimensions: int = Field(default=1536, description="Embedding vector dimensions")
    chroma_path: str = Field(default="./chroma_db", description="ChromaDB persistent storage path")
    chroma_collection: str = Field(default="alive_memories", description="ChromaDB collection name")
    memory_top_k: int = Field(default=5, ge=1, le=50, description="Number of memories to retrieve per turn")
    memory_importance_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum importance score to store a memory")

    # --- usage limits & token saving (Person 2) ---
    max_conversations_per_day: int = Field(default=100, ge=1, description="Maximum conversations per day before all providers are paused")
    daily_token_budget: int = Field(default=0, ge=0, description="Maximum tokens per provider per day (0 = unlimited)")
    compact_conversation_enabled: bool = Field(default=True, description="Enable automatic conversation compaction to save tokens")
    conversation_token_threshold: int = Field(default=6000, ge=500, description="Estimated token count that triggers conversation compaction")
    conversation_keep_recent: int = Field(default=10, ge=2, description="Most recent messages kept verbatim during compaction")
    llm_cache_enabled: bool = Field(default=False, description="Cache identical LLM prompts to avoid repeat billing")
    llm_cache_max_entries: int = Field(default=256, ge=0, description="Maximum entries in the LLM response cache")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        normalized = v.lower().strip()
        if normalized not in {"development", "staging", "production"}:
            raise ValueError(f"Invalid environment '{v}'. Must be development, staging, or production.")
        return normalized

    @field_validator("debug")
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        env = info.data.get("environment", "")
        if v and env == "production":
            raise ValueError("debug mode is not allowed in production")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()


def validate_settings() -> list[str]:
    """Check that required settings are present for the active environment.

    Returns a list of missing field names. Callers can log or raise as needed.
    """
    missing: list[str] = []
    if settings.is_production:
        for field_name in REQUIRED_IN_PRODUCTION:
            value = getattr(settings, field_name, None)
            if not value:
                missing.append(field_name)
    return missing
