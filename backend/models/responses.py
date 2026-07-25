"""Response models.

Pydantic schemas for API responses,
matching the OpenAI Chat Completions format.
"""

from pydantic import BaseModel


class ResponseMessage(BaseModel):
    """A single response message from the assistant."""

    role: str
    content: str


class Choice(BaseModel):
    """A single choice in the completion response."""

    index: int
    message: ResponseMessage
    finish_reason: str


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible Chat Completions response body."""

    id: str
    object: str
    created: int
    model: str
    choices: list[Choice]


class ErrorResponse(BaseModel):
    """Standardised API error response."""

    error: str
