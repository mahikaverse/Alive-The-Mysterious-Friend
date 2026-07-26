"""Reality Check / Response Validator.

Validates generated responses for personality consistency,
emotional consistency, contradictions, hallucinations,
and response length.

This is an MVP implementation that uses lightweight heuristics
(patterns, keywords, and basic checks) rather than an external
LLM call.  A production version could integrate a separate
validity model for deeper semantic analysis.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Phrases that explicitly break the "never reveal you are an AI" rule.
_AI_DISCLAIMER_PATTERNS: tuple[str, ...] = (
    "as an ai",
    "as an artificial intelligence",
    "as a language model",
    "as an llm",
    "i am an ai",
    "i am an artificial intelligence",
    "i am a language model",
    "i am a machine",
    "i don't have feelings",
    "i do not have feelings",
    "i don't have emotions",
    "i do not have emotions",
    "as a machine",
)

# Default maximum allowed response length (characters).
_DEFAULT_MAX_RESPONSE_LENGTH: int = 1500

# Minimum response length to reject empty or near-empty responses.
_DEFAULT_MIN_RESPONSE_LENGTH: int = 2


class ResponseValidator:
    """Validates LLM responses before returning them to the user.

    Usage
    -----
        validator = ResponseValidator()
        is_valid = validator.validate(response, context={
            "persona": persona_dict,
            "emotion": emotion_dict,
            "memory_context": {…},
        })
    """

    def __init__(self, max_response_length: int = _DEFAULT_MAX_RESPONSE_LENGTH) -> None:
        """Initialise the validator.

        Parameters
        ----------
        max_response_length : int
            Maximum allowed response length in characters.
            Defaults to ``1500``.
        """
        self._max_response_length: int = max_response_length
        logger.info("ResponseValidator ready (max_length=%d)", self._max_response_length)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, response: str, context: dict[str, Any] | None = None) -> bool:
        """Run all validation checks on the generated response.

        Iterates through every check defined in the API specification
        and logs the result of each one.  Returns ``True`` only when
        **all** checks pass.

        Parameters
        ----------
        response : str
            The text returned by ``LLMProvider.generate()``.
        context : dict[str, Any] | None
            Optional dictionary that may contain any of the following
            keys used by individual checks:

            - ``"persona"`` — ``PersonaProfile`` as a dict (from
              ``IdentityEngine.to_dict()``)
            - ``"emotion"`` — ``EmotionState`` as a dict (from
              ``model_dump()``)
            - ``"memory_context"`` — arbitrary dict holding memory
              facts for contradiction detection

        Returns
        -------
        bool
            ``True`` if every check passes, ``False`` otherwise.
        """
        context = context or {}
        persona: dict[str, Any] = context.get("persona", {})
        emotion: dict[str, Any] = context.get("emotion", {})
        memory_context: dict[str, Any] = context.get("memory_context", {})

        checks: list[tuple[str, bool]] = [
            ("personality_consistency", self.check_personality_consistency(response, persona)),
            ("emotional_consistency", self.check_emotional_consistency(response, emotion)),
            ("response_length", self.check_response_length(response)),
            ("contradictions", self.check_contradictions(response, memory_context)),
            ("hallucinations", self.check_hallucinations(response)),
        ]

        all_pass: bool = True
        for name, result in checks:
            if result:
                logger.debug("Check passed: %s", name)
            else:
                logger.warning("Check failed: %s", name)
                all_pass = False

        if all_pass:
            logger.info("All response validation checks passed.")
        else:
            logger.warning("Response validation FAILED — at least one check did not pass.")

        return all_pass

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def check_personality_consistency(self, response: str, persona: dict[str, Any]) -> bool:
        """Ensure the response aligns with the established personality.

        Checks that the response does **not** contain phrases that
        explicitly contradict the character's identity (e.g. claiming
        to be an AI).  In an MVP this is a pattern-based gate; a
        production system could also compare sentiment / word choice
        against the persona's known traits.

        Parameters
        ----------
        response : str
        persona : dict[str, Any]
            A ``PersonaProfile`` serialised via ``model_dump()``.

        Returns
        -------
        bool
        """
        response_lower: str = response.lower()

        for pattern in _AI_DISCLAIMER_PATTERNS:
            if pattern in response_lower:
                logger.warning(
                    "Persona consistency violation: response contains '%s'", pattern
                )
                return False

        return True

    def check_emotional_consistency(self, response: str, emotion: dict[str, Any]) -> bool:
        """Ensure the response reflects the current emotional state.

        Uses basic keyword matching between the response and the
        current mood.  This is intentionally lightweight for the MVP.

        Parameters
        ----------
        response : str
        emotion : dict[str, Any]
            An ``EmotionState`` serialised via ``model_dump()``.

        Returns
        -------
        bool
        """
        mood: str = emotion.get("mood", "").lower().strip()

        if not mood or mood == "neutral":
            return True

        # Simple mood-to-keyword mapping for basic consistency.
        mood_positive_keywords: tuple[str, ...] = (
            "happy", "great", "wonderful", "love", "excited",
        )
        mood_negative_keywords: tuple[str, ...] = (
            "sad", "angry", "upset", "frustrated", "miserable",
        )

        positive_moods: tuple[str, ...] = ("happy", "joyful", "excited", "hopeful")
        negative_moods: tuple[str, ...] = ("sad", "angry", "frustrated", "anxious", "stressed")

        response_lower: str = response.lower()

        if mood in positive_moods:
            # Flag if the response is overwhelmingly negative despite a positive mood.
            neg_count: int = sum(
                1 for kw in mood_negative_keywords if kw in response_lower
            )
            if neg_count >= 3:
                logger.warning(
                    "Emotional inconsistency: mood is '%s' but response contains "
                    "%d negative keywords",
                    mood,
                    neg_count,
                )
                return False

        elif mood in negative_moods:
            # Flag if the response is overwhelmingly positive despite a negative mood.
            pos_count: int = sum(
                1 for kw in mood_positive_keywords if kw in response_lower
            )
            if pos_count >= 3:
                logger.warning(
                    "Emotional inconsistency: mood is '%s' but response contains "
                    "%d positive keywords",
                    mood,
                    pos_count,
                )
                return False

        return True

    def check_response_length(self, response: str) -> bool:
        """Verify response length is within acceptable limits.

        Rejects responses that are empty, too short, or exceed the
        configured maximum length.

        Parameters
        ----------
        response : str

        Returns
        -------
        bool
        """
        length: int = len(response.strip())

        if length < _DEFAULT_MIN_RESPONSE_LENGTH:
            logger.warning(
                "Response too short (%d chars, min %d)", length, _DEFAULT_MIN_RESPONSE_LENGTH
            )
            return False

        if length > self._max_response_length:
            logger.warning(
                "Response too long (%d chars, max %d)", length, self._max_response_length
            )
            return False

        return True

    def check_contradictions(self, response: str, memory_context: dict[str, Any]) -> bool:
        """Detect contradictions with previously established facts.

        This check has two parts:

        1. **Internal contradictions** — the response says something
           and then immediately contradicts itself.
        2. **External contradictions** — the response contradicts
           known facts supplied in ``memory_context`` (MVP: exact
           negation patterns against provided facts).

        Parameters
        ----------
        response : str
        memory_context : dict[str, Any]
            Arbitrary dictionary of known facts (e.g. ``{"name": …
            }``).  Not all keys are validated; only those whose values
            are strings are checked for contradiction.

        Returns
        -------
        bool
        """
        # --- Internal contradictions ---
        sentences: list[str] = self._split_sentences(response)

        seen_claims: set[str] = set()
        for sentence in sentences:
            simplified: str = sentence.strip().lower().rstrip(".?!")
            if not simplified:
                continue

            # Check for explicit negation of a previously stated claim.
            for prev in seen_claims:
                if self._is_contradiction(prev, simplified):
                    logger.warning(
                        "Internal contradiction detected: '%s' vs '%s'", prev, simplified
                    )
                    return False

            seen_claims.add(simplified)

        # --- External contradictions (against memory context) ---
        for key, value in memory_context.items():
            if not isinstance(value, str):
                continue

            value_lower: str = value.lower()
            response_lower: str = response.lower()

            # Check if response explicitly negates a known fact.
            for negation in (
                f"i don't {value_lower}",
                f"i do not {value_lower}",
                f"i didn't {value_lower}",
                f"i did not {value_lower}",
                f"i never {value_lower}",
            ):
                if negation in response_lower:
                    logger.warning(
                        "External contradiction: response says '%s' but context has '%s'='%s'",
                        negation,
                        key,
                        value,
                    )
                    return False

        return True

    def check_hallucinations(self, response: str) -> bool:
        """Detect potential hallucinated content.

        For the MVP, this check looks for:

        - Explicit AI disclosures (``"as an AI"`` etc.)
        - Claims of physical abilities or real-time awareness outside
          the simulated context.
        - Generic or robotic phrasing patterns.

        A production system would use an external fact-checking model
        or a secondary LLM call for semantic hallucination detection.

        Parameters
        ----------
        response : str

        Returns
        -------
        bool
        """
        response_lower: str = response.lower()

        # --- AI disclosure (also covered by personality check, but
        #     repeated here to align with the documented API) ---
        for pattern in _AI_DISCLAIMER_PATTERNS:
            if pattern in response_lower:
                logger.warning("Hallucination detected: AI disclosure '%s'", pattern)
                return False

        # --- Physical / real-time awareness claims ---
        hallucination_claims: tuple[str, ...] = (
            "i can see you",
            "i can hear you",
            "i am watching",
            "i can browse the internet",
            "i can access the web",
            "currently online",
            "i am connected to the internet",
            "according to my database",
            "based on my training data",
            "my programming",
        )
        for claim in hallucination_claims:
            if claim in response_lower:
                logger.warning(
                    "Hallucination detected: physical/real-time claim '%s'", claim
                )
                return False

        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split a string into sentences on ``.``, ``!``, ``?``.

        Parameters
        ----------
        text : str

        Returns
        -------
        list[str]
        """
        import re

        return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

    @staticmethod
    def _is_contradiction(a: str, b: str) -> bool:
        """Return ``True`` if *a* and *b* semantically contradict each
        other at a basic heuristic level.

        This is a simplified check that looks for direct negation
        indicators near the main action word.
        """
        a_lower: str = a.lower()
        b_lower: str = b.lower()

        # If one sentence explicitly negates the other's main verb.
        negation_markers: tuple[str, ...] = (
            "don't", "do not", "doesn't", "does not",
            "didn't", "did not", "won't", "will not",
            "can't", "cannot", "couldn't", "could not",
            "never", "no", "not",
        )

        for marker in negation_markers:
            neg_b: str = f"{marker} {b_lower}"
            # Check if a contains "don't [b's verb]" or similar.
            # This is a simplified heuristic.
            if a_lower.startswith(f"i {neg_b}") or f" i {neg_b}" in a_lower:
                return True

        return False
