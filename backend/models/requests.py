"""Request models.

Pydantic schemas for incoming API requests,
including the OpenAI-compatible Chat Completions format.
"""

from pydantic import BaseModel


class Message(BaseModel):
    """A single message in the conversation."""

    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible Chat Completions request body."""

    model: str
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int = 300


class ConversationRequest(BaseModel):
    """Internal representation of a parsed conversation request."""

    conversation: list[Message]
    current_message: str
    metadata: dict = {}
