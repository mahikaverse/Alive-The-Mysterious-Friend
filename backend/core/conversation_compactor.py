"""Conversation and prompt compaction.

Reduces token consumption without dropping context that matters for
quality:

- ``estimate_tokens`` — cheap token estimate (chars / 4).
- ``compact_messages`` — trims an OpenAI-style message list: system
  messages are always kept, the most recent turns are kept verbatim,
  and older turns are truncated to fit within a token budget.
- ``compress_prompt`` — compresses the single master prompt string by
  keeping the system/instruction head intact and trimming the older
  conversation tail, so fallback calls after quota exhaustion still
  have the context they need at a fraction of the tokens.
"""

import logging

logger = logging.getLogger(__name__)

TOKENS_PER_CHAR: float = 0.25
CHARS_PER_TOKEN: int = 4

_CONVERSATION_MARKER: str = "--- Conversation ---"
_COMPACTION_NOTE: str = (
    "[Earlier conversation was compacted to save tokens. "
    "Keep the context in mind but respond naturally to the latest messages.]"
)


def estimate_tokens(text: str) -> int:
    """Roughly estimate the number of tokens in a text string."""
    return max(1, int(len(text) * TOKENS_PER_CHAR))


def _message_text(message: dict) -> str:
    """Return the content of a message dict, tolerating missing keys."""
    return message.get("content", "") if isinstance(message, dict) else str(message)


def _message_tokens(message: dict) -> int:
    """Estimate tokens for a single message dict."""
    return estimate_tokens(_message_text(message))


class ConversationCompactor:
    """Compacts conversation histories and prompts to save tokens.

    Parameters
    ----------
    max_tokens : int
        Default estimated-token budget used by ``compact_messages``.
    keep_recent : int
        Number of most recent non-system messages kept verbatim.
    """

    def __init__(
        self,
        max_tokens: int = 6000,
        keep_recent: int = 10,
    ) -> None:
        self._max_tokens: int = max_tokens
        self._keep_recent: int = keep_recent
        logger.info(
            "ConversationCompactor ready (max_tokens=%d, keep_recent=%d)",
            max_tokens,
            keep_recent,
        )

    # ------------------------------------------------------------------
    # Message-list compaction (request layer)
    # ------------------------------------------------------------------

    def should_compact(self, messages: list[dict]) -> bool:
        """Return whether ``messages`` exceed the token budget."""
        return sum(_message_tokens(m) for m in messages) > self._max_tokens

    def compact_messages(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
        keep_recent: int | None = None,
    ) -> tuple[list[dict], bool]:
        """Compress a message list to fit the token budget.

        System messages are always preserved.  The ``keep_recent`` most
        recent non-system messages are kept verbatim.  Older messages
        are truncated (longer content cut first) until the total fits
        ``max_tokens``.

        Parameters
        ----------
        messages : list[dict]
            OpenAI-style messages with ``role`` and ``content`` keys.
        max_tokens : int | None
            Token budget.  Falls back to the configured value.
        keep_recent : int | None
            Most-recent messages kept verbatim.  Falls back to the
            configured value.

        Returns
        -------
        tuple[list[dict], bool]
            The compacted message list and whether compaction occurred.
        """
        budget = max_tokens or self._max_tokens
        recent_count = keep_recent or self._keep_recent

        total = sum(_message_tokens(m) for m in messages)
        if total <= budget:
            return list(messages), False

        system = [m for m in messages if m.get("role") == "system"]
        others = [m for m in messages if m.get("role") != "system"]

        if not others:
            return list(messages), False

        recent = others[-recent_count:] if recent_count > 0 else []
        old = others[:-recent_count] if recent_count > 0 else others

        system_tokens = sum(_message_tokens(m) for m in system)
        recent_tokens = sum(_message_tokens(m) for m in recent)

        remaining_chars = max(
            0,
            budget * CHARS_PER_TOKEN
            - system_tokens * CHARS_PER_TOKEN
            - recent_tokens * CHARS_PER_TOKEN,
        )
        old_chars = sum(len(_message_text(m)) for m in old)

        kept_old: list[dict] = []

        # Reserve room for the compaction note so the budget is respected.
        if old and remaining_chars > len(_COMPACTION_NOTE):
            remaining_chars -= len(_COMPACTION_NOTE)

        for message in old:
            if remaining_chars <= 0:
                break
            text = _message_text(message)
            if len(text) <= remaining_chars:
                kept_old.append(dict(message))
                remaining_chars -= len(text)
            else:
                if remaining_chars >= 20:
                    trimmed = dict(message)
                    trimmed["content"] = text[:remaining_chars] + "…"
                    kept_old.append(trimmed)
                remaining_chars = 0

        compacted: list[dict] = []
        if kept_old:
            note = {
                "role": "system",
                "content": _COMPACTION_NOTE,
            }
            compacted.append(note)
            compacted.extend(kept_old)

        compacted.extend(recent)

        logger.info(
            "Conversation compacted: %d messages, %d chars -> %d messages, %d chars (budget=%d tokens)",
            len(messages),
            old_chars,
            len(compacted),
            sum(len(_message_text(m)) for m in compacted),
            budget,
        )
        return compacted, True

    # ------------------------------------------------------------------
    # Master-prompt compression (fallback path)
    # ------------------------------------------------------------------

    def compress_prompt(
        self,
        prompt: str,
        max_chars: int | None = None,
        keep_tail_lines: int = 40,
    ) -> str:
        """Compress a master prompt string to fit ``max_chars``.

        The system/instruction head is preserved as much as possible
        and the conversation section is reduced to its most recent
        lines, so a fallback provider still receives full instructions
        plus the latest turns.

        Parameters
        ----------
        prompt : str
        max_chars : int | None
            Maximum prompt length in characters.  Falls back to half
            the original length.
        keep_tail_lines : int
            Maximum number of conversation lines to retain.
        """
        if max_chars is None:
            max_chars = max(4000, len(prompt) // 2)

        if len(prompt) <= max_chars:
            return prompt

        head, sep, tail = prompt.partition(_CONVERSATION_MARKER)

        if sep:
            head_budget = int(max_chars * 0.6)
            tail_budget = max_chars - head_budget

            if len(head) > head_budget:
                head = self._trim_middle(head, head_budget)

            tail_lines = [line for line in tail.splitlines() if line.strip()]
            kept = tail_lines[-keep_tail_lines:]
            tail = "\n".join(kept)
            if len(tail) > tail_budget:
                tail = self._trim_middle(tail, tail_budget)

            compressed = head.rstrip() + "\n" + _CONVERSATION_MARKER + "\n" + tail + "\n\nAlive:"
        else:
            compressed = self._trim_middle(prompt, max_chars)

        logger.info(
            "Prompt compressed: %d chars -> %d chars (%.1f%% saved)",
            len(prompt),
            len(compressed),
            (1 - len(compressed) / len(prompt)) * 100,
        )
        return compressed

    @staticmethod
    def _trim_middle(text: str, max_chars: int) -> str:
        """Keep the head and tail of ``text`` within ``max_chars``."""
        if len(text) <= max_chars:
            return text
        keep = max(40, max_chars // 2)
        head = text[:keep]
        tail = text[-(max_chars - keep):]
        return f"{head}\n[…] trimmed for token budget …\n{tail}"


compactor = ConversationCompactor()
