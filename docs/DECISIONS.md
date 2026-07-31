# DECISIONS.md

# Alive – The Mysterious Friend

## Architecture Decision Record (ADR)

**Purpose**

This document records important architectural and technical decisions made during the project.

Its goal is to preserve the reasoning behind major choices so future contributors understand **why** something was implemented in a particular way.

---

## How to Use

Whenever the team makes a significant technical decision:

- Add a new entry.
- Never modify previous entries.
- If a decision changes, create a new entry explaining the change.
- Keep entries concise and factual.

---

# Decision Template

## ADR-XXX

**Date**

YYYY-MM-DD

**Status**

- Proposed
- Accepted
- Superseded
- Deprecated

**Decision**

Describe the decision.

**Context**

Why was this decision needed?

**Alternatives Considered**

- Option A
- Option B
- Option C

**Reasoning**

Explain why the chosen option was selected.

**Consequences**

Positive:

-

Negative:

-

---

# ADR-001

**Date**

2026-07-26

**Status**

Accepted

### Decision

Use an OpenAI-compatible Chat Completions API.

### Context

Masquerade '26 expects submissions through a standard chat interface.

### Alternatives

- Custom REST API
- GraphQL
- OpenAI-compatible API

### Reasoning

Using the OpenAI format simplifies integration, testing, and future extensibility.

### Consequences

Positive

- Easy integration
- Familiar interface
- Supports existing clients

Negative

- Must follow OpenAI response schema

---

# ADR-002

**Date**

2026-07-26

**Status**

Accepted

### Decision

Adopt a modular architecture.

### Context

Four developers will work in parallel.

### Alternatives

- Monolithic application
- Layered architecture
- Modular architecture

### Reasoning

Independent modules reduce merge conflicts and simplify maintenance.

### Consequences

Positive

- Easier parallel development
- Better scalability
- Clear ownership

Negative

- Requires well-defined interfaces

---

# ADR-003

**Date**

2026-07-26

**Status**

Accepted

### Decision

Use a central Alive Orchestrator.

### Context

Multiple cognitive modules must cooperate to generate a response.

### Alternatives

- Modules communicating directly
- Event-driven architecture
- Central orchestrator

### Reasoning

A single orchestrator keeps modules independent and prevents tight coupling.

### Consequences

Positive

- Simpler integration
- Loose coupling
- Easier debugging

Negative

- Orchestrator becomes a critical component

---

# ADR-004

**Date**

2026-07-26

**Status**

Accepted

### Decision

Separate Memory, Intelligence, Behaviour, and Infrastructure into independent ownership domains.

### Context

The project is being developed by four contributors working simultaneously.

### Alternatives

- Shared ownership
- Feature-based ownership
- Module-based ownership

### Reasoning

Module ownership minimizes merge conflicts and establishes clear responsibilities.

### Consequences

Positive

- Faster development
- Clear accountability
- Easier onboarding

Negative

- Requires coordination when shared models change

---

# ADR-005

**Date**

2026-07-26

**Status**

Accepted

### Decision

Maintain project documentation as the single source of truth.

### Context

Multiple AI assistants and developers will contribute throughout the project.

### Alternatives

- Informal communication
- External notes
- Centralized documentation

### Reasoning

Consistent documentation improves collaboration, reduces ambiguity, and simplifies onboarding.

### Consequences

Positive

- Better team coordination
- Easier maintenance
- Consistent development process

Negative

- Documentation must be kept up to date

---

# ADR-006

**Date**

2026-08-01

**Status**

Accepted

### Decision

Reply speed must not come at the cost of reply quality; do not enforce hard LLM timeouts or deadlines.

### Context

Initial latency tuning added a 10s client timeout and a hard 20s `asyncio.wait_for` deadline in the orchestrator so replies always returned quickly. Testers found the fallback replies unnatural — worse than waiting a minute for a correct answer.

### Alternatives

- Aggressive timeouts + canned fallback replies
- Background memory storage + shorter `max_tokens` only
- Hard deadlines with queueing

### Reasoning

A human-simulation chatbot scores on how natural it sounds, not on 2-second responses. Removing the deadline means slow providers still produce a genuine reply.

### Consequences

Positive

- Correct, human-sounding replies even on slow models
- Latency still improved via background memory storage and `max_tokens=150`

Negative

- Slow providers may occasionally take a long time to reply

---

# ADR-007

**Date**

2026-08-01

**Status**

Accepted

### Decision

Use short replies, emojis (not `*stage directions*`), and language mirroring (English / Hinglish / mixed).

### Context

Alive previously answered in long, formal paragraphs with written actions like `*smiles*`. Users wanted a casual friend who replies in 1–3 sentences, uses emojis sparingly, and responds in the same language as the user (including Hinglish).

### Alternatives

- Keep formal tone
- Always English
- Emojis in every message

### Reasoning

Mirroring the user's language and keeping replies short makes the character feel human and relatable for the Masquerade '26 challenge.

### Consequences

Positive

- More natural, conversational feel
- Works for English, Hinglish, and mixed chats

Negative

- Requires prompt discipline to avoid emoji overuse

---