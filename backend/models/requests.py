"""Request models.

Pydantic schemas for incoming API requests,
including the OpenAI-compatible Chat Completions format.
"""

from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    """A single message in the conversation."""

    role: str = Field(..., description="One of system, user, or assistant")
    content: str = Field(..., min_length=1, description="Message content")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        normalized = v.lower().strip()
        if normalized not in {"system", "user", "assistant"}:
            raise ValueError(f"Invalid role '{v}'. Must be system, user, or assistant.")
        return normalized


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible Chat Completions request body."""

    model: str = Field(..., min_length=1, description="Model identifier")
    messages: list[Message] = Field(..., min_length=1, description="Conversation messages")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=150, ge=1, le=4096, description="Maximum response tokens")
    stream: bool = Field(default=False, description="Whether to stream the response")

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v: list[Message]) -> list[Message]:
        if not v:
            raise ValueError("messages list must not be empty")
        return v


class ConversationRequest(BaseModel):
    """Internal representation of a parsed conversation request."""

    conversation: list[dict] = Field(default_factory=list, description="Full conversation as dicts")
    current_message: str = Field(default="", description="The latest user message")
    metadata: dict = Field(default_factory=dict, description="Request metadata")
