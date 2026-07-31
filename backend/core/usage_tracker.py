"""Daily usage and exhaustion tracker.

Tracks token consumption, call counts and exhaustion state per LLM
provider, plus the total number of conversations handled today.  All
counters roll over automatically when the calendar date changes.

Used by ``LLMProvider`` to decide when to fall back to the next
provider and when the daily conversation limit has been reached, and
by the ``GET /usage`` endpoint for transparency reports.
"""

import threading
import time
from collections import defaultdict
from datetime import date
from typing import Any


class DailyUsageTracker:
    """Thread-safe, date-aware usage tracker."""

    def __init__(
        self,
        daily_token_budget: int = 0,
        max_conversations_per_day: int = 100,
    ) -> None:
        self._lock = threading.Lock()
        self._daily_token_budget: int = daily_token_budget
        self._max_conversations_per_day: int = max_conversations_per_day

        self._date: date = date.today()
        self._tokens: dict[str, dict[str, int]] = defaultdict(
            lambda: {"prompt": 0, "completion": 0, "total": 0}
        )
        self._calls: dict[str, int] = defaultdict(int)
        self._exhausted: dict[str, str] = {}
        self._conversations_today: int = 0

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _rollover(self) -> None:
        """Reset counters when the calendar date has changed."""
        today = date.today()
        if today != self._date:
            self._date = today
            self._tokens.clear()
            self._calls.clear()
            self._exhausted.clear()
            self._conversations_today = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_tokens(
        self,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Accumulate token usage for a provider."""
        prompt_tokens = max(0, int(prompt_tokens or 0))
        completion_tokens = max(0, int(completion_tokens or 0))
        with self._lock:
            self._rollover()
            usage = self._tokens[provider]
            usage["prompt"] += prompt_tokens
            usage["completion"] += completion_tokens
            usage["total"] += prompt_tokens + completion_tokens
            self._calls[provider] += 1

    def record_conversation(self) -> None:
        """Count one conversation against the daily limit."""
        with self._lock:
            self._rollover()
            self._conversations_today += 1

    def mark_exhausted(self, provider: str, reason: str) -> None:
        """Mark a provider as exhausted until the next day."""
        with self._lock:
            self._rollover()
            self._exhausted[provider] = reason

    def clear_exhausted(self, provider: str) -> None:
        """Remove the exhausted flag for a provider."""
        with self._lock:
            self._rollover()
            self._exhausted.pop(provider, None)

    def is_exhausted(self, provider: str) -> bool:
        """Return whether a provider has been marked exhausted today."""
        with self._lock:
            self._rollover()
            return provider in self._exhausted

    def exhaustion_reason(self, provider: str) -> str:
        """Return the reason a provider was exhausted (or ``""``)."""
        with self._lock:
            self._rollover()
            return self._exhausted.get(provider, "")

    def budget_reached(self, provider: str) -> bool:
        """Return whether a provider has exceeded the daily token budget."""
        if self._daily_token_budget <= 0:
            return False
        with self._lock:
            self._rollover()
            return self._tokens[provider]["total"] >= self._daily_token_budget

    def conversations_today(self) -> int:
        """Return the number of conversations handled today."""
        with self._lock:
            self._rollover()
            return self._conversations_today

    def daily_limit_reached(self) -> bool:
        """Return whether the daily conversation limit has been reached."""
        return self.conversations_today() >= self._max_conversations_per_day

    def provider_can_serve(self, provider: str) -> bool:
        """Return whether a provider may still be used right now."""
        return not (
            self.is_exhausted(provider)
            or self.budget_reached(provider)
            or self.daily_limit_reached()
        )

    def snapshot(self) -> dict[str, Any]:
        """Return a full usage and exhaustion report for today."""
        with self._lock:
            self._rollover()
            return {
                "date": self._date.isoformat(),
                "conversations_today": self._conversations_today,
                "max_conversations_per_day": self._max_conversations_per_day,
                "daily_limit_reached": self._conversations_today
                >= self._max_conversations_per_day,
                "daily_token_budget": self._daily_token_budget,
                "providers": {
                    provider: {
                        "tokens": dict(self._tokens[provider]),
                        "calls": self._calls[provider],
                        "exhausted": provider in self._exhausted,
                        "exhausted_reason": self._exhausted.get(provider, ""),
                        "budget_reached": self._daily_token_budget > 0
                        and self._tokens[provider]["total"]
                        >= self._daily_token_budget,
                    }
                    for provider in sorted(
                        set(self._tokens) | set(self._calls) | set(self._exhausted)
                    )
                },
            }


usage_tracker = DailyUsageTracker()


def _utc_now() -> float:
    """Current UNIX timestamp (helper for tests)."""
    return time.time()
