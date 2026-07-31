"""Unit tests for the multi-provider failover, token-saving, and
notification features (Person 2).

Ownership: Person 1 (Backend & Infrastructure)
"""

import sys
import os
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from backend.config.settings import settings
from backend.core.conversation_compactor import ConversationCompactor, estimate_tokens
from backend.core.llm_provider import LLMProvider, _looks_like_exhaustion
from backend.core.notifications import NotificationManager
from backend.core.usage_tracker import DailyUsageTracker

_SETTINGS_KEYS = (
    "openai_api_key",
    "gemini_api_key",
    "deepseek_api_key",
    "nvidia_api_key",
    "openrouter_api_key",
    "grok_api_key",
)


@pytest.fixture(autouse=True)
def _reset_usage_tracker(monkeypatch):
    """Isolate tests from .env API keys and reset the shared tracker."""
    for name in _SETTINGS_KEYS:
        monkeypatch.setattr(settings, name, "")

    from backend.core import usage_tracker as module

    module.usage_tracker._exhausted.clear()
    module.usage_tracker._conversations_today = 0
    module.usage_tracker._tokens.clear()
    module.usage_tracker._calls.clear()
    yield
    module.usage_tracker._exhausted.clear()
    module.usage_tracker._conversations_today = 0
    module.usage_tracker._tokens.clear()
    module.usage_tracker._calls.clear()


# ---------------------------------------------------------------------------
# Provider chain construction
# ---------------------------------------------------------------------------


def test_chain_order_primary_first():
    p = LLMProvider(
        provider="deepseek",
        fallback_order="nvidia,openrouter",
        deepseek_api_key="sk-ds",
        nvidia_api_key="nv-",
        openrouter_api_key="or-",
    )
    assert p._chain == ["deepseek", "nvidia", "openrouter"]


def test_chain_skips_unconfigured_providers():
    p = LLMProvider(
        provider="deepseek",
        fallback_order="nvidia,openrouter",
        deepseek_api_key="sk-ds",
    )
    assert p._chain == ["deepseek"]


def test_chain_dedupes_fallback():
    p = LLMProvider(
        provider="nvidia",
        fallback_order="nvidia,openrouter",
        nvidia_api_key="nv-",
        openrouter_api_key="or-",
    )
    assert p._chain == ["nvidia", "openrouter"]


def test_no_chain_raises():
    p = LLMProvider(
        provider="deepseek",
        fallback_order="",
        openai_api_key="",
    )
    with pytest.raises(ValueError):
        p.generate("hello")


# ---------------------------------------------------------------------------
# Exhaustion detection
# ---------------------------------------------------------------------------


def test_looks_like_exhaustion_status():
    class _Err(Exception):
        status_code = 402

    assert _looks_like_exhaustion(_Err("Insufficient Balance")) is True


def test_looks_like_exhaustion_message():
    class _Err(Exception):
        pass

    assert _looks_like_exhaustion(_Err("rate limit exceeded")) is True
    assert _looks_like_exhaustion(_Err("insufficient_quota")) is True


def test_looks_like_exhaustion_transient_is_false():
    class _Err(Exception):
        status_code = 500

    assert _looks_like_exhaustion(_Err("internal server error")) is False


# ---------------------------------------------------------------------------
# Failover behaviour
# ---------------------------------------------------------------------------


