"""Bond Engine.

Tracks and evolves the relationship between the character
and the user over time.

Implements the RelationshipEngine Protocol defined in
backend/controllers/interfaces.py and integrates with the
ConversationController pipeline.

Design
------
This engine maintains internal state because the Protocol signature
(``update(user_message, emotional_state)``) does not pass the current
``RelationshipState``.  The controller overwrites ``ctx.relationship``
with the returned dict on every call, but the engine cannot read it.

**Architectural limitation (owned by Person 1):**
The Protocol would need a second parameter
``current_relationship: dict`` for the engine to be truly stateless.
Since the interface is owned by Person 1, this engine tracks state
internally.  If ``PipelineContext.relationship`` is ever initialised
with non-default values, the engine's internal state will diverge.
All current default values are ``0.0`` / ``0`` / ``[]``, matching
the engine's baselines.
"""

from __future__ import annotations

import logging
import re
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stimulus → relationship adjustments
# ---------------------------------------------------------------------------

_RELATIONSHIP_STIMULI: dict[str, dict[str, float]] = {
    "greeting":          {"friendship": 0.01, "trust": 0.01},
    "positive_feedback": {"friendship": 0.03, "trust": 0.02},
    "negative_feedback": {"friendship": -0.02, "trust": -0.03},
    "emotional_sharing": {"friendship": 0.04, "trust": 0.06},
    "question":          {"friendship": 0.01, "trust": 0.01},
    "hostile":           {"friendship": -0.05, "trust": -0.08},
    "deep_topic":        {"friendship": 0.02, "trust": 0.03},
    "humor":             {"friendship": 0.02, "trust": 0.01},
    "topic_change":      {"friendship": 0.00, "trust": 0.00},
    "repetitive":        {"friendship": -0.01, "trust": -0.01},
    "silence":           {"friendship": 0.00, "trust": -0.01},
    "neutral":           {"friendship": 0.00, "trust": 0.00},
}

# Shared experience templates keyed by stimulus category.
# Each pool has ≥4 entries so that modular cycling is not immediately obvious.
_EXPERIENCE_TEMPLATES: dict[str, list[str]] = {
    "greeting": [
        "Said hello for the first time",
        "Greeted each other warmly",
        "Started a conversation with a friendly hello",
        "Acknowledged each other's presence",
    ],
    "positive_feedback": [
        "Exchanged kind words",
        "Shared a positive moment",
        "Appreciated each other",
        "Celebrated something good together",
    ],
    "negative_feedback": [
        "Had a disagreement",
        "Exchanged harsh words",
        "Encountered a misunderstanding",
        "Had a tense exchange",
    ],
    "emotional_sharing": [
        "Shared feelings openly",
        "Opened up about emotions",
        "Trusted each other with something personal",
        "Had a heartfelt conversation",
    ],
    "question": [
        "Asked a thoughtful question",
        "Explored a topic together",
        "Dove into a curious discussion",
        "Learned something new together",
    ],
    "hostile": [
        "Had a conflict",
        "Exchanged hostile words",
        "Experienced a heated moment",
        "Clashed over something",
    ],
    "deep_topic": [
        "Discussed something deep",
        "Reflected on life together",
        "Explored a profound idea",
        "Contemplated something meaningful",
    ],
    "humor": [
        "Shared a laugh",
        "Enjoyed a joke together",
        "Found something amusing",
        "Had a lighthearted moment",
    ],
}

# Categories that count as "notable" for shared_experiences.
_NOTABLE_CATEGORIES: frozenset[str] = frozenset({
    "emotional_sharing", "deep_topic", "hostile", "humor",
    "positive_feedback", "negative_feedback", "question",
})

# Maximum shared experiences to retain (FIFO eviction).
_MAX_SHARED_EXPERIENCES: int = 20

# Baseline values for decay toward neutral.
_BASELINE_FRIENDSHIP: float = 0.0
_BASELINE_TRUST: float = 0.0

# Mood categories used for emotion-modulated adjustments.
_POSITIVE_MOODS: frozenset[str] = frozenset({"happy", "joyful", "excited", "hopeful"})
_NEGATIVE_MOODS: frozenset[str] = frozenset({"angry", "frustrated", "stressed"})


