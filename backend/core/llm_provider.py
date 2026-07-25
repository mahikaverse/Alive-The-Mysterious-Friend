"""LLM Provider.

Abstracts communication with supported language model providers
(OpenAI, Gemini) behind a common interface.
"""

import logging

logger = logging.getLogger(__name__)


class LLMProvider:
    """Abstraction layer for language model backends."""

    def generate(self, prompt: str) -> str:
        """Send a prompt to the active LLM backend and return the response."""
        pass

    def _call_openai(self, prompt: str) -> str:
        """Send the prompt to the OpenAI API."""
        pass

    def _call_gemini(self, prompt: str) -> str:
        """Send the prompt to the Gemini API."""
        pass
