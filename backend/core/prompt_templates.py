"""Prompt templates.

Manages and loads prompt templates from the prompts/ directory
for system instructions, personality, safety, and examples.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default path relative to this module: backend/core/ -> backend/prompts/
_DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Mapping from public method names to file names (without extension).
_TEMPLATE_FILES: dict[str, str] = {
    "system_prompt": "system_prompt.md",
    "personality": "personality.md",
    "safety_rules": "safety.md",
    "instructions": "instructions.md",
    "examples": "examples.md",
}


class PromptTemplates:
    """Loads and serves prompt templates stored as markdown files.

    Templates are loaded on first access and cached for subsequent
    calls.  The templates directory can be injected via the constructor,
    making the class testable and deployable in different environments.
    """

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        """Initialise the template loader.

        Parameters
        ----------
        templates_dir : str | Path | None
            Path to the directory containing markdown template files.
            When *None*, defaults to ``backend/prompts/`` relative to
            this module.
        """
        self._templates_dir: Path = (
            Path(templates_dir).resolve()
            if templates_dir is not None
            else _DEFAULT_TEMPLATES_DIR
        )

        if not self._templates_dir.is_dir():
            logger.warning(
                "Prompt templates directory does not exist: %s",
                self._templates_dir,
            )

        # In-memory cache: template_name -> content
        self._cache: dict[str, str] = {}

        logger.info("PromptTemplates ready (dir=%s)", self._templates_dir)

    # ------------------------------------------------------------------
    # Public API — each maps to a specific template file.
    # ------------------------------------------------------------------

    def load_system_prompt(self) -> str:
        """Load the system prompt template (``system_prompt.md``).

        Returns
        -------
        str
            The contents of the system prompt template file.
        """
        return self.load_template("system_prompt")

    def load_personality(self) -> str:
        """Load the personality descriptor template (``personality.md``).

        Returns
        -------
        str
            The contents of the personality template file.
        """
        return self.load_template("personality")

    def load_safety_rules(self) -> str:
        """Load the safety instruction template (``safety.md``).

        Returns
        -------
        str
            The contents of the safety rules template file.
        """
        return self.load_template("safety_rules")

    def load_examples(self) -> str:
        """Load conversation example templates (``examples.md``).

        Returns
        -------
        str
            The contents of the examples template file.
        """
        return self.load_template("examples")

    def load_instructions(self) -> str:
        """Load the response instructions template (``instructions.md``).

        Returns
        -------
        str
            The contents of the instructions template file.
        """
        return self.load_template("instructions")

    def load_template(self, name: str) -> str:
        """Load an arbitrary prompt template by logical name.

        The logical name is looked up in the internal mapping to
        determine the actual filename.  Unknown names are treated as
        a direct filename (with ``.md`` appended if no extension is
        present).

        Parameters
        ----------
        name : str
            Logical template name (e.g. ``"system_prompt"``) or a
            custom filename.

        Returns
        -------
        str
            The contents of the requested template file.

        Raises
        ------
        FileNotFoundError
            If the template file does not exist on disk.
        """
        # Resolve logical name -> filename
        filename = _TEMPLATE_FILES.get(name, name)

        # Append .md if no extension is present
        if "." not in filename:
            filename = f"{filename}.md"

        # Return from cache if available
        if filename in self._cache:
            return self._cache[filename]

        # Load from disk
        file_path = self._templates_dir / filename

        if not file_path.is_file():
            logger.error("Template file not found: %s", file_path)
            raise FileNotFoundError(
                f"Prompt template '{name}' not found at {file_path}. "
                f"Ensure the template file exists in {self._templates_dir}."
            )

        content = file_path.read_text(encoding="utf-8")
        self._cache[filename] = content

        logger.debug("Loaded template: %s (%d chars)", filename, len(content))
        return content
