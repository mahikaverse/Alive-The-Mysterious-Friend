"""Alive Orchestrator.

Central coordinator that invokes every cognitive module
in the correct order to generate a response.

The orchestrator accepts optional service instances via constructor
injection. When a service is not provided, a built-in placeholder
behaviour is used so the pipeline can run end-to-end without all
modules being implemented.
"""

import logging
from typing import Optional

from backend.controllers.interfaces import (
    EmotionEngine,
    LLMProvider,
    LifeSimulator,
    MemoryEngine,
    PersonaEngine,
    PromptBuilder,
    RelationshipEngine,
    ResponseValidator,
)
from backend.models.requests import ConversationRequest
from backend.models.state import PipelineContext

logger = logging.getLogger(__name__)


class ConversationController:
    """Orchestrates the full request processing pipeline.

    Inject real implementations of each service as they become
    available. When None, a safe placeholder default is used.
    """

    def __init__(
        self,
        memory: Optional[MemoryEngine] = None,
        emotion: Optional[EmotionEngine] = None,
        relationship: Optional[RelationshipEngine] = None,
        life: Optional[LifeSimulator] = None,
        persona: Optional[PersonaEngine] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        llm: Optional[LLMProvider] = None,
        validator: Optional[ResponseValidator] = None,
    ) -> None:
        self._memory = memory
        self._emotion = emotion
        self._relationship = relationship
        self._life = life
        self._persona = persona
        self._prompt_builder = prompt_builder
        self._llm = llm
        self._validator = validator

    async def process_request(self, request: ConversationRequest) -> dict:
        """Execute the cognitive pipeline and return a response dict."""
        ctx = PipelineContext(
            conversation=request.conversation,
            current_message=request.current_message,
            metadata=request.metadata,
        )

        ctx = await self._step_parse(ctx)
        ctx = await self._step_retrieve_memories(ctx)
        ctx = await self._step_update_emotion(ctx)
        ctx = await self._step_update_relationship(ctx)
        ctx = await self._step_retrieve_life_events(ctx)
        ctx = await self._step_retrieve_persona(ctx)
        prompt = await self._step_build_prompt(ctx)
        raw = await self._step_generate(prompt)
        validated = await self._step_validate(raw, ctx)
        await self._step_store_memories(ctx, validated)

        return {"content": validated}

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    async def _step_parse(self, ctx: PipelineContext) -> PipelineContext:
        logger.info("parsing conversation")
        return ctx

    async def _step_retrieve_memories(self, ctx: PipelineContext) -> PipelineContext:
        logger.info("retrieving memories")
        if self._memory is not None:
            ctx.memories = self._memory.retrieve(ctx.conversation, ctx.current_message)
        return ctx

    async def _step_update_emotion(self, ctx: PipelineContext) -> PipelineContext:
        logger.info("updating emotion")
        if self._emotion is not None:
            result = self._emotion.update(
                ctx.emotion.model_dump(),
                ctx.current_message,
                ctx.conversation,
            )
            ctx.emotion = ctx.emotion.__class__(**result)
        return ctx

    async def _step_update_relationship(self, ctx: PipelineContext) -> PipelineContext:
        logger.info("updating relationship")
        if self._relationship is not None:
            result = self._relationship.update(ctx.current_message, ctx.emotion.model_dump())
            ctx.relationship = ctx.relationship.__class__(**result)
        return ctx

    async def _step_retrieve_life_events(self, ctx: PipelineContext) -> PipelineContext:
        logger.info("retrieving life events")
        if self._life is not None:
            ctx.life_events.recent_activities = self._life.get_recent_events()
        return ctx

    async def _step_retrieve_persona(self, ctx: PipelineContext) -> PipelineContext:
        logger.info("retrieving persona")
        if self._persona is not None:
            result = self._persona.get_persona()
            ctx.persona = ctx.persona.__class__(**result)
        return ctx

    async def _step_build_prompt(self, ctx: PipelineContext) -> str:
        logger.info("building prompt")
        if self._prompt_builder is not None:
            return self._prompt_builder.build_prompt(
                persona=ctx.persona.model_dump(),
                emotion=ctx.emotion.model_dump(),
                memories=ctx.memories,
                relationships=ctx.relationship.model_dump(),
                life_events=ctx.life_events.recent_activities,
                conversation=ctx.conversation,
            )
        return f"Continue the conversation naturally.\nUser: {ctx.current_message}\nAlive:"

    async def _step_generate(self, prompt: str) -> str:
        logger.info("generating response")
        if self._llm is not None:
            return self._llm.generate(prompt)
        return "Hey! It's nice to meet you."

    async def _step_validate(self, response: str, ctx: PipelineContext) -> str:
        logger.info("validating response")
        if self._validator is not None:
            passed = self._validator.validate(response, ctx.model_dump())
            if not passed:
                logger.warning("response failed validation")
        return response

    async def _step_store_memories(self, ctx: PipelineContext, response: str) -> None:
        logger.info("storing memories")
        if self._memory is not None:
            self._memory.store(ctx.conversation, response)
