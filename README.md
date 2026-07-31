# 🧠 Alive – The Mysterious Friend

> *A Human Simulation System that thinks, remembers, evolves, and builds meaningful relationships.*
> **Status: 🟢 Release Candidate — Ready for Masquerade '26**

---

# 📖 Overview

**Alive – The Mysterious Friend** is a Human Simulation API developed for **Masquerade '26 – The Turing Challenge**.

Unlike traditional chatbots, Alive is designed to simulate a believable human by combining:

- 🧠 Persistent Identity
- 💭 Long-Term Memory
- ❤️ Emotional Intelligence
- 🤝 Relationship Building
- 🌍 Fictional Life Simulation
- 🗣️ Natural Conversations

Instead of generating isolated responses, Alive maintains a continuous personality and internal state, allowing conversations to feel personal, coherent, and realistic over time.

The backend exposes an **OpenAI-compatible Chat Completions API**, enabling seamless integration with the competition platform.

---

# 🗣️ Conversation Style

Alive is tuned to sound like a real, casual friend rather than a chatbot:

- **Short replies** — usually 1 to 3 sentences. Long essays are avoided.
- **Emojis, not stage directions** — feelings are expressed with emojis (😄 🥺 ✨) *only when they genuinely add tone*, never with written actions like `*smiles*`.
- **Language mirroring** — Alive replies in English when you write English, in **Hinglish** (Hindi written in English letters, e.g. "kaise ho", "yaar", "theek hai") when you write Hinglish, and mixes both when you do.
- **Consistent personality** — the tone, warmth, and voice stay stable across conversations.

---

# 🎯 Project Goals

The primary objective of Alive is to create an AI companion that behaves like a real human rather than a traditional chatbot.

Alive aims to:

- Maintain a consistent personality.
- Remember important conversations.
- Develop emotional awareness.
- Build relationships over time.
- Simulate daily life experiences.
- Produce natural, human-like conversations.
- Support modular development for parallel team collaboration.

---

# 🏗️ System Architecture

```
                        Judge
                          │
                          ▼
              POST /chat/completions
                          │
                          ▼
                 FastAPI API Gateway
                          │
                          ▼
               Alive Orchestrator
                          │
        ┌─────────────────────────────────┐
        │                                 │
        │      Cognitive Modules          │
        │                                 │
        │ • Memory Vault                  │
        │ • Identity Engine               │
        │ • Emotion Core                  │
        │ • Bond Engine                   │
        │ • Life Stream                   │
        │ • Mind Composer                 │
        │ • LLM Provider                  │
        │ • Reality Check                 │
        └─────────────────────────────────┘
                          │
                          ▼
                 OpenAI Compatible Response
```

---

# 🧩 Core Modules

## Backend Infrastructure

Responsible for:

- FastAPI
- API Routes
- Request Validation
- Response Formatting
- Logging
- Deployment

---

## Memory Vault

Responsible for:

- Long-Term Memory
- Semantic Retrieval
- Embeddings
- Importance Ranking

---

## Identity Engine

Responsible for:

- Personality
- Interests
- Preferences
- Writing Style
- Opinions

---

## Behaviour Layer

> Owner: **Person 4 — Human Behaviour**

The Behaviour Layer simulates Alive's emotional intelligence, relationship dynamics, and daily life. It is the core of Alive's ability to behave like a real person rather than a chatbot.

### Implemented Modules

| Module | File | Purpose |
|--------|------|---------|
| **EmotionEngine** | `behaviour/emotion_engine.py` | Analyses incoming messages and updates Alive's emotional state. Classifies user intent, evaluates mood transitions (17 moods), and propagates energy, confidence, and curiosity across turns. |
| **RelationshipEngine** | `behaviour/relationship_engine.py` | Tracks and evolves the relationship with the user. Manages friendship score, trust level, conversation count, and shared experiences. Adjusts relationship metrics based on emotional context. |
| **LifeSimulator** | `behaviour/life_simulator.py` | Generates a fictional daily life for Alive. Produces time-of-day-appropriate activities, simulates daily routines, and maintains a bounded event history with deduplication. |
| **MoodManager** | `behaviour/mood_manager.py` | Canonical source of truth for mood vocabulary. Provides mood transitions, derivation, validation, and sentiment classification. Shared across all behaviour modules. |
| **StateManager** | `behaviour/state_manager.py` | Captures and validates behaviour snapshots each turn. Provides safe accessors for prompt building, tracks state deltas, and performs cross-field consistency checks. |

