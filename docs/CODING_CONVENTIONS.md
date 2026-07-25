# CODING_CONVENTIONS.md

# Alive – The Mysterious Friend

## Coding Standards & Development Conventions

**Version:** 1.0

---

# 1. Purpose

This document defines the coding standards, naming conventions, project structure, documentation style, and Git workflow used throughout the Alive project.

Every contributor—human or AI—must follow these conventions to ensure consistency, maintainability, and clean integration across the codebase.

---

# 2. General Principles

Every piece of code should be:

- Readable
- Modular
- Reusable
- Testable
- Maintainable
- Scalable
- Well documented

Always optimize for long-term maintainability rather than short-term speed.

---

# 3. Project Structure

The project follows the following directory structure.

```
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
├── main.py
└── app.py
```

Do not create new top-level folders unless absolutely necessary.

---

# 4. Naming Conventions

## Files

Use lowercase with underscores.

Examples

```
memory_manager.py

emotion_engine.py

response_validator.py
```

Do NOT use

```
MemoryManager.py

EmotionEngine.py
```

---

## Classes

Use PascalCase.

Examples

```python
class MemoryManager:

class EmotionEngine:

class PromptBuilder:
```

---

## Functions

Use snake_case.

Examples

```python
retrieve_memories()

update_emotion()

build_prompt()

validate_response()
```

---

## Variables

Use descriptive snake_case names.

Good

```python
current_mood

memory_score

conversation_history
```

Bad

```python
x

temp

data1
```

---

## Constants

Use uppercase.

```python
MAX_MEMORY_RESULTS = 10

DEFAULT_MODEL = "alive-v1"
```

---

# 5. Type Hints

Every public function should include type hints.

Good

```python
def retrieve_memories(
    conversation: list
) -> list:
```

Avoid

```python
def retrieve(conversation):
```

---

# 6. Function Design

Functions should:

- Perform one responsibility.
- Be easy to test.
- Be reusable.
- Be concise.

Prefer:

```python
retrieve_memories()

rank_memories()

filter_memories()
```

instead of

```python
process_everything()
```

---

# 7. Class Design

Each class should have one clear responsibility.

Example

```
MemoryManager

Responsible only for memory management.
```

Avoid combining unrelated responsibilities into a single class.

---

# 8. Imports

Import order should always be:

### Standard Library

```python
import os

import json
```

### Third-Party Libraries

```python
from fastapi import FastAPI
```

### Local Imports

```python
from backend.memory.memory_manager import MemoryManager
```

Separate each group with one blank line.

---

# 9. Comments

Write comments only when they improve understanding.

Avoid obvious comments.

Bad

```python
# Increment counter

counter += 1
```

Good

```python
# Store only memories above the importance threshold
```

---

# 10. Docstrings

Public classes and functions should include docstrings.

Example

```python
def retrieve_memories():

    """
    Retrieves the most relevant memories
    based on the current conversation.
    """
```

---

# 11. Logging

Never use

```python
print()
```

Instead use Python logging.

Example

```python
logger.info()

logger.warning()

logger.error()
```

---

# 12. Error Handling

Always catch expected exceptions.

Good

```python
try:

    retrieve_memories()

except MemoryError:

    logger.error(...)
```

Never use

```python
except:
```

---

# 13. Configuration

Never hardcode:

- API Keys
- Database URLs
- Tokens
- Passwords

Always use

```
.env
```

Example

```python
OPENAI_API_KEY

DATABASE_URL
```

---

# 14. API Models

Use Pydantic models for all request and response schemas.

Never return raw dictionaries unless necessary.

---

# 15. Folder Ownership

Respect module ownership.

| Folder | Owner |
|---------|-------|
| api | Person 1 |
| controllers | Person 1 |
| config | Person 1 |
| core | Person 2 |
| prompts | Person 2 |
| memory | Person 3 |
| database | Person 3 |
| behaviour | Person 4 |
| models | Shared |
| utils | Shared |

Do not modify another owner's files without coordination.

---

# 16. Commit Message Convention

Use clear commit messages.

Examples

```
feat(api): add chat completions endpoint

feat(memory): implement retrieval engine

feat(emotion): add mood transition logic

fix(api): validate incoming request schema

docs: update architecture
```

---

# 17. Testing Guidelines

Before completing a task:

- Code runs successfully.
- Imports resolve correctly.
- No syntax errors.
- Interfaces match API.md.
- Integration points are documented.

---

# 18. Documentation

Whenever functionality changes:

Update

- PROJECT_STATUS.md
- CHANGELOG.md
- NEXT_TASK.md

If API changes:

Update

- API.md

If architecture changes:

Update

- ARCHITECTURE.md

---

# 19. AI Code Generation Rules

Whenever an AI generates code, it must:

- Produce complete files.
- Include all imports.
- Avoid placeholder implementations.
- Follow project folder structure.
- Respect ownership boundaries.
- Use Python type hints.
- Follow modular design.
- Write production-ready code.
- Explain assumptions if required.

---

# 20. Definition of Done

A task is considered complete only when:

- Code is implemented.
- Code is formatted.
- Type hints are present.
- Logging is included.
- Error handling is implemented.
- Documentation is updated.
- Project status is updated.
- Code is ready for integration.

---

# 21. Project Philosophy

Every contributor should write code as if it will be maintained by someone else in the future.

Consistency, readability, and maintainability are more valuable than clever or overly complex solutions.

The goal is to build a codebase that feels like it was written by a single, disciplined engineering team—even when multiple developers and AI assistants are contributing simultaneously.