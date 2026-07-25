"""Prompt templates.

Manages and loads prompt templates from the prompts/ directory
for system instructions, personality, safety, and examples.
"""

import logging

logger = logging.getLogger(__name__)


class PromptTemplates:
    """Loads and serves prompt templates stored as markdown files."""

    def load_system_prompt(self) -> str:
        """Load the system prompt template."""
        pass

    def load_personality(self) -> str:
        """Load the personality descriptor template."""
        pass

    def load_safety_rules(self) -> str:
        """Load the safety instruction template."""
        pass

    def load_examples(self) -> str:
        """Load conversation example templates."""
        pass

    def load_template(self, name: str) -> str:
        """Load an arbitrary prompt template by name."""
        pass