### Behaviour Pipeline

```
User Message
     │
     ▼
 EmotionEngine
 • Classifies stimulus (greeting, hostile, positive, etc.)
 • Evaluates compound + simple mood transitions
 • Propagates energy, confidence, curiosity
     │
     ▼
 RelationshipEngine
 • Adjusts friendship, trust, conversation count
 • Records shared experiences
 • Modulates based on emotional state
     │
     ▼
 LifeSimulator
 • Rotates daily activities by time-of-day
 • Returns recent life events
     │
     ▼
 StateManager
 • Captures BehaviourSnapshot
 • Validates cross-field consistency
 • Records delta history
     │
     ▼
 ConversationController Response
```

### Production Features

| Feature | Implementation |
|---------|---------------|
| **Protocol compatibility** | All engines satisfy `interfaces.py` Protocol contracts. Return dicts match Pydantic model schemas. |
| **Deterministic behaviour** | LifeSimulator uses turn-count rotation instead of wall-clock time. Consistent across runs. |
| **Bounded memory** | All `deque` collections have `maxlen`. No unbounded growth. |
| **Defensive programming** | Every public method wraps logic in try/except. Corrupted inputs are clamped, coerced, or defaulted. |
| **Validation** | StateManager validates mood strings, bounds floats, checks relationship consistency, and tracks invalid transitions. |
| **Thread safety** | Each request instantiates fresh engine instances via `app.py`. No shared mutable state across requests. |
| **Production-ready architecture** | Module-level constants, frozen keyword sets, deterministic transitions, and comprehensive edge-case handling. |
| **Async compatibility** | All engine methods are `async def`. No blocking I/O or sync operations. |
| **Edge-case handling** | Empty strings, unknown moods, out-of-range values, concurrent calls, and corrupted dicts are all handled gracefully. |

### Validation Status

| Check | Status |
|-------|--------|
| Protocol validation | Passed — all engines satisfy `interfaces.py` |
| Module-level validation | Passed — each module tested independently |
| Production audit | Passed — correctness, safety, and performance verified |
| Cross-module consistency | Passed — mood vocabulary aligned across all modules |
| Compilation checks | Passed — all modules compile cleanly |

### Integration Notes

The Behaviour Layer is **complete and production-ready**.

Remaining work is **integration by Person 1**:

- `app.py:62-67` must be modified to inject `EmotionEngine`, `RelationshipEngine`, and `LifeSimulator` into `ConversationController`.
- The Behaviour Layer is dead code until wired in — all engines are implemented but unused at the application level.
- `app.py` and controller wiring are **outside Behaviour Layer ownership**.

### Known Architectural Limitations

| Limitation | Impact | Status |
|------------|--------|--------|
| RelationshipEngine Protocol does not receive current `RelationshipState` | Engine tracks state internally; diverges if `PipelineContext` is initialised with non-default relationship values | Documented, low risk in practice |
| EmotionEngine contains self-managed mood logic while `MoodManager` exists as canonical | Duplicate vocabulary and transition logic. Identical today, but could drift if one is updated without the other | Documented, no runtime impact |
| `behaviour_models.py` is currently unused | Defines `EmotionSnapshot`, `RelationshipSnapshot`, `LifeEvent` models that are never imported | Dead code, no production impact |

### Behaviour Layer Status

**Production Ready**

Complete. Waiting only for application integration.

---

## Mind Composer

Responsible for combining every cognitive module into a single prompt for the language model.

---

## Reality Check

Validates responses before returning them to the user.

Checks include:

- Personality consistency
- Emotional consistency
- Contradictions
- Hallucinations

---

# ✅ Project Completion

