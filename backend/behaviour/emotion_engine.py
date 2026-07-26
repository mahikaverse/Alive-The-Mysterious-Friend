"""Emotion Core.

Tracks and updates the character's emotional state including mood,
confidence, trust, stress, and energy.

Implements the EmotionEngine Protocol defined in
backend/controllers/interfaces.py and integrates with the
ConversationController pipeline.

Design: Stateless transformer — receives the current emotion state
as input and returns the updated state as output.  No internal
persistence between calls; all state lives in PipelineContext.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from backend.behaviour.mood_manager import MoodManager
from backend.models.state import EmotionState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stimulus categories and their field adjustments
# ---------------------------------------------------------------------------

STIMULUS_ADJUSTMENTS: dict[str, dict[str, float]] = {
    "greeting":          {"trust": 0.02, "stress": -0.02, "energy": 0.03, "confidence": 0.01, "curiosity": 0.02},
    "positive_feedback": {"trust": 0.03, "stress": -0.05, "energy": 0.05, "confidence": 0.08, "curiosity": 0.01},
    "negative_feedback": {"trust": -0.05, "stress": 0.08, "energy": -0.05, "confidence": -0.10, "curiosity": -0.02},
    "question":          {"trust": 0.01, "stress": -0.01, "energy": 0.02, "confidence": 0.02, "curiosity": 0.10},
    "emotional_sharing": {"trust": 0.05, "stress": -0.03, "energy": 0.02, "confidence": 0.03, "curiosity": 0.05},
    "hostile":           {"trust": -0.10, "stress": 0.15, "energy": -0.08, "confidence": -0.12, "curiosity": -0.05},
    "neutral":           {"trust": 0.00, "stress": 0.00, "energy": -0.01, "confidence": 0.00, "curiosity": -0.01},
    "topic_change":      {"trust": 0.00, "stress": 0.01, "energy": 0.02, "confidence": 0.01, "curiosity": 0.08},
    "repetitive":        {"trust": 0.00, "stress": 0.03, "energy": -0.04, "confidence": -0.03, "curiosity": -0.08},
    "deep_topic":        {"trust": 0.02, "stress": 0.02, "energy": -0.02, "confidence": 0.03, "curiosity": 0.12},
    "humor":             {"trust": 0.02, "stress": -0.05, "energy": 0.08, "confidence": 0.04, "curiosity": 0.05},
    "silence":           {"trust": -0.01, "stress": 0.05, "energy": -0.02, "confidence": -0.03, "curiosity": -0.02},
}

# ---------------------------------------------------------------------------
# Keyword signals for stimulus classification
# ---------------------------------------------------------------------------

_SIGNALS: dict[str, list[str]] = {
    "greeting": [
        "hello", "hi", "hey", "good morning", "good evening",
        "good afternoon", "howdy", "greetings", "sup",
    ],
    "positive_feedback": [
        "thanks", "thank you", "great", "awesome", "love", "wonderful",
        "amazing", "perfect", "nice", "good job", "well done", "best",
        "fantastic", "brilliant", "appreciate",
    ],
    "negative_feedback": [
        "wrong", "bad", "terrible", "hate", "stupid", "awful",
        "disappointing", "worst", "annoying", "useless", "boring",
        "dumb", "horrible",
    ],
    "question": [
        "why", "how", "what", "when", "where", "who", "which",
        "can you", "could you", "would you", "do you", "are you",
        "is it", "tell me", "explain",
    ],
    "emotional_sharing": [
        "i feel", "i am feeling", "i'm feeling", "i think",
        "i believe", "honestly", "to be honest", "personally",
        "i love", "i hate", "i worry", "i'm scared", "i'm afraid",
        "means a lot", "important to me",
    ],
    "hostile": [
        "shut up", "go away", "i hate you", "you're stupid",
        "you are stupid", "idiot", "moron", "loser", "pathetic",
        "worthless", "get lost", "drop dead",
    ],
    "humor": [
        "lol", "haha", "lmao", "joke", "funny", "hilarious",
        "that's a good one", "made me laugh", "喜剧", "kidding",
        "just kidding", "开玩笑",
    ],
    "deep_topic": [
        "meaning of life", "philosophy", "universe", "consciousness",
        "existence", "purpose", "destiny", "soul", "think about",
        "wonder about", "what if", "deep", "profound",
    ],
    "topic_change": [
        "by the way", "btw", "anyway", "changing topic",
        "speaking of", "unrelated", "different subject",
    ],
}

# ---------------------------------------------------------------------------
# Mood vocabulary — compatible with ResponseValidator
# ---------------------------------------------------------------------------

_POSITIVE_MOODS: frozenset[str] = frozenset({"happy", "joyful", "excited", "hopeful"})
_NEGATIVE_MOODS: frozenset[str] = frozenset({"sad", "angry", "frustrated", "anxious", "stressed"})
_ALL_KNOWN_MOODS: frozenset[str] = frozenset({
    "neutral", "happy", "excited", "hopeful", "joyful",
    "calm", "thoughtful", "curious", "bored", "tired",
    "exhausted", "confused", "sad", "angry", "frustrated",
    "anxious", "stressed",
})

# Category → mood override used by _compute_mood().
_CATEGORY_MOOD_MAP: dict[str, str] = {
    "hostile":           "angry",
    "emotional_sharing": "thoughtful",
    "question":          "curious",
    "humor":             "happy",
    "deep_topic":        "thoughtful",
    "topic_change":      "curious",
    "repetitive":        "bored",
    "silence":           "confused",
}


class EmotionEngine:
    """Manages emotional state transitions and queries.

    Stateless transformer: receives the current ``EmotionState`` as a
    dict and returns an updated dict.  All transition logic is a pure
    function of the inputs — no internal mutation between calls.
    """

    def __init__(self) -> None:
        self._mood_manager = MoodManager()
        logger.info("EmotionEngine ready")

    # ------------------------------------------------------------------
    # Protocol method
    # ------------------------------------------------------------------

    async def update(
        self,
        current_emotion: dict[str, Any],
        user_message: str,
        conversation_history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Update the emotional state based on the latest interaction.

        Parameters
        ----------
        current_emotion:
            Serialised ``EmotionState`` from ``PipelineContext.emotion``.
        user_message:
            The latest user message.
        conversation_history:
            Full conversation as a list of ``{"role": …, "content": …}``
            dicts.

        Returns
        -------
        dict
            A dict compatible with ``EmotionState(**result)``.
        """
        try:
            mood = str(current_emotion.get("mood", "neutral"))
            trust = float(current_emotion.get("trust", 0.5))
            stress = float(current_emotion.get("stress", 0.0))
            energy = float(current_emotion.get("energy", 0.7))
            confidence = float(current_emotion.get("confidence", 0.5))
            curiosity = float(current_emotion.get("curiosity", 0.5))
        except (TypeError, ValueError):
            logger.warning("Invalid emotion input — falling back to defaults")
            mood, trust, stress = "neutral", 0.5, 0.0
            energy, confidence, curiosity = 0.7, 0.5, 0.5

        # 1. Decay toward baselines
        stress = self._decay(stress, 0.0, 0.05)
        energy = self._decay(energy, 0.7, 0.03)
        confidence = self._decay(confidence, 0.5, 0.02)
        trust = self._decay(trust, 0.5, 0.01)
        curiosity = self._decay(curiosity, 0.5, 0.01)

        # 2. Analyse input
        msg = (user_message or "").strip()
        category = self._classify(msg, conversation_history)
        intensity = self._score_intensity(msg)

        # 3. Apply stimulus adjustments
        trust, stress, energy, confidence, curiosity = self._apply_stimulus(
            category, intensity, trust, stress, energy, confidence, curiosity,
        )

        # 4. Clamp all numeric fields
        trust = self._clamp(trust)
        stress = self._clamp(stress)
        energy = self._clamp(energy)
        confidence = self._clamp(confidence)
        curiosity = self._clamp(curiosity)

        # 5. Compute new mood
        mood = self._compute_mood(mood, category, intensity, trust, stress, energy, confidence, curiosity)

        logger.debug(
            "Emotion update: mood=%s trust=%.2f stress=%.2f energy=%.2f "
            "confidence=%.2f curiosity=%.2f (stimulus=%s, intensity=%.2f)",
            mood, trust, stress, energy, confidence, curiosity,
            category, intensity,
        )

        return {
            "mood": mood,
            "trust": trust,
            "stress": stress,
            "energy": energy,
            "confidence": confidence,
            "curiosity": curiosity,
        }

    # ------------------------------------------------------------------
    # Legacy helpers (kept for backward compatibility)
    # ------------------------------------------------------------------

    def get_state(self) -> dict[str, Any] | None:
        """Return the current emotional state.

        Present for backward compatibility.  The primary interface is
        ``update()`` which is stateless and returns the new state.
        """
        return None

    def decay(self) -> None:
        """Apply natural emotional decay over time.

        Present for backward compatibility.  Decay is now applied
        automatically inside ``update()``.
        """

    # ------------------------------------------------------------------
    # Internal — decay
    # ------------------------------------------------------------------

    @staticmethod
    def _decay(value: float, baseline: float, rate: float) -> float:
        """Exponential decay of *value* toward *baseline*.

        ``rate`` controls how quickly the value returns.  A rate of
        ``0.05`` means ~5 % of the remaining distance is closed per
        call.
        """
        return value + rate * (baseline - value)

    # ------------------------------------------------------------------
    # Internal — stimulus classification
    # ------------------------------------------------------------------

    def _classify(self, msg: str, history: list[dict[str, Any]]) -> str:
        """Classify *msg* into a stimulus category.

        Priority order ensures the strongest signal wins:
        silence → repetitive → hostile → category-specific.
        """
        if not msg:
            return "silence"

        if self._is_repetitive(msg, history):
            return "repetitive"

        msg_lower = msg.lower()

        # Check hostile first — highest priority
        if self._matches_any(msg_lower, _SIGNALS["hostile"]):
            return "hostile"

        # Check remaining categories — first match wins
        for category in ("greeting", "positive_feedback", "negative_feedback",
                         "emotional_sharing", "question", "humor",
                         "deep_topic", "topic_change"):
            if self._matches_any(msg_lower, _SIGNALS[category]):
                return category

        return "neutral"

    @staticmethod
    def _matches_any(text: str, keywords: list[str]) -> bool:
        """Return True if *text* matches any keyword from the list.

        Single-word keywords are matched on word boundaries to avoid
        substring false positives (e.g. ``"hi"`` must not match
        ``"this"``).  Multi-word phrases use substring matching so
        that ``"good morning"`` matches inside ``"I said good morning"``.
        """
        for kw in keywords:
            if " " in kw:
                if kw in text:
                    return True
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", text):
                    return True
        return False

    @staticmethod
    def _is_repetitive(msg: str, history: list[dict[str, Any]]) -> bool:
        """Detect if the current message repeats the last user message."""
        if not history:
            return False
        for entry in reversed(history):
            if entry.get("role") == "user":
                return entry.get("content", "").strip() == msg
        return False

    # ------------------------------------------------------------------
    # Internal — intensity scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _score_intensity(msg: str) -> float:
        """Score the emotional intensity of a message on ``[0.0, 1.0]``."""
        if not msg:
            return 0.0

        score = 0.3  # base intensity

        caps_ratio = sum(1 for c in msg if c.isupper()) / max(len(msg), 1)
        if caps_ratio > 0.5:
            score += 0.2

        exclamations = msg.count("!")
        if exclamations >= 3:
            score += 0.2
        elif exclamations >= 1:
            score += 0.05

        question_marks = msg.count("?")
        if question_marks >= 1:
            score += 0.05

        if len(msg) > 100:
            score += 0.1

        intensity_words = ("very", "extremely", "so", "really", "absolutely",
                           "totally", "completely", "always", "never")
        msg_lower = msg.lower()
        score += sum(0.05 for w in intensity_words if w in msg_lower)

        return min(1.0, score)

    # ------------------------------------------------------------------
    # Internal — field adjustments
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_stimulus(
        category: str,
        intensity: float,
        trust: float,
        stress: float,
        energy: float,
        confidence: float,
        curiosity: float,
    ) -> tuple[float, float, float, float, float]:
        """Apply stimulus adjustments to all numeric fields.

        Returns the five updated values as a tuple.
        """
        adjustments = STIMULUS_ADJUSTMENTS.get(category)
        if not adjustments:
            return trust, stress, energy, confidence, curiosity

        scale = 1.0
        if intensity < 0.3:
            scale = 0.25
        elif intensity < 0.6:
            scale = 1.0
        elif intensity < 0.8:
            scale = 1.5
        else:
            scale = 2.0

        return (
            trust + adjustments["trust"] * scale,
            stress + adjustments["stress"] * scale,
            energy + adjustments["energy"] * scale,
            confidence + adjustments["confidence"] * scale,
            curiosity + adjustments["curiosity"] * scale,
        )

    # ------------------------------------------------------------------
    # Internal — mood computation
    # ------------------------------------------------------------------

    def _compute_mood(
        self,
        current_mood: str,
        category: str,
        intensity: float,
        trust: float,
        stress: float,
        energy: float,
        confidence: float,
        curiosity: float,
    ) -> str:
        """Compute the new mood from the updated numeric state.

        First checks for category-driven overrides, then evaluates
        transition rules, and finally falls back to a derivation from
        numeric values.
        """
        if category in _CATEGORY_MOOD_MAP:
            candidate = _CATEGORY_MOOD_MAP[category]
            if intensity >= 0.5:
                return self._validate_mood(candidate)

        # Transition rules — evaluate trigger conditions
        new_mood = self._evaluate_transitions(
            current_mood, trust, stress, energy, confidence, curiosity,
        )
        if new_mood is not None:
            return self._validate_mood(new_mood)

        # Fallback: derive from numeric state
        return self._validate_mood(self._derive_mood(stress, energy, confidence, trust, curiosity))

    def _evaluate_transitions(
        self,
        current_mood: str,
        trust: float,
        stress: float,
        energy: float,
        confidence: float,
        curiosity: float,
    ) -> str | None:
        """Evaluate transition rules for the current mood.

        Returns a new mood string if a rule fires, or ``None`` if no
        rule matches (caller should fall back to derivation).
        """
        if current_mood == "neutral":
            if stress > 0.5:
                return "anxious"
            if energy < 0.3:
                return "tired"
            if curiosity > 0.7:
                return "curious"
            if energy > 0.6 and confidence > 0.5:
                return "hopeful"

        elif current_mood == "happy":
            if stress > 0.6:
                return "anxious"
            if energy < 0.3:
                return "tired"

        elif current_mood == "sad":
            if confidence > 0.7:
                return "hopeful"
            if energy < 0.2:
                return "exhausted"

        elif current_mood == "anxious":
            if trust > 0.7:
                return "neutral"

        elif current_mood == "angry":
            if energy < 0.3:
                return "frustrated"

        elif current_mood == "curious":
            if energy < 0.3:
                return "tired"

        elif current_mood in ("exhausted", "tired"):
            if energy > 0.5:
                return "neutral"

        return None

    @staticmethod
    def _derive_mood(
        stress: float,
        energy: float,
        confidence: float,
        trust: float,
        curiosity: float,
    ) -> str:
        """Derive a mood from the numeric state when no transition fires."""
        if stress > 0.7:
            return "stressed"
        if stress > 0.5:
            return "anxious"
        if energy < 0.2:
            return "exhausted"
        if energy < 0.4:
            return "tired"
        if confidence < 0.2:
            return "sad"
        if confidence > 0.8 and trust > 0.7:
            return "happy"
        if curiosity > 0.8:
            return "curious"
        return "neutral"

    # ------------------------------------------------------------------
    # Internal — utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_mood(mood: str) -> str:
        """Validate a mood value against the known vocabulary.

        Returns the input if valid, ``"neutral"`` otherwise.
        """
        mood_lower = mood.lower().strip()
        if mood_lower in _ALL_KNOWN_MOODS:
            return mood_lower
        logger.warning("Unknown mood '%s' — falling back to 'neutral'", mood)
        return "neutral"

    @staticmethod
    def _clamp(value: float) -> float:
        """Clamp a float to the ``[0.0, 1.0]`` range."""
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value
