"""API route definitions.

Defines the OpenAI-compatible /chat/completions endpoint
and health-check route.
"""

import time

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_conversation_controller
from backend.config.settings import settings
from backend.controllers.conversation_controller import ConversationController
from backend.controllers.request_handler import RequestHandler
from backend.controllers.response_handler import ResponseHandler
from backend.models.requests import ChatCompletionRequest
from backend.models.responses import ChatCompletionResponse, ErrorResponse

router = APIRouter()

START_TIME = time.time()


@router.get(
    "/health",
    summary="Health check",
    description="Returns service status, version, and uptime.",
)
async def health() -> dict:
    """Health check endpoint returning service status."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - START_TIME),
        "model": settings.model_name,
    }


@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Chat Completions",
    description="OpenAI-compatible Chat Completions endpoint.",
)
async def chat_completions(
    body: ChatCompletionRequest,
    controller: ConversationController = Depends(get_conversation_controller),
) -> ChatCompletionResponse:
    """OpenAI-compatible Chat Completions endpoint."""
    request_handler = RequestHandler()
    response_handler = ResponseHandler()

    parsed = request_handler.parse(body)
    orchestrator_result = await controller.process_request(parsed)
    response = response_handler.format_response(
        content=orchestrator_result["content"],
        model=body.model,
    )

    return response