class RelationshipEngine:
    """Manages relationship growth and queries.

    Tracks friendship, trust, conversation count, and shared
    experiences across the lifetime of the instance.  The ``update()``
    method is the primary Protocol interface; the legacy helpers
    (``get_friendship_score``, ``get_trust_level``) provide backward
    compatibility.
    """

    def __init__(self) -> None:
        self._friendship: float = _BASELINE_FRIENDSHIP
        self._trust: float = _BASELINE_TRUST
        self._conversation_count: int = 0
        self._shared_experiences: deque[str] = deque(maxlen=_MAX_SHARED_EXPERIENCES)
        logger.info("RelationshipEngine ready")

    # ------------------------------------------------------------------
    # Protocol method
    # ------------------------------------------------------------------

    async def update(
        self,
        user_message: str,
        emotional_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Update relationship metrics after an interaction.

        Parameters
        ----------
        user_message:
            The latest user message.  Must be a string; non-string
            values are treated as silence.
        emotional_state:
            Serialised ``EmotionState`` from ``PipelineContext.emotion``.
            Read for mood context only; relationship state is not
            available through this Protocol.

        Returns
        -------
        dict
            A dict compatible with ``RelationshipState(**result)``.
        """
        msg = user_message if isinstance(user_message, str) else ""

        mood = self._extract_mood(emotional_state)
        category = self._classify(msg)

        # Decay toward baselines
        self._friendship = self._decay(self._friendship, _BASELINE_FRIENDSHIP, 0.01)
        self._trust = self._decay(self._trust, _BASELINE_TRUST, 0.01)

        # Apply stimulus adjustments
        adjustments = _RELATIONSHIP_STIMULI.get(category, _RELATIONSHIP_STIMULI["neutral"])
        self._friendship += adjustments["friendship"]
        self._trust += adjustments["trust"]

        # Emotion-modulated adjustments
        if mood in _POSITIVE_MOODS:
            self._friendship += 0.005
            self._trust += 0.005
        elif mood in _NEGATIVE_MOODS:
            self._friendship -= 0.005
            self._trust -= 0.005

        # Clamp
        self._friendship = self._clamp(self._friendship)
        self._trust = self._clamp(self._trust)

        # Increment conversation count
        self._conversation_count += 1

        # Add shared experience if notable
        if category in _NOTABLE_CATEGORIES:
            templates = _EXPERIENCE_TEMPLATES.get(category)
            if templates:
                idx = self._conversation_count % len(templates)
                self._shared_experiences.append(templates[idx])

        logger.debug(
            "Relationship update: friendship=%.3f trust=%.3f count=%d "
            "experiences=%d (stimulus=%s, mood=%s)",
            self._friendship, self._trust, self._conversation_count,
            len(self._shared_experiences), category, mood,
        )

        return {
            "friendship_score": self._friendship,
            "trust": self._trust,
            "conversation_count": self._conversation_count,
            "shared_experiences": list(self._shared_experiences),
        }

    # ------------------------------------------------------------------
    # Legacy helpers (kept for backward compatibility)
    # ------------------------------------------------------------------

    def get_friendship_score(self) -> float:
        """Return the current friendship score."""
        return self._friendship

    def get_trust_level(self) -> float:
        """Return the current trust level."""
        return self._trust

    # ------------------------------------------------------------------
    # Internal — mood extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_mood(emotional_state: dict[str, Any]) -> str:
        """Safely extract the mood string from an emotion dict."""
        if not isinstance(emotional_state, dict):
            return "neutral"
        mood = emotional_state.get("mood", "neutral")
        return str(mood).lower().strip() if mood else "neutral"

    # ------------------------------------------------------------------
    # Internal — classification
    # ------------------------------------------------------------------

    @classmethod
    def _classify(cls, msg: str) -> str:
        """Classify *msg* into a stimulus category for relationship tracking.

        Single-word keywords use word-boundary matching to avoid false
        positives (e.g. ``"hi"`` must not match ``"this"``).  Multi-word
        phrases use substring matching.

        Priority order ensures the strongest relationship signal wins:
        hostile → emotional_sharing → positive/negative → greeting →
        deep_topic → humor → question → topic_change → neutral.
        """
        if not msg:
            return "silence"

        text = msg.lower()
        stripped = text.strip()

        if not stripped:
            return "silence"

        # Hostile — highest priority
        if cls._matches_any(text, _HOSTILE_WORDS):
            return "hostile"

        # Emotional sharing (must check before positive/negative
        # because "i love" and "i hate" appear in both)
        if cls._matches_any(text, _EMOTIONAL_WORDS):
            return "emotional_sharing"

        # Positive feedback
        if cls._matches_any(text, _POSITIVE_WORDS):
            return "positive_feedback"

        # Negative feedback
        if cls._matches_any(text, _NEGATIVE_WORDS):
            return "negative_feedback"

        # Greeting
        if cls._matches_any(text, _GREETING_WORDS):
            return "greeting"

        # Deep topic
        if cls._matches_any(text, _DEEP_WORDS):
            return "deep_topic"

        # Humor
        if cls._matches_any(text, _HUMOR_WORDS):
            return "humor"

        # Question
        if cls._matches_any(text, _QUESTION_WORDS):
            return "question"

        # Topic change
        if cls._matches_any(text, _TOPIC_WORDS):
            return "topic_change"

        return "neutral"

    # ------------------------------------------------------------------
    # Internal — keyword matching
    # ------------------------------------------------------------------

    @staticmethod
    def _matches_any(text: str, keywords: tuple[str, ...]) -> bool:
        """Return True if *text* matches any keyword.

        Single-word keywords are matched on word boundaries to avoid
        substring false positives (e.g. ``"hi"`` must not match
        ``"this"``).  Multi-word phrases use substring matching so
        that ``"shut up"`` matches inside ``"please shut up now"``.
        """
        for kw in keywords:
            if " " in kw:
                if kw in text:
                    return True
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", text):
                    return True
        return False

    # ------------------------------------------------------------------
    # Internal — utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _decay(value: float, baseline: float, rate: float) -> float:
        """Exponential decay of *value* toward *baseline*."""
        return value + rate * (baseline - value)

    @staticmethod
    def _clamp(value: float) -> float:
        """Clamp a float to the ``[0.0, 1.0]`` range."""
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value


# ---------------------------------------------------------------------------
# Keyword tuples — module-level for fast lookup, frozen after import.
# Single words use \b matching; multi-word phrases use substring matching.
# ---------------------------------------------------------------------------

_HOSTILE_WORDS: tuple[str, ...] = (
    "shut up", "go away", "i hate you", "you're stupid",
    "you are stupid", "stupid", "idiot", "moron", "loser",
    "pathetic", "worthless", "get lost",
)

_EMOTIONAL_WORDS: tuple[str, ...] = (
    "i feel", "i am feeling", "i'm feeling", "i think",
    "i believe", "honestly", "to be honest", "personally",
    "i worry", "i'm scared", "i'm afraid", "means a lot",
    "important to me",
)

_POSITIVE_WORDS: tuple[str, ...] = (
    "thanks", "thank you", "great", "awesome", "love",
    "wonderful", "amazing", "perfect", "nice", "good job",
    "well done", "best", "fantastic", "brilliant", "appreciate",
)

_NEGATIVE_WORDS: tuple[str, ...] = (
    "wrong", "bad", "terrible", "hate", "awful",
    "disappointing", "worst", "annoying", "useless", "boring",
    "dumb", "horrible",
)

_GREETING_WORDS: tuple[str, ...] = (
    "hello", "hi", "hey", "good morning", "good evening",
    "good afternoon", "howdy", "greetings", "sup",
)

_DEEP_WORDS: tuple[str, ...] = (
    "meaning of life", "philosophy", "universe", "consciousness",
    "existence", "purpose", "destiny", "soul", "deep", "profound",
)

_HUMOR_WORDS: tuple[str, ...] = (
    "lol", "haha", "lmao", "joke", "funny", "hilarious",
    "made me laugh", "kidding", "just kidding",
)

_QUESTION_WORDS: tuple[str, ...] = (
    "why", "how", "what", "when", "where", "who", "which",
    "can you", "could you", "would you", "do you", "are you",
    "is it", "tell me", "explain",
)

_TOPIC_WORDS: tuple[str, ...] = (
    "by the way", "btw", "anyway", "changing topic",
    "speaking of", "unrelated", "different subject",
)
