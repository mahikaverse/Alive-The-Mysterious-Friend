"""Service interfaces / contracts for external cognitive modules.

These Protocol classes define the contract that every external
module must satisfy when integrated into the Alive pipeline.

Person 1 (Backend) owns these interfaces. Each method signature
matches the corresponding API specification in API.md.
Implementations live in their respective owner's directory:
  - MemoryEngine     → Person 3  (backend/memory/)
  - PersonaEngine    → Person 2  (backend/core/)
  - EmotionEngine    → Person 4  (backend/behaviour/)
  - RelationshipEngine → Person 4 (backend/behaviour/)
  - LifeSimulator    → Person 4  (backend/behaviour/)
  - PromptBuilder    → Person 2  (backend/core/)
  - LLMProvider      → Person 2  (backend/core/)
  - ResponseValidator → Person 2 (backend/core/)
"""

from typing import Protocol


class MemoryEngine(Protocol):
    """Contract for the Memory Vault module (Person 3)."""

    def retrieve(self, conversation: list, current_message: str) -> list[dict]:
        """Retrieve relevant memories for the current context."""

    def store(self, conversation: list, response: str) -> None:
        """Store important information from a conversation turn."""

    def update(self, memory_id: str, updates: dict) -> None:
        """Update an existing memory record."""


class PersonaEngine(Protocol):
    """Contract for the Identity Engine module (Person 2)."""

    def get_persona(self) -> dict:
        """Return the current persona profile."""

    def update_persona(self, updates: dict) -> None:
        """Apply incremental updates to the persona."""


class EmotionEngine(Protocol):
    """Contract for the Emotion Core module (Person 4)."""

    def update(self, current_emotion: dict, user_message: str, conversation_history: list) -> dict:
        """Update the emotional state and return the new state."""


class RelationshipEngine(Protocol):
    """Contract for the Bond Engine module (Person 4)."""

    def update(self, user_message: str, emotional_state: dict) -> dict:
        """Update relationship metrics and return the new state."""


class LifeSimulator(Protocol):
    """Contract for the Life Stream module (Person 4)."""

    def get_recent_events(self) -> list[str]:
        """Return the most recent life events."""


class PromptBuilder(Protocol):
    """Contract for the Mind Composer module (Person 2)."""

    def build_prompt(
        self,
        persona: dict,
        emotion: dict,
        memories: list,
        relationships: dict,
        life_events: list,
        conversation: list,
    ) -> str:
        """Combine all cognitive contexts into a single master prompt."""


class LLMProvider(Protocol):
    """Contract for the LLM Provider module (Person 2)."""

    def generate(self, prompt: str) -> str:
        """Send a prompt to the language model and return the response."""


class ResponseValidator(Protocol):
    """Contract for the Reality Check module (Person 2)."""

    def validate(self, response: str, context: dict) -> bool:
        """Validate the generated response and return whether it passes."""
