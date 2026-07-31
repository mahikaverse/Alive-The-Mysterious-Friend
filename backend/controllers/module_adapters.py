"""Adapter wrappers for Person 2's cognitive modules.

Bridges the gap between the orchestrator's async Protocol interfaces
and the synchronous implementations in backend/core/ with typed parameters.

Each adapter:
1. Wraps a concrete Person 2 module via composition (no modifications to core/)
2. Converts between dict (orchestrator) and typed-object (module) representations
3. Uses asyncio.to_thread for sync-to-async bridging

Ownership: Person 1 (Backend & Infrastructure)
"""

import asyncio
import logging
from typing import Any

from backend.config.settings import settings as app_settings
from backend.core.identity_engine import IdentityEngine
from backend.core.llm_provider import LLMProvider as ConcreteLLMProvider
from backend.core.prompt_builder import PromptBuilder as ConcretePromptBuilder
from backend.core.response_validator import ResponseValidator as ConcreteResponseValidator
from backend.models.requests import Message
from backend.models.state import EmotionState, LifeContext, PersonaProfile, RelationshipState

logger = logging.getLogger(__name__)


class IdentityEngineAdapter:
    """Async adapter wrapping IdentityEngine (Person 2)."""

    def __init__(self, engine: IdentityEngine | None = None) -> None:
        self._engine = engine or IdentityEngine()
        logger.info("IdentityEngineAdapter ready")

    async def get_persona(self) -> dict[str, Any]:
        persona = await asyncio.to_thread(self._engine.get_persona)
        return persona.model_dump()

    async def update_persona(self, updates: dict[str, Any]) -> None:
        logger.warning("update_persona called — IdentityEngine is read-only")


class PromptBuilderAdapter:
    """Async adapter wrapping PromptBuilder (Person 2).

    Converts orchestrator dicts to the typed Pydantic objects
    that PromptBuilder.build_prompt() expects.
    """

    def __init__(self, builder: ConcretePromptBuilder | None = None) -> None:
        self._builder = builder or ConcretePromptBuilder()
        logger.info("PromptBuilderAdapter ready")

    async def build_prompt(
        self,
        persona: dict[str, Any],
        emotion: dict[str, Any],
        memories: list[Any],
        relationships: dict[str, Any],
        life_events: list[str],
        conversation: list[dict[str, Any]],
    ) -> str:
        typed_persona = PersonaProfile(**persona)
        typed_emotion = EmotionState(**emotion)
        typed_relationship = RelationshipState(**relationships)
        typed_life = LifeContext(recent_activities=life_events)
        typed_conversation = [Message(**m) for m in conversation]

        return await asyncio.to_thread(
            self._builder.build_prompt,
            typed_persona,
            typed_emotion,
            memories,
            typed_relationship,
            typed_life,
            typed_conversation,
        )


class LLMProviderAdapter:
    """Async adapter wrapping LLMProvider (Person 2)."""

    def __init__(self, provider: ConcreteLLMProvider | None = None) -> None:
        self._provider = provider or ConcreteLLMProvider(
            provider=app_settings.llm_provider,
            fallback_order=app_settings.llm_fallback_order,
        )
        logger.info(
            "LLMProviderAdapter ready (provider=%s)",
            app_settings.llm_provider,
        )

    async def generate(self, prompt: str) -> str:
        return await asyncio.to_thread(self._provider.generate, prompt)


class ResponseValidatorAdapter:
    """Async adapter wrapping ResponseValidator (Person 2)."""

    def __init__(self, validator: ConcreteResponseValidator | None = None) -> None:
        self._validator = validator or ConcreteResponseValidator()
        logger.info("ResponseValidatorAdapter ready")

    async def validate(self, response: str, context: dict[str, Any]) -> bool:
        return await asyncio.to_thread(self._validator.validate, response, context)
