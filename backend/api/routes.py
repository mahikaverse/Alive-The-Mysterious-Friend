"""API route definitions.

Defines the OpenAI-compatible /chat/completions endpoint,
health-check, and readiness probe routes.
"""

import time

from fastapi import APIRouter, Depends
from starlette.requests import Request

from backend.api.dependencies import get_conversation_controller
from backend.core.notifications import notification_manager
from backend.core.usage_tracker import usage_tracker
from backend.utils.metrics import metrics_collector
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
    """Lightweight liveness probe — returns immediately if the process is alive."""
    return {
        "status": "ok",
        "version": "1.1.0",
        "uptime_seconds": int(time.time() - START_TIME),
        "model": settings.model_name,
        "environment": settings.environment,
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Indicates whether the application is ready to serve traffic.",
)
async def ready() -> dict:
    """Readiness probe — confirms the orchestrator and core services are initialised."""
    return {
        "status": "ready",
        "version": "1.1.0",
        "orchestrator": "initialised",
    }


@router.get(
    "/metrics",
    summary="Application metrics",
    description="In-memory request metrics for monitoring and diagnostics.",
)
async def metrics() -> dict:
    """Return a snapshot of request metrics collected since startup."""
    return metrics_collector.snapshot()


@router.get(
    "/usage",
    summary="LLM usage report",
    description="Per-provider token usage, call counts, exhaustion state, and today's conversation count.",
)
async def usage() -> dict:
    """Return the daily LLM usage and provider health report."""
    return usage_tracker.snapshot()


@router.get(
    "/notifications",
    summary="Recent notifications",
    description="Recent runtime notifications (provider exhaustion, compaction, daily limit).",
)
async def notifications(since: int | None = None, limit: int = 50) -> dict:
    """Return recent notifications, newest first."""
    return {
        "notifications": notification_manager.list(since=since, limit=limit),
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
    request: Request,
    body: ChatCompletionRequest,
    controller: ConversationController = Depends(get_conversation_controller),
) -> ChatCompletionResponse:
    """OpenAI-compatible Chat Completions endpoint."""
    rid = request.state.request_id
    request_handler = RequestHandler()
    response_handler = ResponseHandler()

    parsed = request_handler.parse(body, request_id=rid)
    orchestrator_result = await controller.process_request(parsed)

    response = response_handler.format_response(
        content=orchestrator_result["content"],
        model=body.model,
        request_id=rid,
    )

    return response
