"""Request handler.

Parses, validates, and enriches incoming API requests
before delegating to the orchestrator.
"""

import logging

from backend.models.requests import ChatCompletionRequest, ConversationRequest

logger = logging.getLogger(__name__)

MAX_CONVERSATION_LENGTH = 100
APPROX_TOKENS_PER_CHAR = 0.25


class RequestHandler:
    """Handles incoming request parsing and validation."""

    def parse(self, body: ChatCompletionRequest) -> ConversationRequest:
        """Parse a validated ChatCompletionRequest into an internal context."""
        conversation_dicts = [m.model_dump() for m in body.messages]
        self._check_conversation_length(conversation_dicts)

        current = body.messages[-1].content if body.messages else ""

        return ConversationRequest(
            conversation=conversation_dicts,
            current_message=current,
            metadata={
                "model": body.model,
                "temperature": body.temperature,
                "max_tokens": body.max_tokens,
                "stream": body.stream,
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
