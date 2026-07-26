"""LLM Provider.

Abstracts communication with supported language model providers
(OpenAI, Gemini) behind a common interface.

Provider selection and model names are read from environment variables:

- ``LLM_PROVIDER`` — ``"openai"`` (default) or ``"gemini"``
- ``OPENAI_MODEL``  — e.g. ``"gpt-4o-mini"``
- ``GEMINI_MODEL``  — e.g. ``"gemini-1.5-flash"``

API keys and shared parameters are consumed from the project's
``Settings`` singleton (``openai_api_key``, ``gemini_api_key``,
``max_tokens``, ``temperature``).

Timeout: 30 seconds.
Retries: 2 attempts on transient failures (rate limits, server errors,
timeouts, connection errors).
"""

import logging
import os
import time
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT: int = 30
_DEFAULT_MAX_RETRIES: int = 2
_DEFAULT_MAX_TOKENS: int = 300
_DEFAULT_TEMPERATURE: float = 0.7


class LLMProvider:
    """Abstraction layer for language model backends.

    Usage
    -----
        provider = LLMProvider()
        response = provider.generate(master_prompt)

    Parameters can be injected via the constructor for testing or
    overridden at runtime.
    """

    def __init__(
        self,
        provider: str | None = None,
        openai_api_key: str | None = None,
        openai_model: str | None = None,
        gemini_api_key: str | None = None,
        gemini_model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        """Initialise the LLM provider.

        Every parameter is optional.  Values not supplied are resolved
        from environment variables or the project ``Settings`` singleton
        as documented in the module docstring.

        Parameters
        ----------
        provider : str | None
            ``"openai"`` or ``"gemini"``.  Falls back to the
            ``LLM_PROVIDER`` env var (default ``"openai"``).
        openai_api_key : str | None
            Override for the OpenAI API key.
        openai_model : str | None
            Override for the OpenAI model name.
        gemini_api_key : str | None
            Override for the Gemini API key.
        gemini_model : str | None
            Override for the Gemini model name.
        max_tokens : int | None
            Maximum response tokens.  Falls back to ``settings.max_tokens``
            then ``300``.
        temperature : float | None
            Sampling temperature.  Falls back to ``settings.temperature``
            then ``0.7``.
        timeout : int | None
            Request timeout in seconds.  Falls back to ``30``.
        max_retries : int | None
            Number of retries on transient failures.  Falls back to
            ``2``.
        """
        # --- provider selection ---
        self._provider: str = (
            (provider or os.getenv("LLM_PROVIDER") or "openai").strip().lower()
        )

        # --- OpenAI ---
        self._openai_api_key: str = (
            openai_api_key or settings.openai_api_key or ""
        )
        self._openai_model: str = (
            openai_model or os.getenv("OPENAI_MODEL") or ""
        )

        # --- Gemini ---
        self._gemini_api_key: str = (
            gemini_api_key or settings.gemini_api_key or ""
        )
        self._gemini_model: str = (
            gemini_model or os.getenv("GEMINI_MODEL") or ""
        )

        # --- shared parameters ---
        self._max_tokens: int = (
            max_tokens if max_tokens is not None
            else (settings.max_tokens or _DEFAULT_MAX_TOKENS)
        )
        self._temperature: float = (
            temperature if temperature is not None
            else (settings.temperature or _DEFAULT_TEMPERATURE)
        )
        self._timeout: int = timeout if timeout is not None else _DEFAULT_TIMEOUT
        self._max_retries: int = (
            max_retries if max_retries is not None else _DEFAULT_MAX_RETRIES
        )

        logger.info(
            "LLMProvider ready (provider=%s, timeout=%ds, max_retries=%d)",
            self._provider,
            self._timeout,
            self._max_retries,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """Send a prompt to the active LLM backend and return the response.

        Parameters
        ----------
        prompt : str
            The master prompt produced by ``PromptBuilder.build_prompt()``.

        Returns
        -------
        str
            The text content of the model's response.

        Raises
        ------
        ValueError
            If the configured provider is unsupported or missing required
            configuration (API key, model name).
        RuntimeError
            If generation fails after exhausting all retries.
        """
        if self._provider == "openai":
            return self._call_openai(prompt)
        elif self._provider == "gemini":
            return self._call_gemini(prompt)
        else:
            raise ValueError(
                f"Unsupported LLM provider: '{self._provider}'. "
                f"Expected 'openai' or 'gemini'. "
                f"Set the LLM_PROVIDER environment variable."
            )

    # ------------------------------------------------------------------
    # Provider-specific implementations
    # ------------------------------------------------------------------

    def _call_openai(self, prompt: str) -> str:
        """Send the prompt to the OpenAI API.

        Parameters
        ----------
        prompt : str

        Returns
        -------
        str

        Raises
        ------
        ValueError
            If the API key or model name is missing.
        RuntimeError
            If generation fails after retries.
        """
        if not self._openai_api_key:
            raise ValueError(
                "OpenAI API key is not configured. "
                "Set the OPENAI_API_KEY environment variable."
            )
        if not self._openai_model:
            raise ValueError(
                "OpenAI model name is not configured. "
                "Set the OPENAI_MODEL environment variable."
            )

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self._openai_api_key,
                timeout=self._timeout,
                max_retries=self._max_retries,
            )

            response = client.chat.completions.create(
                model=self._openai_model,
                messages=[
                    {"role": "system", "content": prompt},
                ],
                max_tokens=self._max_tokens,
                temperature=self._temperature,
            )

            content: str = response.choices[0].message.content or ""
            logger.debug(
                "OpenAI response received (%d chars, model=%s)",
                len(content),
                self._openai_model,
            )
            return content

        except Exception as exc:
            logger.error("OpenAI generation failed: %s", exc)
            raise RuntimeError(
                f"OpenAI generation failed after {self._max_retries} retries: {exc}"
            ) from exc

    def _call_gemini(self, prompt: str) -> str:
        """Send the prompt to the Gemini API.

        Parameters
        ----------
        prompt : str

        Returns
        -------
        str

        Raises
        ------
        ValueError
            If the API key or model name is missing.
        RuntimeError
            If generation fails after retries.
        """
        if not self._gemini_api_key:
            raise ValueError(
                "Gemini API key is not configured. "
                "Set the GEMINI_API_KEY environment variable."
            )
        if not self._gemini_model:
            raise ValueError(
                "Gemini model name is not configured. "
                "Set the GEMINI_MODEL environment variable."
            )

        import google.generativeai as genai

        genai.configure(api_key=self._gemini_api_key)
        model = genai.GenerativeModel(self._gemini_model)

        last_exception: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=self._max_tokens,
                        temperature=self._temperature,
                    ),
                    request_options={"timeout": self._timeout},
                )

                content: str = response.text if response else ""
                logger.debug(
                    "Gemini response received (%d chars, model=%s)",
                    len(content),
                    self._gemini_model,
                )
                return content

            except (genai.types.BlockedPromptException,
                    genai.types.StopCandidateException) as exc:
                # Permanent — do not retry.
                logger.error("Gemini request blocked or stopped: %s", exc)
                raise RuntimeError(f"Gemini request rejected: {exc}") from exc

            except Exception as exc:
                last_exception = exc
                is_transient = self._is_transient_gemini_error(exc)

                if is_transient and attempt < self._max_retries:
                    wait = 2 ** attempt  # exponential backoff
                    logger.warning(
                        "Gemini transient error (attempt %d/%d): %s. "
                        "Retrying in %ds …",
                        attempt,
                        self._max_retries,
                        exc,
                        wait,
                    )
                    time.sleep(wait)
                    continue

                logger.error(
                    "Gemini generation failed (attempt %d/%d): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                break

        raise RuntimeError(
            f"Gemini generation failed after {self._max_retries} retries: "
            f"{last_exception}"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_transient_gemini_error(exc: Exception) -> bool:
        """Determine whether a Gemini SDK exception is transient.

        Transient errors are those that may succeed after a short
        delay (rate limits, server unavailability, timeouts).
        """
        exc_name = type(exc).__name__

        # google.api_core exceptions
        transient_patterns = (
            "ResourceExhausted",
            "ServiceUnavailable",
            "DeadlineExceeded",
            "InternalServerError",
            "GatewayTimeout",
            "TooManyRequests",
        )
        if any(p in exc_name for p in transient_patterns):
            return True

        # httpx / connection-level timeouts
        if isinstance(exc, TimeoutError):
            return True

        return False
