"""Response handler.

Formats orchestrator output into the OpenAI-compatible
Chat Completions response schema and validates output.
"""

import logging
import time
import uuid

from backend.models.responses import (
    ChatCompletionResponse,
    Choice,
    ErrorDetail,
    ErrorResponse,
    ResponseMessage,
    Usage,
)

logger = logging.getLogger(__name__)

MAX_RESPONSE_LENGTH = 4096


class ResponseHandler:
    """Formats internal responses into the OpenAI Chat Completions format."""

    def format_response(
        self,
        content: str,
        model: str,
        request_id: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> ChatCompletionResponse:
        """Wrap the generated content in an OpenAI-compatible response envelope."""
        self._validate_content(content)

        response_id = f"chatcmpl-{request_id}" if request_id else f"chatcmpl-{uuid.uuid4().hex[:12]}"

        return ChatCompletionResponse(
            id=response_id,
            object="chat.completion",
            created=int(time.time()),
            model=model,
            choices=[
                Choice(
                    index=0,
                    message=ResponseMessage(role="assistant", content=content),
                    finish_reason="stop",
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens or self._estimate_tokens(content),
                total_tokens=prompt_tokens + (completion_tokens or self._estimate_tokens(content)),
            ),
        )

    def format_error(self, status_code: int, message: str, details: list | None = None) -> ErrorResponse:
        """Return a standardised error response."""
        return ErrorResponse(error=message, details=details)

    def _validate_content(self, content: str) -> None:
        """Raise if the generated content fails basic validation."""
        if not content or not content.strip():
            raise ValueError("Generated response content is empty.")
        if len(content) > MAX_RESPONSE_LENGTH:
            logger.warning("Response content exceeds max length (%d chars)", len(content))

    def _estimate_tokens(self, text: str) -> int:
        """Roughly estimate token count from character length."""
        return max(1, int(len(text) * 0.25))
