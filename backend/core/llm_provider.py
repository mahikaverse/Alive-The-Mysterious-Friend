"""LLM Provider.

Abstraction for language-model backends with automatic multi-provider
failover and token-saving behaviour.

Provider chain
--------------
A chain is built from a primary provider plus a fallback order
(``LLM_FALLBACK_ORDER``).  Providers that have no API key configured
are skipped.  When a provider is exhausted (quota / rate limit /
insufficient balance) it is marked unavailable for the rest of the
day and the next provider in the chain is tried.  If every provider
is exhausted the daily conversation limit is considered reached, a
notification is recorded, and a graceful in-character reply is
returned.

Supported providers:

- ``"openai"``      — ``OPENAI_API_KEY`` / ``OPENAI_MODEL``
- ``"gemini"``      — ``GEMINI_API_KEY`` / ``GEMINI_MODEL``
- ``"deepseek"``    — ``DEEPSEEK_API_KEY`` / ``DEEPSEEK_MODEL``
- ``"nvidia"``      — ``NVIDIA_API_KEY`` / ``NVIDIA_MODEL``
- ``"openrouter"``  — ``OPENROUTER_API_KEY`` / ``OPENROUTER_MODEL``
- ``"grok"``        — ``GROK_API_KEY`` / ``GROK_MODEL``

Shared parameters (``max_tokens``, ``temperature``, ``timeout``,
``max_retries``) come from the project ``Settings`` singleton or can
be injected for testing.

Token-saving features
---------------------
- Conversation compaction (request layer, see ConversationCompactor).
- Prompt compression before a fallback provider is tried.
- Per-provider daily token budgets and a daily conversation limit.
- Optional in-memory response cache for repeated identical prompts.
- Exhausted providers are skipped, avoiding wasted retries.
"""

import logging
import os
import time
from datetime import date
from typing import Any

from backend.config.settings import settings
from backend.core.conversation_compactor import compactor, estimate_tokens
from backend.core.notifications import notification_manager
from backend.core.usage_tracker import usage_tracker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_TIMEOUT: int = 30
_DEFAULT_MAX_RETRIES: int = 2
_DEFAULT_MAX_TOKENS: int = 300
_DEFAULT_TEMPERATURE: float = 0.7

_DEFAULT_FALLBACK_ORDER: tuple[str, ...] = ("nvidia", "openrouter", "grok")

_OPENAI_COMPATIBLE_BASE_URLS: dict[str, str] = {
    "deepseek": "https://api.deepseek.com",
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "grok": "https://api.x.ai/v1",
}

_ALL_PROVIDERS: tuple[str, ...] = (
    "openai",
    "gemini",
    "deepseek",
    "nvidia",
    "openrouter",
    "grok",
)

