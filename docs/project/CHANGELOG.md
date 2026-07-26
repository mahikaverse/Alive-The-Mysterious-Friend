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

### Code

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

### Integration

✅ Completed Person 2 — Intelligence Layer Integration

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