| Milestone | Status |
|-----------|--------|
| API Layer | ✅ Complete |
| Memory System | ✅ Complete (ChromaDB + PostgreSQL) |
| Behaviour Layer | ✅ Complete (Emotion, Relationship, Life Sim) |
| Intelligence Layer | ✅ Complete (Identity, Prompts, LLM, Validator) |
| Orchestrator Pipeline | ✅ Complete (All 8 modules wired) |
| End-to-End Integration | ✅ Complete (22 tests passing) |
| Docker / Deployment | ✅ Complete (Multi-stage, docker-compose) |

---

# 📂 Project Structure

---

# 👥 Team Responsibilities

| Person | Responsibility |
|----------|----------------|
| Person 1 | Backend & Infrastructure |
| Person 2 | Intelligence Layer |
| Person 3 | Memory System |
| Person 4 | Human Behaviour |

---

# 🛠️ Technology Stack

## Backend

- Python
- FastAPI
- Pydantic
- Uvicorn

## AI

- OpenAI-compatible providers with automatic failover:
  - DeepSeek (`deepseek-chat`)
  - NVIDIA NIM (`meta/llama-3.3-70b-instruct`)
  - OpenRouter (`deepseek/deepseek-chat`)
  - xAI Grok (`grok-2-latest`)
  - OpenAI (`gpt-4o-mini`)
  - Google Gemini (`gemini-1.5-flash`)

## Memory

- PostgreSQL
- ChromaDB (vector store)

## Deployment

- Docker
- Railway / Render

## Utilities

- Python Logging
- dotenv

---

# 🚀 Getting Started

## Clone Repository

```bash
git clone <repository-url>

cd Alive
```

---

## Create Virtual Environment

```bash
python -m venv .venv
```

---

## Activate Environment

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment

Create a `.env` file.

Example:

```env
# Pick a primary provider and set at least one key (DeepSeek, NVIDIA,
# OpenRouter, Grok, OpenAI, or Gemini). Providers without a key are skipped.
LLM_PROVIDER=deepseek
LLM_FALLBACK_ORDER=nvidia,openrouter,grok
DEEPSEEK_API_KEY=your_deepseek_api_key

# Optional: enables long-term memory (embeddings) + persistence
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://alive:alive@postgres:5432/alive
```

Full list of variables is in `.env.example`.

> **Memory note:** memory *storage* runs in the background so it never
> delays a reply. Memory *retrieval* (embeddings) requires `OPENAI_API_KEY`.

---

## Run Server

```bash
uvicorn backend.main:app --reload
```

Server:

```
http://localhost:8000
```

---

# 📡 API Endpoint

```
POST /chat/completions
```

Compatible with the OpenAI Chat Completions API.

Example:

```json
{
    "model": "alive-v1",
    "messages": [
        {
            "role": "user",
            "content": "Hello!"
        }
    ]
}
```

---

# 📚 Documentation

Complete documentation is available inside the `docs/` directory.

| File | Purpose |
|------|---------|
| `docs/AI_RULES.md` | Development guidelines |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/API.md` | API contracts |
| `docs/CODING_CONVENTIONS.md` | Coding standards |
| `docs/DECISIONS.md` | Architecture decision records |
| `docs/INTEGRATION.md` | Module integration |
| `docs/MANUAL_TESTING_GUIDE.md` | Manual testing (Swagger UI, Postman, curl, k6) + deployment checklist |
| `docs/plans/PLAN_PERSON_1-4.md` | Development plans |
| `docs/prompts/PROMPT_PERSON_1-4.md` | AI coding prompts |
| `docs/project/PROJECT_STATUS.md` | Live project progress |
| `docs/project/CHANGELOG.md` | Project history |
| `docs/project/NEXT_TASK.md` | Current priorities |
| `HOW_TO_RUN.md` | Quick-start guide |

---

# 🧪 Development Workflow

Every developer should:

1. Read the documentation.
2. Work only on assigned modules.
3. Test changes locally.
4. Update project status.
5. Update changelog.
6. Commit changes.
7. Push to feature branch.

---

# 🎯 Competition Goal

Alive is designed to maximize the feeling that the evaluator is interacting with a real human rather than an AI.

Success is measured not only by correctness but also by:

- Personality consistency
- Emotional realism
- Memory retention
- Relationship development
- Natural conversation flow

---

# 📜 License

This project is developed for **Masquerade '26 – The Turing Challenge**.

All rights reserved by the project team.