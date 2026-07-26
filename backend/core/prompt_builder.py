"""Mind Composer / Prompt Builder.

Combines persona, emotion, memories, relationships,
life events, and conversation into a single master prompt.
"""

import logging
from typing import Any

from backend.core.prompt_templates import PromptTemplates
from backend.models.requests import Message
from backend.models.state import (
    EmotionState,
    LifeContext,
    PersonaProfile,
    RelationshipState,
)

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Assembles the master prompt for the language model.

    The builder loads declarative templates via ``PromptTemplates`` and
    injects the runtime state from every cognitive module to produce a
    single coherent instruction string for the LLM.

    Usage
    -----
        templates = PromptTemplates()
        builder = PromptBuilder(templates)
        prompt = builder.build_prompt(
            persona=profile,
            emotion=emotion_state,
            memories=[...],
            relationships=relationship_state,
            life_events=life_context,
            conversation=messages,
        )
    """

    def __init__(self, templates: PromptTemplates | None = None) -> None:
        """Initialise the builder with an optional template loader.

        Parameters
        ----------
        templates : PromptTemplates | None
            Template loader instance.  When *None*, a default loader
            pointing to ``backend/prompts/`` is created automatically.
        """
        self._templates: PromptTemplates = templates or PromptTemplates()
        logger.info("PromptBuilder ready")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_prompt(
        self,
        persona: PersonaProfile,
        emotion: EmotionState,
        memories: list[Any],
        relationships: RelationshipState,
        life_events: LifeContext,
        conversation: list[Message],
    ) -> str:
        """Combine all cognitive contexts into a single master prompt.

        Parameters
        ----------
        persona : PersonaProfile
            Current identity profile (name, traits, interests, …).
        emotion : EmotionState
            Current emotional state (mood, energy, stress, …).
        memories : list[Any]
            Relevant memories retrieved by the Memory Vault.
        relationships : RelationshipState
            Current relationship state with the user.
        life_events : LifeContext
            Recent life-simulation events.
        conversation : list[Message]
            Full conversation history.

        Returns
        -------
        str
            The assembled master prompt, ready for the LLM provider.
        """
        sections: list[str] = []

        sections.append(self._build_system_block(persona, emotion))
        sections.append(self._build_memory_block(memories))
        sections.append(self._build_context_block(relationships, life_events))

        instructions = self._templates.load_instructions()
        examples = self._templates.load_examples()
        sections.append(instructions)
        sections.append(examples)

        sections.append(self._build_conversation_block(conversation))

        master_prompt = "\n\n".join(sections)

        logger.debug(
            "Master prompt assembled (%d chars, %d sections)",
            len(master_prompt),
            len(sections),
        )
        return master_prompt

    # ------------------------------------------------------------------
    # Internal builders  (one per cognitive domain)
    # ------------------------------------------------------------------

    def _build_system_block(
        self,
        persona: PersonaProfile,
        emotion: EmotionState,
    ) -> str:
        """Build the system-instruction portion of the prompt.

        Loads the system prompt, personality, and safety templates,
        then appends the current persona data and emotional state as
        structured context for the LLM.

        Parameters
        ----------
        persona : PersonaProfile
        emotion : EmotionState

        Returns
        -------
        str
        """
        lines: list[str] = []

        lines.append(self._templates.load_system_prompt())
        lines.append(self._templates.load_personality())
        lines.append(self._templates.load_safety_rules())

        lines.append("")
        lines.append("--- Your Identity ---")
        lines.append(f"Name: {persona.name}")
        lines.append(f"Age: {persona.age}")
        if persona.personality_traits:
            lines.append(f"Personality Traits: {', '.join(persona.personality_traits)}")
        if persona.interests:
            lines.append(f"Interests: {', '.join(persona.interests)}")
        if persona.writing_style:
            lines.append(f"Writing Style: {persona.writing_style}")

        lines.append("")
        lines.append("--- Your Current Emotional State ---")
        lines.append(f"Mood: {emotion.mood}")
        lines.append(f"Energy: {emotion.energy}")
        lines.append(f"Stress: {emotion.stress}")
        lines.append(f"Confidence: {emotion.confidence}")
        lines.append(f"Curiosity: {emotion.curiosity}")

        return "\n".join(lines)

    def _build_memory_block(self, memories: list[Any]) -> str:
        """Build the relevant-memories section of the prompt.

        Parameters
        ----------
        memories : list[Any]
            Each item may be a string or an object with a string
            representation.

        Returns
        -------
        str
            An empty section (``"--- No relevant memories ---"``) when
            the list is empty, otherwise a bullet-list of memories.
        """
        if not memories:
            return "--- No relevant memories ---"

        lines = ["--- Relevant Memories ---"]
        for memory in memories:
            text = str(memory) if not isinstance(memory, str) else memory
            lines.append(f"- {text}")

        return "\n".join(lines)

    def _build_context_block(
        self,
        relationships: RelationshipState,
        life_events: LifeContext,
    ) -> str:
        """Build the relationship and life-context section.

        Parameters
        ----------
        relationships : RelationshipState
        life_events : LifeContext

        Returns
        -------
        str
        """
        lines: list[str] = []

        lines.append("--- Your Relationship ---")
        lines.append(f"Trust: {relationships.trust}")
        lines.append(f"Friendship Score: {relationships.friendship_score}")
        lines.append(f"Conversations Had: {relationships.conversation_count}")
        if relationships.shared_experiences:
            shared = ", ".join(str(e) for e in relationships.shared_experiences)
            lines.append(f"Shared Experiences: {shared}")

        lines.append("")
        lines.append("--- Your Recent Life ---")
        if life_events.recent_activities:
            for act in life_events.recent_activities:
                lines.append(f"- Recent Activity: {act}")
        if life_events.ongoing_events:
            for evt in life_events.ongoing_events:
                lines.append(f"- Ongoing Event: {evt}")
        if life_events.daily_routine:
            lines.append(f"Daily Routine: {', '.join(life_events.daily_routine)}")
        if not life_events.recent_activities and not life_events.ongoing_events:
            lines.append("(Nothing notable has happened recently.)")

        return "\n".join(lines)

    def _build_conversation_block(self, conversation: list[Message]) -> str:
        """Build the ongoing conversation history section.

        Formats the message list as a script of alternating user and
        assistant turns, ending with a prompt for the next assistant
        response.

        Parameters
        ----------
        conversation : list[Message]

        Returns
        -------
        str
        """
        lines = ["--- Conversation ---"]
        for msg in conversation:
            role = msg.role.capitalize()
            lines.append(f"{role}: {msg.content}")

        lines.append("")
        lines.append("Alive:")

        return "\n".join(lines)