def _fake_response(content: str, prompt_tokens: int = 10, completion_tokens: int = 5):
    return (
        content,
        SimpleNamespace(
            usage=SimpleNamespace(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        ),
    )


def test_failover_to_next_provider_when_primary_exhausted(monkeypatch):
    class _QuotaError(Exception):
        status_code = 402

    p = LLMProvider(
        provider="deepseek",
        fallback_order="nvidia",
        deepseek_api_key="sk-ds",
        nvidia_api_key="nv-",
    )

    def fake_call(provider, prompt):
        if provider == "deepseek":
            raise _QuotaError("Insufficient Balance")
        return _fake_response("hello from nvidia", prompt_tokens=20)

    monkeypatch.setattr(p, "_call", fake_call)

    result = p.generate("test prompt")
    assert result == "hello from nvidia"

    from backend.core.usage_tracker import usage_tracker

    assert usage_tracker.is_exhausted("deepseek")
    assert not usage_tracker.is_exhausted("nvidia")
    assert usage_tracker.snapshot()["providers"]["nvidia"]["tokens"]["total"] == 25


def test_all_providers_exhausted_returns_daily_limit_reply(monkeypatch):
    class _QuotaError(Exception):
        status_code = 429

    p = LLMProvider(
        provider="deepseek",
        fallback_order="nvidia",
        deepseek_api_key="sk-ds",
        nvidia_api_key="nv-",
    )

    def fake_call(provider, prompt):
        raise _QuotaError("rate limit exceeded")

    monkeypatch.setattr(p, "_call", fake_call)

    result = p.generate("test prompt")
    assert "daily conversation limit" in result

    from backend.core.notifications import notification_manager

    messages = [n["message"] for n in notification_manager.list()]
    assert any("Daily conversation limit reached" in m for m in messages)


def test_transient_failure_still_falls_back(monkeypatch):
    p = LLMProvider(
        provider="deepseek",
        fallback_order="nvidia",
        deepseek_api_key="sk-ds",
        nvidia_api_key="nv-",
    )

    def fake_call(provider, prompt):
        if provider == "deepseek":
            raise TimeoutError("connection timed out")
        return _fake_response("recovered", prompt_tokens=5)

    monkeypatch.setattr(p, "_call", fake_call)

    result = p.generate("test")
    assert result == "recovered"

    from backend.core.usage_tracker import usage_tracker

    # Timeout is transient — primary should NOT be marked exhausted.
    assert not usage_tracker.is_exhausted("deepseek")


def test_prompt_is_compressed_on_fallback(monkeypatch):
    class _QuotaError(Exception):
        status_code = 402

    p = LLMProvider(
        provider="deepseek",
        fallback_order="nvidia",
        deepseek_api_key="sk-ds",
        nvidia_api_key="nv-",
    )

    big_prompt = "A" * 20000

    seen_prompts = []

    def fake_call(provider, prompt):
        seen_prompts.append((provider, prompt))
        if provider == "deepseek":
            raise _QuotaError("Insufficient Balance")
        return _fake_response("ok", prompt_tokens=1)

    monkeypatch.setattr(p, "_call", fake_call)

    p.generate(big_prompt)
    nvidia_prompt = seen_prompts[1][1]
    assert len(nvidia_prompt) < len(big_prompt)
    assert len(nvidia_prompt) >= 4000  # head + tail still present


def test_daily_limit_reached_short_circuits(monkeypatch):
    from backend.core.usage_tracker import usage_tracker

    p = LLMProvider(
        provider="deepseek",
        fallback_order="nvidia",
        deepseek_api_key="sk-ds",
        nvidia_api_key="nv-",
    )
    monkeypatch.setattr(usage_tracker, "_max_conversations_per_day", 1)
    usage_tracker.record_conversation()

    called = {"n": 0}

    def fake_call(provider, prompt):
        called["n"] += 1
        return _fake_response("should not happen")

    monkeypatch.setattr(p, "_call", fake_call)
    result = p.generate("hi")

    assert called["n"] == 0
    assert "daily conversation limit" in result


# ---------------------------------------------------------------------------
# Conversation compactor
# ---------------------------------------------------------------------------


def test_compactor_keeps_recent_and_system():
    c = ConversationCompactor(max_tokens=100, keep_recent=2)
    messages = [
        {"role": "system", "content": "You are Alive."},
        {"role": "user", "content": "A" * 400},
        {"role": "assistant", "content": "B" * 400},
        {"role": "user", "content": "C" * 400},
        {"role": "user", "content": "recent one"},
        {"role": "assistant", "content": "recent two"},
    ]
    original_tokens = estimate_tokens("".join(m["content"] for m in messages))
    compacted, did_compact = c.compact_messages(messages)

    assert did_compact is True
    roles = [m["role"] for m in compacted]
    assert roles[0] == "system"
    assert "recent two" in compacted[-1]["content"]
    compacted_tokens = estimate_tokens("".join(m["content"] for m in compacted))
    assert compacted_tokens <= 100
    assert compacted_tokens < original_tokens // 3


def test_compactor_returns_unchanged_when_within_budget():
    c = ConversationCompactor(max_tokens=1000, keep_recent=2)
    messages = [
        {"role": "user", "content": "short"},
        {"role": "assistant", "content": "reply"},
    ]
    compacted, did_compact = c.compact_messages(messages)
    assert did_compact is False
    assert compacted == messages


def test_compress_prompt_keeps_head_and_tail():
    c = ConversationCompactor()
    head = "SYSTEM INSTRUCTIONS\n" * 50
    conversation = "--- Conversation ---\n" + "\n".join(
        f"User: line {i} " + "x" * 50 for i in range(100)
    ) + "\n\nAlive:"
    prompt = head + "\n" + conversation

    compressed = c.compress_prompt(prompt, max_chars=4000)
    assert len(compressed) <= 4000
    assert "SYSTEM INSTRUCTIONS" in compressed  # head preserved
    assert "Alive:" in compressed  # conversation tail preserved


def test_compress_prompt_unchanged_when_small():
    c = ConversationCompactor()
    prompt = "small prompt"
    assert c.compress_prompt(prompt, max_chars=4000) == prompt


# ---------------------------------------------------------------------------
# Usage tracker
# ---------------------------------------------------------------------------


def test_usage_tracker_budget():
    t = DailyUsageTracker(daily_token_budget=100, max_conversations_per_day=50)
    t.record_tokens("deepseek", 60, 40)
    assert t.budget_reached("deepseek") is True
    assert t.provider_can_serve("deepseek") is False


def test_usage_tracker_exhaustion():
    t = DailyUsageTracker()
    t.mark_exhausted("deepseek", "no balance")
    assert t.is_exhausted("deepseek")
    assert t.exhaustion_reason("deepseek") == "no balance"
    t.clear_exhausted("deepseek")
    assert not t.is_exhausted("deepseek")


def test_usage_tracker_daily_limit():
    t = DailyUsageTracker(max_conversations_per_day=3)
    for _ in range(3):
        t.record_conversation()
    assert t.daily_limit_reached() is True
    assert t.conversations_today() == 3


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


def test_notification_manager_ring_buffer():
    n = NotificationManager(max_entries=5)
    for i in range(10):
        n.notify(f"event {i}", level="info", source="test")
    entries = n.list()
    assert len(entries) == 5
    assert entries[0]["message"] == "event 9"  # newest first
    assert n.list(since=0)  # no crash
