# AI_RULES.md

> **Purpose:**  
> This document defines the universal rules that every AI assistant and every team member must follow throughout the development of the project. Before starting any task, every AI must read this document completely and strictly adhere to the workflow defined below.

---

# 1. Startup Protocol

Before writing **any code**, always perform the following steps **in order**.

1. Read `ARCHITECTURE.md` completely to understand the overall system design.
2. Read `API.md` to understand all API contracts and interfaces.
3. Read `PROJECT_STATUS.md` to understand the current state of the project.
4. Read `CHANGELOG.md` to avoid duplicating completed work.
5. Read `NEXT_TASK.md` to identify the current development priorities.
6. Read your assigned `PLAN_PERSON_X.md`.
7. Read your assigned `PROMPT_PERSON_X.md`.

**Do not skip any step.**

---

# 2. Scope Rules

- Only work on the modules assigned to you.
- Never modify another person's module unless explicitly instructed.
- Never change API contracts without updating `API.md`.
- Never change the project folder structure without approval.
- Never modify the database schema without documenting the change.
- Never remove existing functionality unless instructed.
- Always maintain backward compatibility.
- Keep all modules loosely coupled and highly modular.
- Reuse existing utilities whenever possible.
- Avoid unnecessary dependencies.

---

# 3. Coding Standards

All code written for this project must follow these standards.

## General

- Write clean, readable, and maintainable code.
- Use meaningful variable and function names.
- Prefer composition over duplication.
- Keep functions small and focused.
- Separate business logic from API logic.

## Python Standards

- Use type hints wherever possible.
- Follow PEP 8 conventions.
- Use descriptive docstrings.
- Avoid global variables.
- Keep configuration inside `.env`.

## Error Handling

- Handle expected exceptions gracefully.
- Never expose sensitive information in error messages.
- Return meaningful HTTP status codes.
- Add proper logging for important operations.

## Security

- Never hardcode API keys.
- Never hardcode secrets.
- Read all secrets from environment variables.
- Validate all incoming requests.
- Sanitize user input wherever required.

---

# 4. Documentation Rules

Whenever you complete any task:

1. Update `PROJECT_STATUS.md`.
2. Append your work to `CHANGELOG.md`.
3. Update `NEXT_TASK.md` if priorities have changed.
4. Mark completed items in your `PLAN_PERSON_X.md`.
5. Document any new APIs or architectural changes.

Documentation should always reflect the current implementation.

---

# 5. Git Workflow Rules

- Never commit directly to the `main` branch.
- Work only on your assigned feature branch.
- Keep commits small and meaningful.
- Write descriptive commit messages.
- Pull the latest changes before merging.
- Resolve merge conflicts carefully.
- Merge only after successful testing.

Example branch names:

- `feature/backend-api`
- `feature/prompt-engine`
- `feature/memory-engine`
- `feature/behaviour-engine`

---

# 6. API Rules

- Follow the API contracts defined in `API.md`.
- Never change request or response formats without documentation.
- Maintain compatibility with the OpenAI Chat Completions API.
- Validate all incoming request data.
- Return appropriate HTTP status codes.
- Ensure responses follow the expected JSON structure.

---

# 7. Integration Rules

Before integrating your module:

- Verify that dependencies are available.
- Do not assume another module is complete.
- Mock unavailable modules when necessary.
- Clearly document temporary workarounds.
- Inform the team of any integration blockers.

---

# 8. Testing Rules

Before marking any task as completed:

- Verify the code runs without errors.
- Test all implemented functionality.
- Validate API responses.
- Test edge cases wherever applicable.
- Ensure existing functionality is unaffected.

---

# 9. Completion Protocol

Before stopping your work session, verify the following:

- [ ] Code compiles successfully.
- [ ] No API contracts have been broken.
- [ ] Required tests have been completed.
- [ ] Documentation has been updated.
- [ ] `PROJECT_STATUS.md` has been updated.
- [ ] `CHANGELOG.md` has been updated.
- [ ] `NEXT_TASK.md` reflects the current priorities.
- [ ] Your `PLAN_PERSON_X.md` has been updated.
- [ ] Your code is ready for integration.

---

# 10. Communication Rules

If you encounter a blocker:

- Document it in `PROJECT_STATUS.md`.
- Mention the dependency clearly.
- Do not modify another person's module to bypass the issue.
- Wait until the dependency is resolved or coordinate with the respective owner.

---

# 11. Quality Principles

Every contribution should aim to be:

- Modular
- Maintainable
- Scalable
- Reusable
- Well documented
- Easy to test
- Easy to integrate

Avoid quick fixes that increase technical debt.

---

# 12. Project Philosophy

The objective of this project is **not simply to build a chatbot**, but to build a **Human Simulation System** capable of maintaining personality, memory, emotions, reasoning, and consistent conversational behavior while exposing an OpenAI-compatible API.

Every implementation decision should support this objective.

---

**Remember:**
Always prioritize code quality, modularity, and maintainability over writing code quickly. Every completed task should leave the project in a better and more stable state than before.