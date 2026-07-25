# API.md

# Alive – The Mysterious Friend

## API Specification

**Version:** 1.0

---

# 1. Overview

This document defines the external and internal API contracts used throughout the Alive Human Simulation System.

The primary objective is to expose an **OpenAI-compatible Chat Completions API** while allowing internal modules to communicate through well-defined interfaces.

Every developer must strictly follow the contracts defined in this document.

---

# 2. API Philosophy

Alive follows an **API-first architecture**.

Every module communicates through predefined interfaces instead of directly accessing another module's implementation.

Benefits include:

- Independent development
- Easier testing
- Better scalability
- Cleaner architecture
- Simple integration

---

# 3. External API

## Base Endpoint

```
POST /chat/completions
```

This endpoint is fully compatible with the OpenAI Chat Completions API.

---

# 4. Request Format

### Headers

```http
Content-Type: application/json
Authorization: Bearer <API_KEY>   (Optional)
```

---

### Request Body

```json
{
  "model": "alive-v1",
  "messages": [
    {
      "role": "system",
      "content": "You are Alive."
    },
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 300
}
```

---

# 5. Response Format

```json
{
  "id": "chatcmpl-001",
  "object": "chat.completion",
  "created": 1721800000,
  "model": "alive-v1",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hey! It's nice to meet you."
      },
      "finish_reason": "stop"
    }
  ]
}
```

---

# 6. Request Lifecycle

```
Incoming Request

↓

Validate Request

↓

Extract Conversation

↓

Run Cognitive Pipeline

↓

Generate Response

↓

Validate Response

↓

Update Internal State

↓

Return Response
```

---

# 7. Internal API Contracts

Every internal module exposes a clear interface.

No module should directly manipulate another module's data.

---

# 8. Conversation Controller API

### Input

```python
ConversationRequest
```

Contains:

- Conversation history
- Current user message
- Request metadata

### Output

```python
ConversationContext
```

Contains:

- Parsed conversation
- Current user input
- Context summary

---

# 9. Memory Engine API

### retrieve()

```python
retrieve(
    conversation,
    current_message
)
```

Returns

```python
RelevantMemories
```

---

### store()

```python
store(
    conversation,
    response
)
```

Stores important information.

---

### update()

Updates existing memories.

---

# 10. Persona Engine API

### get_persona()

Returns

```python
PersonaProfile
```

Contains

- Name
- Age
- Interests
- Writing style
- Personality traits
- Opinions

---

# 11. Emotion Engine API

### update()

Input

- Current emotion
- User message
- Conversation history

Returns

```python
EmotionState
```

Example

```json
{
    "mood":"happy",
    "trust":0.82,
    "stress":0.12,
    "energy":0.74
}
```

---

# 12. Relationship Engine API

### update()

Updates

- Friendship score
- Trust
- Conversation count
- Shared experiences

Returns

```python
RelationshipState
```

---

# 13. Life Simulator API

### get_recent_events()

Returns

```python
LifeEvents
```

Example

```json
[
    "Went grocery shopping",
    "Read a science fiction novel",
    "Cooked dinner"
]
```

---

# 14. Prompt Builder API

### build_prompt()

Input

- Persona
- Emotion
- Memories
- Relationships
- Life Events
- Conversation

Returns

```python
MasterPrompt
```

---

# 15. LLM Provider API

### generate()

Input

```python
MasterPrompt
```

Returns

```python
GeneratedResponse
```

Supported providers

- OpenAI
- Gemini

---

# 16. Response Validator API

### validate()

Checks

- Personality consistency
- Emotional consistency
- Hallucinations
- Contradictions
- Response length

Returns

```python
ValidatedResponse
```

---

# 17. Error Responses

## 400 Bad Request

```json
{
    "error":"Invalid request format."
}
```

---

## 401 Unauthorized

```json
{
    "error":"Unauthorized."
}
```

---

## 404 Not Found

```json
{
    "error":"Endpoint not found."
}
```

---

## 429 Too Many Requests

```json
{
    "error":"Rate limit exceeded."
}
```

---

## 500 Internal Server Error

```json
{
    "error":"Internal server error."
}
```

---

# 18. Module Communication

```
Conversation Controller

↓

Memory.retrieve()

↓

Persona.get_persona()

↓

Emotion.update()

↓

Relationship.update()

↓

Life.get_recent_events()

↓

Prompt.build_prompt()

↓

LLM.generate()

↓

Validator.validate()

↓

Memory.store()
```

---

# 19. API Design Rules

All APIs must follow these principles:

- Stateless external API
- Modular internal APIs
- Strong typing
- Clear request/response models
- Proper error handling
- Backward compatibility
- Consistent naming conventions

---

# 20. Validation Rules

Every incoming request must validate:

- Valid JSON
- Required fields present
- Valid message structure
- Supported roles (`system`, `user`, `assistant`)
- Maximum conversation length
- Token limits
- Parameter ranges

Invalid requests should immediately return an appropriate HTTP error response.

---

# 21. Future API Extensions

The architecture is designed to support additional endpoints in future versions, such as:

| Endpoint | Purpose |
|----------|---------|
| `POST /memory/search` | Search stored memories |
| `GET /persona` | Retrieve current persona profile |
| `GET /emotion` | Retrieve current emotional state |
| `GET /relationship` | Retrieve relationship statistics |
| `GET /health` | Health check endpoint |
| `GET /metrics` | Monitoring and diagnostics |

These endpoints are optional and are not required for the current hackathon.

---

# 22. Developer Notes

- Never modify an API contract without updating this document.
- Keep request and response formats consistent across all modules.
- Every internal module should expose a clear interface rather than allowing direct data access.
- Any new endpoint or interface introduced during development must be documented here before integration.