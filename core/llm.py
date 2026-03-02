"""Anthropic LLM client wrapper for the Resume–Job Matching Agent.

Responsibilities:
- Initialise the Anthropic client from settings.
- Expose a single generate_text() method used by all parsing endpoints.

Scoring logic does NOT go here — this module is parsing-only.
"""

import logging
import traceback

import anthropic

from core.config import settings
from core.errors import internal_error

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around the Anthropic messages API."""

    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Check your .env file.")
        logger.info("LLMClient initialised. API key present: YES. Model: %s", settings.llm_model)
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the LLM and return the raw text response.

        Args:
            system_prompt: The system-level instruction (role + output rules).
            user_prompt: The user-level content (the actual text to parse).

        Returns:
            Raw string content from the first text block of the LLM response.

        Raises:
            HTTPException(500): On any Anthropic API error.
        """
        try:
            message = self._client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as exc:
            logger.error("Anthropic API error: %s\n%s", exc, traceback.format_exc())
            raise internal_error(f"Anthropic API error: {exc}") from exc

        raw = message.content[0].text
        # Log a truncated preview to aid debugging without flooding logs.
        logger.debug("Raw LLM output (first 500 chars): %s", raw[:500])
        return raw


# Module-level singleton — avoids re-initialising the client on every request.
llm_client = LLMClient()
