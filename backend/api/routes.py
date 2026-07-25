"""API route definitions.

Defines the OpenAI-compatible /chat/completions endpoint
and optional health-check route.
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/chat/completions")
async def chat_completions():
    """OpenAI-compatible Chat Completions endpoint."""
    pass


@router.get("/health")
async def health():
    """Health check endpoint."""
    pass
