"""Identity Engine.

Thin, read-only abstraction over PersonaProfile that safely exposes
persona data to downstream components (Prompt Builder, Orchestrator).

The engine is independent of any specific data source. A PersonaProfile
is injected through the constructor, allowing the caller to load it
from configuration, a file, a database, an API, or in-memory defaults.

Usage:
    profile = PersonaProfile(name="Alive", interests=[...])
    engine = IdentityEngine(persona=profile)
    persona = engine.get_persona()
"""

import copy
import logging
from typing import Any

from backend.models.state import PersonaProfile

logger = logging.getLogger(__name__)


class IdentityEngine:
    """Manages and safely exposes a character's identity profile.

    This class is a stateless wrapper around a single PersonaProfile
    instance.  It does **not** mutate the profile; any updates to the
    persona should be handled by a dedicated service outside this class.
    """

    def __init__(self, persona: PersonaProfile | None = None) -> None:
        """Initialise the engine with an optional PersonaProfile.

        Parameters
        ----------
        persona : PersonaProfile | None
            A pre-loaded persona profile.  When *None*, the engine
            falls back to ``PersonaProfile()`` minimal defaults and
            logs a warning so callers know no external source was
            configured.
        """
        if persona is None:
            logger.warning(
                "IdentityEngine initialised without an external persona source. "
                "Using built-in defaults — no personality data has been loaded."
            )
            self._persona: PersonaProfile = PersonaProfile()
        else:
            self._persona: PersonaProfile = persona

        logger.info("IdentityEngine ready (name=%s, age=%s)", self._persona.name, self._persona.age)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_persona(self) -> PersonaProfile:
        """Return a deep copy of the current persona profile.

        Returns
        -------
        PersonaProfile
            A fully independent copy of the internal profile.  Mutating
            the returned object will *not* affect the engine's state.
        """
        return copy.deepcopy(self._persona)

    def get_writing_style(self) -> str:
        """Return the character's writing-style descriptor.

        Returns
        -------
        str
            A short description of the speaking style (e.g. ``"casual"``).
        """
        return self._persona.writing_style

    def get_personality_traits(self) -> list[str]:
        """Return a copy of the personality-traits list.

        Returns
        -------
        list[str]
            A new list containing the current personality traits.
        """
        return copy.deepcopy(self._persona.personality_traits)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the persona profile to a plain dictionary.

        This is the primary serialisation method used by the Prompt
        Builder when assembling the master prompt.

        Returns
        -------
        dict[str, Any]
            All persona fields as a JSON-compatible dictionary.
        """
        return self._persona.model_dump()
