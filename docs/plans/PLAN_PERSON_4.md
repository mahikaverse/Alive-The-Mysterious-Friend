# PLAN_PERSON_4.md

# Person 4 — Human Behaviour Layer

## Role

You are responsible for making Alive feel like a human instead of a chatbot.

---

# Modules

- Emotion Core
- Bond Engine
- Life Stream

---

# Responsibilities

Develop:

- Emotion tracking
- Relationship evolution
- Daily life simulation
- Mood updates
- Human behavioural state

---

# Consumes

- Current conversation
- Previous emotional state
- Previous relationship state

---

# Produces

- Emotional Context
- Relationship Context
- Life Context

---

# Development Order

1. Emotion Core
2. Relationship Engine
3. Life Simulator
4. Behaviour Updates
5. Integration

---

# Definition of Done

- Emotions update correctly
- Relationships evolve naturally
- Life events remain consistent
- Behaviour state available for Prompt Builder

# File Ownership

You are responsible for Alive's human behaviour.

You may create or modify files only inside the following directories.

backend/
│
├── behaviour/
│   ├── emotion_engine.py
│   ├── relationship_engine.py
│   ├── life_simulator.py
│   ├── mood_manager.py
│   ├── state_manager.py
│   ├── behaviour_models.py
│   └── __init__.py

Shared (Read Only)

backend/models/
backend/utils/

Do NOT modify

backend/api/
backend/controllers/
backend/core/
backend/prompts/
backend/memory/
backend/database/

You own every component responsible for human behaviour simulation.