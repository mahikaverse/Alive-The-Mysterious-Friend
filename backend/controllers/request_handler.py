"""Request handler.

Parses, validates, and enriches incoming API requests
before delegating to the orchestrator.
"""

import logging

from backend.config.settings import settings
from backend.core.conversation_compactor import ConversationCompactor, estimate_tokens
from backend.core.notifications import notification_manager
from backend.models.requests import ChatCompletionRequest, ConversationRequest

logger = logging.getLogger(__name__)

MAX_CONVERSATION_LENGTH = 100
APPROX_TOKENS_PER_CHAR = 0.25


class RequestHandler:
    """Handles incoming request parsing and validation."""

    def __init__(self) -> None:
        self._compactor = ConversationCompactor(
            max_tokens=settings.conversation_token_threshold,
            keep_recent=settings.conversation_keep_recent,
        )

    def parse(self, body: ChatCompletionRequest, request_id: str = "") -> ConversationRequest:
        """Parse a validated ChatCompletionRequest into an internal context."""
        conversation_dicts = [m.model_dump() for m in body.messages]
        self._check_conversation_length(conversation_dicts)

        current = body.messages[-1].content if body.messages else ""

        if settings.compact_conversation_enabled and self._compactor.should_compact(
            conversation_dicts
        ):
            before = sum(estimate_tokens(m["content"]) for m in conversation_dicts)
            conversation_dicts, compacted = self._compactor.compact_messages(
                conversation_dicts
            )
            if compacted:
                after = sum(estimate_tokens(m["content"]) for m in conversation_dicts)
                notification_manager.notify(
                    f"Conversation compacted to save tokens "
                    f"(~{before} tokens -> ~{after} tokens)",
                    level="info",
                    source="request",
                    action="compaction",
                    tokens_saved=before - after,
                )

        logger.info("[%s] parsed %d messages, last role=%s", request_id, len(conversation_dicts), body.messages[-1].role if body.messages else "none")

        return ConversationRequest(
            conversation=conversation_dicts,
            current_message=current,
            metadata={
                "model": body.model,
                "temperature": body.temperature,
                "max_tokens": body.max_tokens,
                "stream": body.stream,
                "request_id": request_id,
            },
        )

    def estimate_token_count(self, text: str) -> int:
        """Roughly estimate the number of tokens in a text string."""
        return max(1, int(len(text) * APPROX_TOKENS_PER_CHAR))

    def _check_conversation_length(self, messages: list[dict]) -> None:
        """Raise if the conversation exceeds the maximum allowed length."""
        if len(messages) > MAX_CONVERSATION_LENGTH:
            raise ValueError(
                f"Conversation exceeds maximum length of {MAX_CONVERSATION_LENGTH} messages."
            )

    def _check_token_limit(self, body: ChatCompletionRequest) -> None:
        """Estimate total tokens and raise if they exceed safety limits."""
        total_chars = sum(len(m.content) for m in body.messages)
        estimated = self.estimate_token_count(total_chars) + body.max_tokens
        if estimated > 8192:
            raise ValueError(
                f"Estimated token usage ({estimated}) exceeds safety limit of 8192 tokens."
            )