_DAILY_LIMIT_REPLY: str = (
    "Hey… I've hit my daily conversation limit for today. "
    "Let's pick this up again tomorrow — I'll be right here."
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _looks_like_exhaustion(exc: Exception) -> bool:
    """Heuristically detect quota / rate-limit / billing errors.

    Returns ``True`` for errors that indicate a provider should be
    considered exhausted for the day (401/402/403/429, insufficient
    balance, rate limits), ``False`` for generic transient failures.
    """
    exc_name = type(exc).__name__
    message = str(exc).lower()

    exhaustion_markers = (
        "insufficient_quota",
        "insufficient quota",
        "insufficient balance",
        "out of credits",
        "out of quota",
        "quota exceeded",
        "exceeded your current quota",
        "rate limit",
        "rate_limit",
        "too many requests",
        "429",
        "402",
        "billing",
        "payment required",
        "credit",
        "no balance",
        "resource_exhausted",
        "exhausted",
    )

    for marker in exhaustion_markers:
        if marker in message or marker in exc_name.lower():
            return True

    # openai SDK status-based detection
    status = getattr(exc, "status_code", None)
    if status in (401, 402, 403, 429):
        return True

    # google.api_core ResourceExhausted surfaced by the Gemini SDK
    if "ResourceExhausted" in exc_name or "QuotaExceeded" in exc_name:
        return True

    return False


def _extract_usage(response: Any) -> tuple[int, int]:
    """Best-effort extraction of (prompt_tokens, completion_tokens)."""
    usage = getattr(response, "usage", None)
    if usage is not None:
        try:
            prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
            completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            return prompt_tokens, completion_tokens
        except (TypeError, ValueError):
            pass

    usage_metadata = getattr(response, "usage_metadata", None)
    if usage_metadata is not None:
        prompt_tokens = int(
            getattr(usage_metadata, "prompt_token_count", 0) or 0
        )
        completion_tokens = int(
            getattr(usage_metadata, "candidates_token_count", 0) or 0
        )
        return prompt_tokens, completion_tokens

    return 0, 0


class LLMProvider:
    """Abstraction layer for language model backends with failover.

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
        fallback_order: str | None = None,
        openai_api_key: str | None = None,
        openai_model: str | None = None,
        gemini_api_key: str | None = None,
        gemini_model: str | None = None,
        deepseek_api_key: str | None = None,
        deepseek_model: str | None = None,
        nvidia_api_key: str | None = None,
        nvidia_model: str | None = None,
        openrouter_api_key: str | None = None,
        openrouter_model: str | None = None,
        grok_api_key: str | None = None,
        grok_model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        """Initialise the LLM provider.

        Values not supplied are resolved from environment variables or
        the project ``Settings`` singleton.

        Parameters
        ----------
        provider : str | None
            Primary provider.  Falls back to the ``LLM_PROVIDER`` env
            var (default ``"deepseek"``).
        fallback_order : str | None
            Comma-separated fallback providers tried after the primary
            is exhausted.  Falls back to ``LLM_FALLBACK_ORDER``.
        """
        primary: str = (
            (provider or os.getenv("LLM_PROVIDER") or settings.llm_provider)
            .strip()
            .lower()
        )

        fallback_raw: str = (
            fallback_order
            or os.getenv("LLM_FALLBACK_ORDER")
            or settings.llm_fallback_order
            or ""
        )
        fallbacks: list[str] = [
            p.strip().lower()
            for p in fallback_raw.split(",")
            if p.strip().lower()
        ]

        # --- provider credentials & models ---
        self._openai_api_key: str = openai_api_key or settings.openai_api_key or ""
        self._openai_model: str = (
            openai_model or os.getenv("OPENAI_MODEL") or settings.openai_model or ""
        )

        self._gemini_api_key: str = gemini_api_key or settings.gemini_api_key or ""
        self._gemini_model: str = (
            gemini_model or os.getenv("GEMINI_MODEL") or settings.gemini_model or ""
        )

        self._deepseek_api_key: str = deepseek_api_key or settings.deepseek_api_key or ""
        self._deepseek_model: str = (
            deepseek_model or os.getenv("DEEPSEEK_MODEL") or settings.deepseek_model or ""
        )

        self._nvidia_api_key: str = nvidia_api_key or settings.nvidia_api_key or ""
        self._nvidia_model: str = (
            nvidia_model or os.getenv("NVIDIA_MODEL") or settings.nvidia_model or ""
        )

        self._openrouter_api_key: str = (
            openrouter_api_key or settings.openrouter_api_key or ""
        )
        self._openrouter_model: str = (
            openrouter_model
            or os.getenv("OPENROUTER_MODEL")
            or settings.openrouter_model
            or ""
        )

        self._grok_api_key: str = grok_api_key or settings.grok_api_key or ""
        self._grok_model: str = (
            grok_model or os.getenv("GROK_MODEL") or settings.grok_model or ""
        )

        # --- shared parameters ---
        self._max_tokens: int = (
            max_tokens
            if max_tokens is not None
            else (settings.max_tokens or _DEFAULT_MAX_TOKENS)
        )
        self._temperature: float = (
            temperature
            if temperature is not None
            else (settings.temperature or _DEFAULT_TEMPERATURE)
        )
        self._timeout: int = timeout if timeout is not None else _DEFAULT_TIMEOUT
        self._max_retries: int = (
            max_retries if max_retries is not None else _DEFAULT_MAX_RETRIES
        )

        # --- provider chain (dedup, primary first, configured keys only) ---
        chain = [primary]
        for p in fallbacks:
            if p not in chain:
                chain.append(p)
        for p in _ALL_PROVIDERS:  # always append any remaining known providers
            if p not in chain:
                chain.append(p)

        self._chain: list[str] = [p for p in chain if self._has_credentials(p)]

        # --- caching ---
        self._cache_enabled: bool = settings.llm_cache_enabled
        self._cache: dict[tuple, str] = {}
        self._cache_order: list[tuple] = []
        self._cache_max_entries: int = settings.llm_cache_max_entries

        # --- daily-limit notification guard ---
        self._daily_limit_notified_date: date | None = None
        self._compressed_prompt: str | None = None

        logger.info(
            "LLMProvider ready (chain=%s, timeout=%ds, max_retries=%d)",
            self._chain,
            self._timeout,
            self._max_retries,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """Send a prompt to the LLM backend with automatic failover.

        Parameters
        ----------
        prompt : str
            The master prompt produced by ``PromptBuilder.build_prompt()``.

        Returns
        -------
        str
            The text content of the model's response.  When every
            provider is exhausted a graceful daily-limit reply is
            returned and a notification is recorded.

        Raises
        ------
        ValueError
            If no provider is configured at all.
        RuntimeError
            If generation fails across the chain for non-exhaustion
            reasons (e.g. all providers errored transiently).
        """
        if not self._chain:
            raise ValueError(
                "No LLM provider configured. Add at least one API key "
                "(DEEPSEEK_API_KEY, NVIDIA_API_KEY, OPENROUTER_API_KEY, GROK_API_KEY, ...) "
                "and set LLM_PROVIDER."
            )

        if usage_tracker.daily_limit_reached():
            self._notify_daily_limit()
            return _DAILY_LIMIT_REPLY

        errors: dict[str, Exception] = {}
        self._compressed_prompt = None

        for provider in self._chain:
            if not usage_tracker.provider_can_serve(provider):
                continue

            cache_key = self._cache_key(provider, prompt)
            if self._cache_enabled and cache_key in self._cache:
                logger.info("[llm] cache hit (provider=%s)", provider)
                usage_tracker.record_conversation()
                return self._cache[cache_key]

            try:
                content = self._call(provider, prompt)
            except Exception as exc:  # noqa: BLE001 — failover by design
                errors[provider] = exc
                reason = str(exc) or type(exc).__name__

                if _looks_like_exhaustion(exc):
                    usage_tracker.mark_exhausted(provider, reason)
                    notification_manager.notify(
                        f"Provider '{provider}' exhausted: {reason}",
                        level="warning",
                        source="llm",
                        provider=provider,
                        action="fallback",
                    )
                    logger.warning(
                        "[llm] provider '%s' exhausted (%s) — falling back",
                        provider,
                        reason,
                    )
                else:
                    notification_manager.notify(
                        f"Provider '{provider}' failed: {reason}",
                        level="warning",
                        source="llm",
                        provider=provider,
                        action="fallback",
                    )
                    logger.warning(
                        "[llm] provider '%s' failed (%s) — falling back",
                        provider,
                        reason,
                    )

                # Compress the prompt before the next provider so the
                # fallback consumes fewer tokens.
                prompt = self._compress(prompt, len(errors))
                continue

            prompt_tokens, completion_tokens = _extract_usage(content[1])
            usage_tracker.record_tokens(
                provider, prompt_tokens, completion_tokens
            )
            usage_tracker.record_conversation()

            if self._cache_enabled:
                self._cache_put(cache_key, content[0])

            logger.info(
                "[llm] response from '%s' (model=%s, tokens=%d/%d)",
                provider,
                self._model_for(provider),
                prompt_tokens,
                completion_tokens,
            )
            return content[0]

        # All providers exhausted or failed.
        if self._chain and all(
            usage_tracker.exhaustion_reason(p)
            or (p not in errors and not usage_tracker.provider_can_serve(p))
            for p in self._chain
        ):
            self._notify_daily_limit()
            return _DAILY_LIMIT_REPLY

        if errors:
            raise RuntimeError(
                f"All {len(self._chain)} LLM provider(s) failed: "
                + "; ".join(f"{p}: {e}" for p, e in errors.items())
            )

        return _DAILY_LIMIT_REPLY

    # ------------------------------------------------------------------
    # Provider dispatch
    # ------------------------------------------------------------------

    def _call(self, provider: str, prompt: str) -> tuple[str, Any]:
        """Dispatch to the provider implementation.

        Returns ``(content, raw_response)`` so token usage can be
        extracted afterwards.
        """
        if provider == "openai":
            return self._call_openai_compatible(
                provider,
                api_key=self._openai_api_key,
                model=self._openai_model,
                base_url=None,
                prompt=prompt,
            )
        if provider == "gemini":
            return self._call_gemini(prompt)
        if provider == "deepseek":
            return self._call_openai_compatible(
                provider,
                api_key=self._deepseek_api_key,
                model=self._deepseek_model,
                base_url=_OPENAI_COMPATIBLE_BASE_URLS["deepseek"],
                prompt=prompt,
            )
        if provider == "nvidia":
            return self._call_openai_compatible(
                provider,
                api_key=self._nvidia_api_key,
                model=self._nvidia_model,
                base_url=_OPENAI_COMPATIBLE_BASE_URLS["nvidia"],
                prompt=prompt,
            )
        if provider == "openrouter":
            return self._call_openai_compatible(
                provider,
                api_key=self._openrouter_api_key,
                model=self._openrouter_model,
                base_url=_OPENAI_COMPATIBLE_BASE_URLS["openrouter"],
                prompt=prompt,
                extra_headers={
                    "HTTP-Referer": "https://github.com/anomalyco/opencode",
                    "X-Title": "Alive",
                },
            )
        if provider == "grok":
            return self._call_openai_compatible(
                provider,
                api_key=self._grok_api_key,
                model=self._grok_model,
                base_url=_OPENAI_COMPATIBLE_BASE_URLS["grok"],
                prompt=prompt,
            )
        raise ValueError(f"Unsupported LLM provider: '{provider}'")

    def _call_openai_compatible(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: str | None,
        prompt: str,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[str, Any]:
        """Send a chat-completion request to any OpenAI-compatible API.

        Returns ``(content, raw_response)``.

        Raises
        ------
        ValueError
            If the API key or model name is missing.
        RuntimeError
            If the request fails after retries.
        """
        if not api_key:
            raise ValueError(
                f"{provider.capitalize()} API key is not configured. "
                f"Set the {provider.upper()}_API_KEY environment variable."
            )
        if not model:
            raise ValueError(
                f"{provider.capitalize()} model name is not configured. "
                f"Set the {provider.upper()}_MODEL environment variable."
            )

        try:
            from openai import OpenAI

            client_kwargs: dict[str, Any] = {
                "api_key": api_key,
                "timeout": self._timeout,
                "max_retries": self._max_retries,
            }
            if base_url:
                client_kwargs["base_url"] = base_url

            client = OpenAI(**client_kwargs)

            request_kwargs: dict[str, Any] = {
                "model": model,
                "messages": [{"role": "system", "content": prompt}],
                "max_tokens": self._max_tokens,
                "temperature": self._temperature,
            }
            if extra_headers:
                request_kwargs["extra_headers"] = extra_headers

            response = client.chat.completions.create(**request_kwargs)

            content: str = response.choices[0].message.content or ""
            logger.debug(
                "%s response received (%d chars, model=%s)",
                provider.capitalize(),
                len(content),
                model,
            )
            return content, response

        except ValueError:
            raise

        except Exception as exc:
            logger.error("%s generation failed: %s", provider.capitalize(), exc)
            raise RuntimeError(
                f"{provider.capitalize()} generation failed after "
                f"{self._max_retries} retries: {exc}"
            ) from exc

    def _call_gemini(self, prompt: str) -> tuple[str, Any]:
        """Send the prompt to the Gemini API.

        Returns ``(content, raw_response)``.
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
                return content, response

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
    # Token-saving helpers
    # ------------------------------------------------------------------

    def _has_credentials(self, provider: str) -> bool:
        """Return whether an API key is configured for ``provider``."""
        if provider == "openai":
            return bool(self._openai_api_key)
        if provider == "gemini":
            return bool(self._gemini_api_key)
        if provider == "deepseek":
            return bool(self._deepseek_api_key)
        if provider == "nvidia":
            return bool(self._nvidia_api_key)
        if provider == "openrouter":
            return bool(self._openrouter_api_key)
        if provider == "grok":
            return bool(self._grok_api_key)
        return False

    def _model_for(self, provider: str) -> str:
        """Return the configured model name for ``provider``."""
        return {
            "openai": self._openai_model,
            "gemini": self._gemini_model,
            "deepseek": self._deepseek_model,
            "nvidia": self._nvidia_model,
            "openrouter": self._openrouter_model,
            "grok": self._grok_model,
        }.get(provider, "")

    def _compress(self, prompt: str, error_count: int) -> str:
        """Compress the prompt once, then reuse it for later fallbacks."""
        if error_count == 1:
            logger.info(
                "[llm] compressing prompt for fallback (%d provider(s) failed so far)",
                error_count,
            )
            self._compressed_prompt = compactor.compress_prompt(prompt)
        return self._compressed_prompt or prompt

    def _cache_key(self, provider: str, prompt: str) -> tuple:
        return (provider, prompt, self._max_tokens, self._temperature)

    def _cache_put(self, key: tuple, value: str) -> None:
        """Store a response in the bounded LRU cache."""
        if not self._cache_enabled:
            return
        if key in self._cache:
            self._cache_order.remove(key)
        self._cache[key] = value
        self._cache_order.append(key)
        while len(self._cache_order) > self._cache_max_entries:
            oldest = self._cache_order.pop(0)
            self._cache.pop(oldest, None)

    def _notify_daily_limit(self) -> None:
        """Record the daily-conversation-limit notification once per day."""
        today = date.today()
        if self._daily_limit_notified_date == today:
            return
        self._daily_limit_notified_date = today
        usage_tracker.record_conversation()
        notification_manager.notify(
            "Daily conversation limit reached — all LLM providers are "
            "exhausted. Conversations are paused until tomorrow.",
            level="error",
            source="llm",
            action="daily_limit",
            providers=list(self._chain),
        )
        logger.error("Daily conversation limit reached — all providers exhausted.")

    @staticmethod
    def _is_transient_gemini_error(exc: Exception) -> bool:
        """Determine whether a Gemini SDK exception is transient."""
        exc_name = type(exc).__name__

        transient_patterns = (
            "ServiceUnavailable",
            "DeadlineExceeded",
            "InternalServerError",
            "GatewayTimeout",
            "TooManyRequests",
        )
        if any(p in exc_name for p in transient_patterns):
            return True

        if isinstance(exc, TimeoutError):
            return True

        return False
