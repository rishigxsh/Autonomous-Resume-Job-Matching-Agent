"""Application configuration for the Resume–Job Matching Agent.

Settings are loaded from environment variables when present, and fall back to
the defaults below.  pydantic-settings is used so the same BaseModel
validation that governs data contracts also governs configuration values.

LLM API keys and external service settings will be added here in Phase 3.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Top-level application settings."""

    app_name: str = "Autonomous Resume–Job Matching Agent"
    version: str = "0.1.0"


# Module-level singleton — import and use `settings` everywhere.
settings = Settings()
