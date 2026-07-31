"""Test an LLM API key and report token usage.

Usage:
    python scripts/test_provider.py deepseek
    python scripts/test_provider.py nvidia
    python scripts/test_provider.py openrouter
    python scripts/test_provider.py grok
    python scripts/test_provider.py all

Sends a short prompt to each requested provider (or the whole failover
chain) and prints the response, per-provider token usage, and the
current daily usage report.  No API key is ever printed.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from backend.core.llm_provider import LLMProvider
from backend.core.usage_tracker import usage_tracker

TEST_PROMPT = (
    "This is a connectivity test. Reply with exactly one short sentence "
    "confirming you are working."
)


def main() -> None:
    target = (sys.argv[1] if len(sys.argv) > 1 else "all").strip().lower()

    if target in ("all", "chain"):
        provider = LLMProvider()
        print(f"\nActive provider chain: {provider._chain}")
        for name in provider._chain:
            _test(name)
    elif target == "deepseek":
        _test("deepseek")
    elif target == "nvidia":
        _test("nvidia")
    elif target == "openrouter":
        _test("openrouter")
    elif target == "grok":
        _test("grok")
    elif target == "openai":
        _test("openai")
    elif target == "gemini":
        _test("gemini")
    else:
        print(f"Unknown target '{target}'. Use: deepseek | nvidia | openrouter | grok | openai | gemini | all")
        sys.exit(2)

    print("\n" + "=" * 60)
    print("Daily usage report:")
    import json

    print(json.dumps(usage_tracker.snapshot(), indent=2))


def _test(provider_name: str) -> None:
    """Test a single provider with a fresh LLMProvider instance."""
    print("\n" + "=" * 60)
    print(f"Testing provider: {provider_name}")
    print("=" * 60)

    llm = LLMProvider(provider=provider_name)
    try:
        response = llm.generate(TEST_PROMPT)
        print(f"\n[OK] Response ({len(response)} chars): {response[:200]}")
        report = usage_tracker.snapshot()
        prov = report["providers"].get(provider_name, {})
        print(f"\nUsage: {prov.get('tokens', {}).get('total', 0)} tokens "
              f"across {prov.get('calls', 0)} call(s)")
    except ValueError as exc:
        print(f"\n[SKIP] {exc}")
    except RuntimeError as exc:
        print(f"\n[FAIL] {exc}")


if __name__ == "__main__":
    main()
