# PLAN_PERSON_3.md

# Person 3 — Memory Layer

## Role

You are responsible for everything Alive remembers.

You design storage, retrieval, ranking, and persistence of memories.

---

# Modules

- Memory Vault
- Database Layer
- Embeddings
- Vector Search
- Memory Ranking

---

# Responsibilities

Develop:

- Memory storage
- Memory retrieval
- Similarity search
- Importance scoring
- Embedding pipeline

---

# Consumes

- Conversation history

---

# Produces

- Relevant Memories
- Updated Memory Store

---

# Development Order

1. Database
2. Memory schema
3. Embeddings
4. Retrieval
5. Ranking
6. Storage

---

# Definition of Done

- Memories stored
- Memories retrieved
- Similarity search works
- Ranking operational

# File Ownership

You are responsible for Alive's memory system.

You may create or modify files only inside the following directories.

backend/
│
├── memory/
│   ├── memory_manager.py
│   ├── memory_store.py
│   ├── retrieval.py
│   ├── ranking.py
│   ├── embeddings.py
│   ├── importance.py
│   └── __init__.py
│
├── database/
│   ├── models.py
│   ├── connection.py
│   ├── repositories.py
│   ├── migrations/
│   └── __init__.py

Shared (Read Only)

backend/models/
backend/utils/

Do NOT modify

backend/api/
backend/controllers/
backend/core/
backend/behaviour/
backend/prompts/

You own every component related to memory persistence and retrieval.