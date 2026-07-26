# NEXT_TASK.md

# Alive – The Mysterious Friend

## Development Queue

Tasks are ordered by priority.

Only work on the highest priority task assigned to you unless instructed otherwise.

---

# 🔴 High Priority

## Person 1 — ✅ All Tasks Complete (Backend Infrastructure + Behaviour Integration)

All Person 1 tasks have been completed and verified:

### Backend Foundation
- ✅ FastAPI application with full configuration management
- ✅ Structured logging via log_config.py
- ✅ Request-timing middleware and CORS support
- ✅ GET /health endpoint
- ✅ POST /chat/completions with OpenAI-compatible format
- ✅ Alive Orchestrator skeleton with 10-step cognitive pipeline
- ✅ Request validation and response formatting
- ✅ Dependency injection for orchestrator
- ✅ Global exception handlers

### API Contract Layer
- ✅ Enhanced Pydantic models with field validators
- ✅ ErrorResponse, Usage, and streaming-ready response models
- ✅ PipelineContext for strongly-typed orchestrator context passing
- ✅ Custom HTTP exception classes (400/401/404/429/500)
- ✅ Service Protocol interfaces for all 8 external cognitive modules
- ✅ Centralized exception handler registration for each HTTP status
- ✅ Conversation length and token estimation checks
- ✅ Response content validation and usage tracking
- ✅ Pluggable module services via constructor injection

### Chat Completions Pipeline
- ✅ Full async request lifecycle (10-step pipeline)
- ✅ RequestContext with contextvars-based request ID propagation
- ✅ RequestContextMiddleware — X-Request-ID header propagation
- ✅ RequestIDFilter — request_id traceability in every log line
- ✅ All 8 external module interfaces fully async
- ✅ Per-step timing and structured lifecycle logging
- ✅ Safe-step wrapper with error recovery
- ✅ Pipeline summary logging

### Production Infrastructure
- ✅ Multi-stage Dockerfile (builder + runtime, non-root user, HEALTHCHECK)
- ✅ docker-compose.yml with healthchecks, bridge network, env passthrough
- ✅ Environment profiles: development/staging/production
- ✅ JSON log formatter for production log aggregation
- ✅ /ready readiness probe endpoint
- ✅ Startup validation warning for missing required settings in production
- ✅ Entrypoint script — auto-selects gunicorn or uvicorn
- ✅ Graceful shutdown timeout configuration
- ✅ Swagger/ReDoc disabled in production

### Behaviour Layer Integration (Person 1 → Person 4)
- ✅ EmotionEngine wired into orchestrator — async, matches Protocol, no adapter needed
- ✅ RelationshipEngine wired into orchestrator — async, matches Protocol, no adapter needed
- ✅ LifeSimulator wired into orchestrator — async, matches Protocol, no adapter needed
- ✅ All 3 modules injected via app.py, alongside existing Person 2 adapters
- ✅ Pipeline verified — emotion classification, relationship updates, life event seeding all fire correctly

---

## Person 2 — ✅ Fully Integrated Into Backend Pipeline

All Person 2 modules have been implemented, tested individually, and integrated asynchronously into the Alive Orchestrator:

- ✅ Identity Engine — Complete. Connected via IdentityEngineAdapter.
- ✅ Prompt Templates — Complete. Consumed by PromptBuilder.
- ✅ Prompt Builder — Complete. Connected via PromptBuilderAdapter with type conversion.
- ✅ LLM Provider — Complete. Connected via LLMProviderAdapter.
- ✅ Response Validator — Complete. Connected via ResponseValidatorAdapter.
- ✅ Person 1 + Person 2 Pipeline Fully Wired — Intelligence layer is active in all 4 pipeline steps.

### Status

**The complete Person 1 → Person 2 → Person 4 pipeline is operational. All 8 cognitive module slots are populated (MemoryEngine awaits Person 3). Behaviour engines fire correctly in the pipeline — emotion classification, relationship updates, and life event seeding are active.**

Remaining work:
- 🟡 Person 3: Implement Memory Vault, embeddings, retrieval, importance scoring.
- 🔵 End-to-end integration testing after all 4 persons are complete.

---

## Person 3

- Design database schema.
- Implement Memory Vault.
- Create embedding pipeline.
- Implement memory retrieval.
- Implement importance scoring.

---

## Person 4 — ✅ Complete (Code + Integration)

All Person 4 modules have been implemented, tested, and integrated into the orchestrator:
- ✅ EmotionEngine — implemented, async Protocol-compatible, wired into orchestrator
- ✅ RelationshipEngine — implemented, async Protocol-compatible, wired into orchestrator
- ✅ LifeSimulator — implemented, async Protocol-compatible, wired into orchestrator
- ✅ MoodManager — canonical mood vocabulary shared across all behaviour modules
- ✅ StateManager — internal behaviour-layer state validation utility

---

# 🟡 Medium Priority

## Person 1 — ✅ All Complete

---

## Person 2

---

## Person 3

- Memory ranking.
- Semantic search optimization.
- Memory compression.

---

## Person 4 — ✅ Complete

---

# 🟢 Low Priority

- Performance optimization.
- Monitoring.
- Logging improvements.
- Additional testing.
- Documentation improvements.

---

# Integration Milestones

## Milestone 1

✅ Documentation Complete

---

## Milestone 2

✅ Backend Running

---

## Milestone 3

⬜ Memory Working

---

## Milestone 4

✅ Behaviour Working (EmotionEngine, RelationshipEngine, LifeSimulator integrated)

---

## Milestone 5

✅ Intelligence Working (IdentityEngine, PromptBuilder, LLMProvider, ResponseValidator integrated)

---

## Milestone 6

⬜ End-to-End Integration

---

## Milestone 7

⬜ Final Testing

---

## Milestone 8

⬜ Ready for Masquerade '26 Submission

---

Every developer should update this file after completing their assigned tasks.

Always keep the highest-priority pending work at the top.