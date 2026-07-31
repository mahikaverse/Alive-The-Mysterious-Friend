# CHANGELOG.md

# Alive – The Mysterious Friend

## Project Changelog

---

# Version 1.1

## 1 August 2026

### Conversation Quality & Latency

✅ Shortened replies to 1–3 sentences (`max_tokens` default 300 → 150; response validator max length 1500 → 800)

✅ Replaced written stage directions (`*smiles*`) with emojis, used only when they genuinely add tone

✅ Added Hinglish support — Alive mirrors the user's language (English → English, Hinglish → Hinglish, mixed → mixed)

✅ Prompt templates updated (system prompt, personality, instructions, examples, safety) for natural, casual tone

### Performance

✅ Moved memory storage to a background task — OpenAI embedding round-trip no longer delays the reply

✅ Tuned LLM timeout (30s) and retries (2); no hard deadline enforced so slow models still answer correctly

### Infra

✅ Dockerfile: create and chown `/app/chroma_db` for the non-root container user

✅ Entrypoint: log-level value lowercased for uvicorn

### Docs & Config

✅ Updated README (conversation style section, tech stack providers, env example, docs table)

✅ Updated API, INTEGRATION, MANUAL_TESTING_GUIDE, PROJECT_STATUS docs

✅ Postman collection `max_tokens` example → 150

✅ `.env.example` reflects `MAX_TOKENS=150` and multi-provider keys

✅ Removed unused `faiss-cpu` from requirements.txt / pyproject.toml

✅ `.gitignore`: added `.pytest_cache/`, coverage, and cache entries

---

# Version 1.0

## 26 July 2026

### Documentation

✅ Created AI_RULES.md

✅ Created ARCHITECTURE.md

✅ Created API.md

✅ Created INTEGRATION.md

✅ Created PLAN_PERSON_1.md

✅ Created PLAN_PERSON_2.md

✅ Created PLAN_PERSON_3.md

✅ Created PLAN_PERSON_4.md

✅ Created PROMPT_PERSON_1.md

✅ Created PROMPT_PERSON_2.md

✅ Created PROMPT_PERSON_3.md

✅ Created PROMPT_PERSON_4.md

---

## 25 July 2026

### Backend Foundation (Person 1)

✅ Created FastAPI application with full configuration management
✅ Implemented structured logging via log_config.py
✅ Added request-timing middleware and CORS support
✅ Implemented GET /health endpoint
✅ Implemented POST /chat/completions with OpenAI-compatible format
✅ Built Alive Orchestrator skeleton with 10-step cognitive pipeline
✅ Created request validation and response formatting
✅ Added dependency injection for orchestrator
✅ Set up global exception handlers
✅ Verified server starts and both endpoints respond correctly

### API Contract Layer (Person 1)

✅ Enhanced Pydantic models with field validators (role, temperature, max_tokens)
✅ Added ErrorResponse, Usage, and streaming-ready response models
✅ Created PipelineContext for strongly-typed orchestrator context passing
✅ Implemented custom HTTP exception classes (400/401/404/429/500)
✅ Created service Protocol interfaces for all 8 external cognitive modules
✅ Added centralized exception handler registration for each HTTP status
✅ Enhanced request handler with conversation length and token estimation checks
✅ Enhanced response handler with content validation and usage tracking
✅ Wired orchestrator with constructor injection for pluggable module services
✅ Verified all endpoints and error rejection paths

### Chat Completions Pipeline (Person 1)

✅ Implemented full async request lifecycle in Alive Orchestrator (10-step pipeline)
✅ Created RequestContext with contextvars-based request ID propagation
✅ Added RequestContextMiddleware — generates/accepts X-Request-ID, sets response header
✅ Added RequestIDFilter — every log line includes [request_id] for traceability
✅ Made all 8 external module interfaces fully async
✅ Added per-step timing and structured lifecycle logging
✅ Implemented safe-step wrapper with error recovery — per-step try/except with fallback values
✅ Added pipeline summary logging (total time, response length)
✅ Response ID derived from request ID for correlation (chatcmpl-{request_id})
✅ Verified custom X-Request-ID header propagation end-to-end

### Production Infrastructure (Person 1)

