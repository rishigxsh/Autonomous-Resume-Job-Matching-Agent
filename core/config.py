"""Application configuration for the Resume–Job Matching Agent.

Settings are loaded from environment variables (or a local .env file) and fall
back to the defaults below.

Required environment variables:
    ANTHROPIC_API_KEY   — your Anthropic API key (no default; must be set)

Optional environment variables:
    ENV                 — "dev" or "prod" (default: dev)
    CORS_ORIGINS        — comma-separated allowed origins (default: localhost dev ports)
    LLM_MODEL           — Claude model ID (default: claude-sonnet-4-6)
    LLM_TEMPERATURE     — sampling temperature (default: 0.0)
    LLM_MAX_TOKENS      — max tokens for LLM response (default: 2000)
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Autonomous Resume–Job Matching Agent"
    version: str = "0.1.0"

    # Environment mode
    env: str = "dev"  # "dev" or "prod"

    # CORS — comma-separated string, split at runtime.
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"

    # Anthropic LLM settings
    anthropic_api_key: str  # Required — no default; server will fail fast if missing.
    llm_model: str = "claude-sonnet-4-6"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 2000

    @property
    def is_prod(self) -> bool:
        return self.env.lower() == "prod"

    @property
    def allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# Module-level singleton — import and use `settings` everywhere.
settings = Settings()
