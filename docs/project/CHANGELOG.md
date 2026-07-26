# CHANGELOG.md

# Alive – The Mysterious Friend

## Project Changelog

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

Future changes should always be appended below.

Never modify previous entries.