✅ Built multi-stage Dockerfile (builder + runtime, non-root user, HEALTHCHECK)
✅ Created docker-compose.yml with healthchecks, bridge network, env passthrough
✅ Added environment profiles: development/staging/production with validation
✅ Added JSON log formatter for production log aggregation
✅ Created /ready readiness probe endpoint with orchestrator status
✅ Improved /health to include environment label
✅ Added startup validation warning for missing required settings in production
✅ Created scripts/entrypoint.sh — auto-selects gunicorn (production) or uvicorn --reload (dev)
✅ Centralized metadata (__app_name__, __version__, __description__) in backend/__init__.py
✅ Added graceful shutdown timeout configuration
✅ Disabled Swagger/ReDoc docs in production
✅ Added gunicorn as production ASGI server with uvicorn workers
✅ Expanded .env.example with all documented variables and grouped sections
✅ Verified all three endpoints (/health, /ready, /chat/completions) work

### Intelligence Layer — Code (Person 2)

✅ Implemented IdentityEngine (backend/core/identity_engine.py)
✅ Implemented PromptTemplates (backend/core/prompt_templates.py)
✅ Implemented PromptBuilder (backend/core/prompt_builder.py)
✅ Implemented LLMProvider (backend/core/llm_provider.py)
✅ Implemented ResponseValidator (backend/core/response_validator.py)
✅ Created prompt template files (backend/prompts/*.md)

- system_prompt.md: core identity and purpose
- personality.md: how personality manifests in responses
- safety.md: guardrails and behavioural boundaries
- instructions.md: step-by-step response generation process
- examples.md: example conversations demonstrating desired style
- PromptTemplates loads, caches, and serves markdown templates
- Pure declarative templates — no inline placeholders or logic
- Dependency injection for templates directory (testable, deployable)
- Cache with reload_all() for runtime updates
- builder.build_prompt() assembles system, memory, context, instructions, examples, conversation blocks
- builder._build_system_block(persona, emotion) — loads templates + injects persona/emotion data
- builder._build_memory_block(memories) — formats relevant memories as bullet list
- builder._build_context_block(relationships, life_events) — relationship state + life context
- builder._build_conversation_block(conversation) — formats message history ending with "Alive:"
- PromptTemplates injected via constructor for testability
- Type-hinted parameters use shared models (PersonaProfile, EmotionState, RelationshipState, LifeContext, Message)
- LLMProvider.generate() accepts MasterPrompt (str) and returns response (str)
- Provider-agnostic design — routes to OpenAI or Gemini via _call_openai / _call_gemini
- Provider selected via LLM_PROVIDER env var (openai | gemini)
- Backend model names from OPENAI_MODEL / GEMINI_MODEL env vars
- Timeout: 30s, retries: 2 on transient failures (exponential backoff for Gemini)
- Dependency injection for all configuration values (testable)
- Clear validation errors for missing API keys or model names
- ResponseValidator.validate(response, context) returns bool — True if all checks pass
- check_personality_consistency() — detects AI disclosure phrases
- check_emotional_consistency() — mood-tone match via keyword heuristics
- check_response_length() — enforces min/max length bounds
- check_contradictions() — internal sentence contradictions + external fact negation
- check_hallucinations() — AI disclosures, physical/real-time claims, database claims
- Lightweight MVP heuristics; no external LLM calls for validation
- Configurable max_response_length via constructor injection

### Intelligence Layer — Integration

✅ Completed Person 2 — Intelligence Layer Integration (Person 2)

- Reviewed all 5 module interfaces for compatibility
- Verified data flow: IdentityEngine → PromptBuilder → LLMProvider → ResponseValidator
- All data types compatible (PersonaProfile, str, bool)
- Created integration test demonstrating complete pipeline with mock data
- Removed unused constant _SENTENCE_ENDINGS from response_validator.py
- No architectural changes required — modules integrate cleanly

- Thin, read-only abstraction over PersonaProfile
- Dependency injection via constructor (data-source agnostic)
- Deep copies on get_persona() to prevent external mutation
- Warning log when no external persona source is configured
- Public API: get_persona(), get_writing_style(), get_personality_traits(), to_dict()
- No personality data invented — uses only the provided or default PersonaProfile

---

### Intelligence Layer — Integrated Into Orchestrator (Person 1)

✅ Created adapter wrappers in controllers/module_adapters.py (no modifications to Person 2's code):
- IdentityEngineAdapter — async wrapper, returns dict from PersonaProfile
- PromptBuilderAdapter — converts orchestrator dicts to typed Pydantic objects
- LLMProviderAdapter — sync-to-async bridge via asyncio.to_thread
- ResponseValidatorAdapter — sync-to-async bridge via asyncio.to_thread
- All adapters wired into ConversationController via app.py DI

### Behaviour Layer — Integrated Into Orchestrator (Person 1)

✅ Wired Person 4 behaviour modules into ConversationController via app.py (no adapters needed):
- EmotionEngine — async, matches EmotionEngine Protocol, injected directly
- RelationshipEngine — async, matches RelationshipEngine Protocol, injected directly
- LifeSimulator — async, matches LifeSimulator Protocol, injected directly
- No adapter wrappers required — Person 4 modules already implement async Protocols
- All 3 modules injected into orchestrator alongside existing Person 2 modules
- Verified: pipeline executes all 10 steps with behaviour modules active
- Verified: emotion stimulus classification, relationship metric updates, and life event seeding all fire correctly in the pipeline
- Graceful fallback on LLM step when no API key is configured (expected dev behavior)

### Project Version Bump

✅ Project version updated to v1.1
✅ Overall progress updated to 80%
✅ Behaviour modules marked complete and integrated in PROJECT_STATUS.md

### Medium-Priority Features (Person 1)

✅ Implemented `AuthMiddleware` in `backend/api/middleware.py`:
- Checks `Authorization: Bearer <key>` on all non-public endpoints
- No-op when `API_KEY` env var is empty (backward compatible)
- Public paths: /health, /ready, /metrics, /docs, /redoc, /openapi.json
- Returns 401 with standard error format on missing/invalid key
- Registered after RequestContextMiddleware for request_id traceability

✅ Implemented `MetricsCollector` in `backend/utils/metrics.py`:
- Thread-safe in-memory counters: total requests, errors, latency
- Requests broken down by path and status code
- Averaged latency calculation
- Exposed via `GET /metrics` endpoint (public, no auth required)
- Integrated into RequestContextMiddleware for automatic recording

✅ Updated `.env.example` with `API_KEY` variable documentation

---

## 28 July 2026

### E2E Integration & Final Testing (Person 1)

✅ Created comprehensive 14-test end-to-end integration suite (tests/test_end_to_end.py):
   - Server startup / health / readiness / metrics endpoints
   - OpenAI-compatible POST /chat/completions with single-turn, system-message, multi-turn variants
   - X-Request-ID propagation and response correlation (chatcmpl-{request_id})
   - Request validation error handling (empty messages, invalid role, missing model, out-of-range params)
   - Behaviour engine verification across multiple conversation turns
   - Concurrent request isolation (5 parallel requests)
   - 404 handling for unknown routes
✅ Added RequestValidationError exception handler in app.py — returns 400 instead of FastAPI's default 422
✅ Fixed LLM fallback in _step_generate — returns natural greeting instead of leaking master prompt
✅ Fixed hardcoded sys.path in tests/integration_test_p2.py and tests/test_memory.py
✅ All 14 E2E tests pass, all existing Person 2/3 test suites pass
✅ Project version bumped to v1.1.0, progress updated to 100%

### Optional Enhancements (Person 1)

✅ Performance: Reduced redundant model_dump() calls in orchestrator — cached dicts for prompt builder context
✅ Edge-case tests: Expanded E2E suite from 14 → 22 tests including:
   - Auth middleware (API_KEY validation: missing, invalid, valid, public paths)
   - Empty message content rejection
   - Very long message (6000 chars) handling
   - Zero temperature acceptance
   - Negative max_tokens rejection
   - Max conversation length enforcement
   - Comprehensive response schema validation (id format, usage totals)
   - HTTP method not allowed (PUT /chat/completions)
✅ Documentation: Updated README with project completion table and release-candidate badge
✅ Version bumped metadata to v1.1.0 across all endpoints

Future changes should always be appended below.

Never modify previous entries.