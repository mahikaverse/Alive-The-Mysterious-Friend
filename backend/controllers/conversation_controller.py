"""Alive Orchestrator.

Central coordinator that invokes every cognitive module
in the correct order to generate a response.

Lifecycle (per ARCHITECTURE.md and INTEGRATION.md):
  1. Parse conversation
  2. Retrieve memories       (MemoryEngine)
  3. Update emotion           (EmotionEngine)
  4. Update relationship      (RelationshipEngine)
  5. Retrieve life events     (LifeSimulator)
  6. Retrieve persona         (PersonaEngine)
  7. Build master prompt      (PromptBuilder)
  8. Generate response        (LLMProvider)
  9. Validate response        (ResponseValidator)
  10. Store new memories      (MemoryEngine)

Every step is wrapped in error handling so that a single
module failure never crashes the entire pipeline.
"""

import asyncio
import logging
import time
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
from backend.utils.request_context import get_current_request_id

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
        self._background_tasks: set[asyncio.Task] = set()

    async def process_request(self, request: ConversationRequest) -> dict:
        """Execute the cognitive pipeline and return a response dict."""
        pipeline_start = time.perf_counter()
        rid = get_current_request_id()

        ctx = PipelineContext(
            request_id=rid,
            conversation=request.conversation,
            current_message=request.current_message,
            metadata=request.metadata,
        )

        logger.info("[%s] pipeline started — %d messages", rid, len(ctx.conversation))

        ctx = await self._safe_step("parse", ctx, self._step_parse)
        ctx = await self._safe_step("retrieve_memories", ctx, self._step_retrieve_memories)
        ctx = await self._safe_step("update_emotion", ctx, self._step_update_emotion)
        ctx = await self._safe_step("update_relationship", ctx, self._step_update_relationship)
        ctx = await self._safe_step("retrieve_life_events", ctx, self._step_retrieve_life_events)
        ctx = await self._safe_step("retrieve_persona", ctx, self._step_retrieve_persona)
        prompt = await self._safe_step("build_prompt", ctx, self._step_build_prompt, is_prompt=True)
        raw = await self._safe_step("generate", ctx, self._step_generate, is_prompt=True, prompt_arg=prompt)
        validated = await self._safe_step("validate", ctx, self._step_validate, is_prompt=True, prompt_arg=raw)
        self._schedule_memory_store(ctx, validated)

        elapsed = time.perf_counter() - pipeline_start
        logger.info(
            "[%s] pipeline finished — %.4fs total — response %d chars",
            rid, elapsed, len(validated),
        )

        return {"content": validated}

    # ------------------------------------------------------------------
    # Safe step wrapper
    # ------------------------------------------------------------------

    async def _safe_step(self, name: str, ctx: PipelineContext, step_fn, is_prompt: bool = False, prompt_arg: str = "") -> PipelineContext | str:
        """Execute a pipeline step with timing and error handling.

        If the step raises, the error is logged and a fallback value
        is returned so the pipeline can continue.
        """
        rid = ctx.request_id or get_current_request_id()
        start = time.perf_counter()
        try:
            if is_prompt:
                result = await step_fn(ctx, prompt_arg)
            else:
                result = await step_fn(ctx)
            elapsed = time.perf_counter() - start
            logger.info("[%s] step %s OK (%.4fs)", rid, name, elapsed)
            return result
        except Exception:
            elapsed = time.perf_counter() - start
            logger.exception("[%s] step %s FAILED after %.4fs — using fallback", rid, name, elapsed)
            if is_prompt:
                return prompt_arg or "[fallback response]"
            return ctx

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    def _schedule_memory_store(self, ctx: PipelineContext, response_text: str) -> None:
        """Persist memories in the background so storage never delays the reply.

        Memory storage performs an embedding API call; waiting on it adds
        latency to every response. Running it as a background task returns
        the reply to the user immediately after generation.
        """
        if self._memory is None:
            return

        async def _store() -> None:
            try:
                await self._step_store_memories(ctx, response_text)
            except Exception:
                logger.exception(
                    "[%s] background memory storage failed",
                    ctx.request_id or get_current_request_id(),
                )

        task = asyncio.create_task(_store())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _step_parse(self, ctx: PipelineContext) -> PipelineContext:
        return ctx

    async def _step_retrieve_memories(self, ctx: PipelineContext) -> PipelineContext:
        if self._memory is not None:
            ctx.memories = await self._memory.retrieve(ctx.conversation, ctx.current_message)
        return ctx

    async def _step_update_emotion(self, ctx: PipelineContext) -> PipelineContext:
        if self._emotion is not None:
            result = await self._emotion.update(
                ctx.emotion.model_dump(),
                ctx.current_message,
                ctx.conversation,
            )
            ctx.emotion = ctx.emotion.__class__(**result)
        return ctx

    async def _step_update_relationship(self, ctx: PipelineContext) -> PipelineContext:
        if self._relationship is not None:
            result = await self._relationship.update(
                ctx.current_message,
                ctx.emotion.model_dump(),
            )
            ctx.relationship = ctx.relationship.__class__(**result)
        return ctx

    async def _step_retrieve_life_events(self, ctx: PipelineContext) -> PipelineContext:
        if self._life is not None:
            ctx.life_events.recent_activities = await self._life.get_recent_events()
        return ctx

    async def _step_retrieve_persona(self, ctx: PipelineContext) -> PipelineContext:
        if self._persona is not None:
            result = await self._persona.get_persona()
            ctx.persona = ctx.persona.__class__(**result)
        return ctx

    async def _step_build_prompt(self, ctx: PipelineContext, _unused: str = "") -> str:
        if self._prompt_builder is not None:
            emotion_dict = ctx.emotion.model_dump()
            relationship_dict = ctx.relationship.model_dump()
            persona_dict = ctx.persona.model_dump()
            return await self._prompt_builder.build_prompt(
                persona=persona_dict,
                emotion=emotion_dict,
                memories=ctx.memories,
                relationships=relationship_dict,
                life_events=ctx.life_events.recent_activities,
                conversation=ctx.conversation,
            )
        return f"Continue the conversation naturally.\nUser: {ctx.current_message}\nAlive:"

    async def _step_generate(self, ctx: PipelineContext, prompt: str = "") -> str:
        if self._llm is not None:
            try:
                return await self._llm.generate(prompt)
            except Exception as exc:
                logger.warning(
                    "[%s] LLM generation failed: %s — using fallback response",
                    ctx.request_id, exc,
                )
                return "Hey! It's nice to meet you. How are you doing today?"
        return "Hey! It's nice to meet you."

    async def _step_validate(self, ctx: PipelineContext, response_text: str = "") -> str:
        if self._validator is not None:
            passed = await self._validator.validate(response_text, ctx.model_dump())
            if not passed:
                logger.warning("[%s] response failed validation — using anyway", ctx.request_id)
        return response_text

    async def _step_store_memories(self, ctx: PipelineContext, response_text: str = "") -> None:
        if self._memory is not None:
            await self._memory.store(ctx.conversation, response_text)
