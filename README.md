# 🧠 Alive – The Mysterious Friend

> *A Human Simulation System that thinks, remembers, evolves, and builds meaningful relationships.*

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

## Emotion Core

Responsible for:

- Mood
- Confidence
- Trust
- Stress
- Emotional State

---

## Bond Engine

Responsible for:

- Friendship
- Trust
- Shared Experiences
- Relationship Growth

---

## Life Stream

Responsible for:

- Daily Activities
- Personal Experiences
- Fictional Timeline
- Event History

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

# 📂 Project Structure

```
Alive/

backend/
│
├── api/
├── controllers/
├── config/
├── core/
├── memory/
├── behaviour/
├── database/
├── prompts/
├── models/
├── utils/
│
├── app.py
└── main.py

docs/
│
├── AI_RULES.md
├── ARCHITECTURE.md
├── API.md
├── INTEGRATION.md
│
├── plans/
├── prompts/
└── project/

tests/

Dockerfile

README.md
```

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

- OpenAI
- Gemini

## Memory

- PostgreSQL
- ChromaDB / FAISS

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
OPENAI_API_KEY=your_api_key

DATABASE_URL=your_database_url
```

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
| AI_RULES.md | Development guidelines |
| ARCHITECTURE.md | System architecture |
| API.md | API contracts |
| INTEGRATION.md | Module integration |
| PLAN_PERSON_1-4.md | Development plans |
| PROMPT_PERSON_1-4.md | AI coding prompts |
| PROJECT_STATUS.md | Live project progress |
| CHANGELOG.md | Project history |
| NEXT_TASK.md | Current priorities |

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