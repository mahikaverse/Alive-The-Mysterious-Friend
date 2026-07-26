"""Response models.

Pydantic schemas for API responses,
matching the OpenAI Chat Completions format.
"""

from pydantic import BaseModel, Field


class ResponseMessage(BaseModel):
    """A single response message from the assistant."""

    role: str = Field(default="assistant", description="Message role")
    content: str = Field(..., description="Response content")


class Choice(BaseModel):
    """A single choice in the completion response."""

    index: int = Field(0, description="Choice index")
    message: ResponseMessage = Field(..., description="Response message")
    finish_reason: str = Field("stop", description="Reason the response finished")


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(0, description="Tokens used in the prompt")
    completion_tokens: int = Field(0, description="Tokens used in the completion")
    total_tokens: int = Field(0, description="Total tokens used")


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible Chat Completions response body."""

    id: str = Field(..., description="Unique completion identifier")
    object: str = Field("chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used")
    choices: list[Choice] = Field(..., description="Completion choices")
    usage: Usage | None = Field(None, description="Token usage statistics")


class ErrorDetail(BaseModel):
    """A single error detail."""

    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error description")


class ErrorResponse(BaseModel):
    """Standardised API error response."""

    error: str = Field(..., description="Error summary")
    details: list[ErrorDetail] | None = Field(None, description="Detailed error information")
