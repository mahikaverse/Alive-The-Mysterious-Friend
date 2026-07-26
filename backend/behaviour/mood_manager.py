"""Mood Manager.

Centralised mood vocabulary, transitions, and derivation logic
for the Behaviour Layer.

Design
------
This module is the **single source of truth** for mood-related
constants and algorithms.  Other behaviour modules (EmotionEngine,
RelationshipEngine, StateManager) and core modules (ResponseValidator)
reference the vocabulary defined here rather than maintaining their
own copies.

The ``MoodManager`` class is a stateless utility — all methods are
pure functions of their inputs.  It does not hold mutable state
between calls; any stateful behaviour belongs in the caller.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mood vocabulary — canonical definitions
# ---------------------------------------------------------------------------

# All recognised mood strings.  Must stay synchronised with
# EmotionState.mood and ResponseValidator positive/negative sets.
ALL_MOODS: frozenset[str] = frozenset({
    "neutral", "happy", "excited", "hopeful", "joyful",
    "calm", "thoughtful", "curious", "bored", "tired",
    "exhausted", "confused", "sad", "angry", "frustrated",
    "anxious", "stressed",
})

# Positive moods — used by ResponseValidator and RelationshipEngine.
POSITIVE_MOODS: frozenset[str] = frozenset({
    "happy", "joyful", "excited", "hopeful",
})

# Negative moods — used by ResponseValidator and RelationshipEngine.
NEGATIVE_MOODS: frozenset[str] = frozenset({
    "sad", "angry", "frustrated", "anxious", "stressed",
})

# Moods that imply low energy.
_LOW_ENERGY_MOODS: frozenset[str] = frozenset({
    "tired", "exhausted", "bored", "sad", "calm",
})

# Moods that imply high arousal / activation.
_HIGH_AROUSAL_MOODS: frozenset[str] = frozenset({
    "angry", "anxious", "excited", "stressed", "frustrated",
})

# Default mood when an unrecognised value is encountered.
_DEFAULT_MOOD: str = "neutral"

# ---------------------------------------------------------------------------
# Category-to-mood mapping (stimulus-driven overrides)
# ---------------------------------------------------------------------------

CATEGORY_MOOD_MAP: dict[str, str] = {
    "hostile":           "angry",
    "emotional_sharing": "thoughtful",
    "question":          "curious",
    "humor":             "happy",
    "deep_topic":        "thoughtful",
    "topic_change":      "curious",
    "repetitive":        "bored",
    "silence":           "confused",
}

# ---------------------------------------------------------------------------
# Mood-to-adjective mapping (for prompt builder and response tone)
# ---------------------------------------------------------------------------

_MOOD_ADJECTIVES: dict[str, str] = {
    "neutral":     "calm",
    "happy":       "cheerful",
    "excited":     "enthusiastic",
    "hopeful":     "optimistic",
    "joyful":      "joyful",
    "calm":        "serene",
    "thoughtful":  "contemplative",
    "curious":     "inquisitive",
    "bored":       "indifferent",
    "tired":       "weary",
    "exhausted":   "drained",
    "confused":    "perplexed",
    "sad":         "melancholy",
    "angry":       "irritated",
    "frustrated":  "exasperated",
    "anxious":     "uneasy",
    "stressed":    "overwhelmed",
}

# ---------------------------------------------------------------------------
# Mood-to-energy mapping (baseline energy for each mood)
# ---------------------------------------------------------------------------

_MOOD_ENERGY: dict[str, float] = {
    "neutral":     0.5,
    "happy":       0.7,
    "excited":     0.9,
    "hopeful":     0.65,
    "joyful":      0.75,
    "calm":        0.4,
    "thoughtful":  0.45,
    "curious":     0.6,
    "bored":       0.25,
    "tired":       0.2,
    "exhausted":   0.1,
    "confused":    0.35,
    "sad":         0.3,
    "angry":       0.8,
    "frustrated":  0.7,
    "anxious":     0.6,
    "stressed":    0.55,
}

# ---------------------------------------------------------------------------
# Transition rules: (source_mood, condition_field, threshold, target_mood)
# Condition: if state[field] > threshold -> transition to target_mood.
# Negative threshold means "less than" (abs of threshold).
# ---------------------------------------------------------------------------

_TRANSITION_RULES: tuple[tuple[str, str, float, str], ...] = (
    # From neutral
    ("neutral", "stress",     0.5, "anxious"),
    ("neutral", "energy",    -0.3, "tired"),
    ("neutral", "curiosity",  0.7, "curious"),
    # From happy
    ("happy", "stress", 0.6, "anxious"),
    ("happy", "energy", -0.3, "tired"),
    # From sad
    ("sad", "confidence", 0.7, "hopeful"),
    ("sad", "energy",    -0.2, "exhausted"),
    # From anxious
    ("anxious", "trust", 0.7, "neutral"),
    # From angry
    ("angry", "energy", -0.3, "frustrated"),
    # From curious
    ("curious", "energy", -0.3, "tired"),
    # From exhausted/tired
    ("exhausted", "energy", 0.5, "neutral"),
    ("tired",     "energy", 0.5, "neutral"),
)

# Compound transition rules: (source_mood, conditions, target_mood)
# conditions is a dict of field -> (threshold, operator) where
# operator is ">" or "<".
_COMPOUND_TRANSITION_RULES: tuple[tuple[str, dict[str, tuple[float, str]], str], ...] = (
    # neutral + high energy + high confidence -> hopeful
    ("neutral", {"energy": (0.6, ">"), "confidence": (0.5, ">")}, "hopeful"),
)

# Thresholds for deriving mood from numeric state (descending priority).
_DERIVE_RULES: tuple[tuple[str, float, str], ...] = (
    ("stress",    0.7, "stressed"),
    ("stress",    0.5, "anxious"),
    ("energy",   -0.2, "exhausted"),   # negative = less than
    ("energy",   -0.4, "tired"),
    ("confidence", -0.2, "sad"),
    # Compound: confidence > 0.8 AND trust > 0.7 -> happy
    # (handled separately in derive_mood)
    ("curiosity", 0.8, "curious"),
)


# ---------------------------------------------------------------------------
# Public API — validation and normalisation
# ---------------------------------------------------------------------------

def validate_mood(mood: str | Any) -> str:
    """Validate and normalise a mood string.

    Returns the lowercased, stripped mood if it is in the known
    vocabulary, or ``_DEFAULT_MOOD`` otherwise.

    Parameters
    ----------
    mood:
        Any value — will be coerced to string.

    Returns
    -------
    str
        A valid mood string.
    """
    if not isinstance(mood, str):
        return _DEFAULT_MOOD
    normalised = mood.lower().strip()
    if normalised in ALL_MOODS:
        return normalised
    logger.debug("Unknown mood '%s' -- falling back to '%s'", mood, _DEFAULT_MOOD)
    return _DEFAULT_MOOD


def normalise_mood(mood: str | Any) -> str:
    """Alias for :func:`validate_mood` — normalise a mood input."""
    return validate_mood(mood)


def is_valid_mood(mood: str | Any) -> bool:
    """Return True if *mood* is a recognised mood string."""
    if not isinstance(mood, str):
        return False
    return mood.lower().strip() in ALL_MOODS


def is_positive(mood: str | Any) -> bool:
    """Return True if the mood is in the positive set."""
    return validate_mood(mood) in POSITIVE_MOODS


def is_negative(mood: str | Any) -> bool:
    """Return True if the mood is in the negative set."""
    return validate_mood(mood) in NEGATIVE_MOODS


# ---------------------------------------------------------------------------
# Public API — transition logic
# ---------------------------------------------------------------------------

def compute_mood_from_category(
    category: str,
    intensity: float = 0.5,
) -> str | None:
    """Look up the mood override for a stimulus category.

    Returns the mood string if the category has an override and
    *intensity* is above 0.5, or ``None`` if no override applies.
    """
    mood = CATEGORY_MOOD_MAP.get(category)
    if mood and intensity >= 0.5:
        return validate_mood(mood)
    return None


def evaluate_transitions(
    current_mood: str,
    state: dict[str, float] | None = None,
) -> str | None:
    """Evaluate transition rules for *current_mood*.

    Parameters
    ----------
    current_mood:
        The mood to evaluate transitions from.
    state:
        Numeric state dict with keys like ``"stress"``, ``"energy"``,
        ``"trust"``, ``"confidence"``, ``"curiosity"``.
        Values outside ``[-1.0, 1.0]`` are clamped.

    Returns
    -------
    str or None
        The target mood if a rule fires, or ``None`` if no rule matches.
    """
    if state is None:
        return None

    src = validate_mood(current_mood)

    for rule_src, field, threshold, target in _TRANSITION_RULES:
        if rule_src != src:
            continue

        value = state.get(field)
        if value is None or not isinstance(value, (int, float)):
            continue

        # Negative threshold means "less than" (abs of threshold).
        if threshold < 0:
            if value < abs(threshold):
                return validate_mood(target)
        else:
            if value > threshold:
                return validate_mood(target)

    # Compound rules — all conditions must be satisfied.
    for rule_src, conditions, target in _COMPOUND_TRANSITION_RULES:
        if rule_src != src:
            continue

        all_met = True
        for field, (threshold, op) in conditions.items():
            value = state.get(field)
            if value is None or not isinstance(value, (int, float)):
                all_met = False
                break
            if op == ">" and value <= threshold:
                all_met = False
                break
            if op == "<" and value >= threshold:
                all_met = False
                break

        if all_met:
            return validate_mood(target)

    return None


def derive_mood(
    stress: float = 0.0,
    energy: float = 0.7,
    confidence: float = 0.5,
    trust: float = 0.5,
    curiosity: float = 0.5,
) -> str:
    """Derive a mood from numeric state when no transition fires.

    Uses a priority-ordered evaluation.  Compound rules are checked
    after simple threshold rules.

    Parameters
    ----------
    stress, energy, confidence, trust, curiosity:
        Numeric state values (clamped internally to [0.0, 1.0]).

    Returns
    -------
    str
        A valid mood string.
    """
    stress = _clamp(stress)
    energy = _clamp(energy)
    confidence = _clamp(confidence)
    trust = _clamp(trust)
    curiosity = _clamp(curiosity)

    # Simple threshold rules (checked in priority order).
    for field_name, threshold, mood in _DERIVE_RULES:
        if threshold < 0:
            # "less than" rule
            val = {"stress": stress, "energy": energy, "confidence": confidence}.get(field_name, 0.0)
            if val < abs(threshold):
                return validate_mood(mood)
        else:
            val = {"stress": stress, "energy": energy, "curiosity": curiosity}.get(field_name, 0.0)
            if val > threshold:
                return validate_mood(mood)

    # Compound rule: high confidence + high trust -> happy
    if confidence > 0.8 and trust > 0.7:
        return "happy"

    return "neutral"


def transition(
    current_mood: str,
    state: dict[str, float] | None = None,
    category: str | None = None,
    intensity: float = 0.5,
) -> str:
    """Compute the next mood given the current state.

    Evaluation order:
    1. Category override (if *intensity* >= 0.5 and category has one).
    2. Transition rules for *current_mood*.
    3. Derivation from numeric state.
    4. Fallback to ``"neutral"``.

    Parameters
    ----------
    current_mood:
        The current mood string.
    state:
        Numeric state dict (stress, energy, confidence, trust, curiosity).
    category:
        Optional stimulus category override.
    intensity:
        Stimulus intensity on ``[0.0, 1.0]``.

    Returns
    -------
    str
        The new mood string, guaranteed to be in :data:`ALL_MOODS`.
    """
    # 1. Category override
    if category:
        override = compute_mood_from_category(category, intensity)
        if override is not None:
            return override

    # 2. Transition rules
    if state:
        target = evaluate_transitions(current_mood, state)
        if target is not None:
            return target

    # 3. Derive from numeric state
    if state:
        return derive_mood(
            stress=state.get("stress", 0.0),
            energy=state.get("energy", 0.7),
            confidence=state.get("confidence", 0.5),
            trust=state.get("trust", 0.5),
            curiosity=state.get("curiosity", 0.5),
        )

    return validate_mood(current_mood)


# ---------------------------------------------------------------------------
# Public API — prompt / tone helpers
# ---------------------------------------------------------------------------

def get_mood_adjective(mood: str | Any) -> str:
    """Return a descriptive adjective for the given mood.

    Parameters
    ----------
    mood:
        Any value — will be validated and normalised.

    Returns
    -------
    str
        An adjective suitable for inclusion in prompts or responses.
    """
    validated = validate_mood(mood)
    return _MOOD_ADJECTIVES.get(validated, "neutral")


def get_energy_level(mood: str | Any) -> float:
    """Return a baseline energy level for the given mood.

    Parameters
    ----------
    mood:
        Any value — will be validated and normalised.

    Returns
    -------
    float
        A value on ``[0.0, 1.0]`` representing expected energy.
    """
    validated = validate_mood(mood)
    return _MOOD_ENERGY.get(validated, 0.5)


def get_mood_sentiment(mood: str | Any) -> str:
    """Classify a mood as 'positive', 'negative', or 'neutral'.

    Parameters
    ----------
    mood:
        Any value — will be validated and normalised.

    Returns
    -------
    str
        One of ``"positive"``, ``"negative"``, ``"neutral"``.
    """
    validated = validate_mood(mood)
    if validated in POSITIVE_MOODS:
        return "positive"
    if validated in NEGATIVE_MOODS:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp *value* to ``[lo, hi]``."""
    if not isinstance(value, (int, float)):
        return lo
    v = float(value)
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


# ---------------------------------------------------------------------------
# Backward-compatible class wrapper
# ---------------------------------------------------------------------------

class MoodManager:
    """Thin wrapper around the module-level mood functions.

    Kept for backward compatibility with ``EmotionEngine`` which
    imports ``MoodManager``.  All methods delegate to the pure
    module-level functions above.
    """

    def transition(self, current_mood: str, stimulus: str) -> str:
        """Transition from *current_mood* based on a stimulus category."""
        return transition(current_mood, category=stimulus)

    def get_mood_adjective(self, mood: str = "neutral") -> str:
        """Return an adjective describing *mood*."""
        return get_mood_adjective(mood)

    def get_energy_level(self, mood: str = "neutral") -> float:
        """Return the energy level associated with *mood*."""
        return get_energy_level(mood)

    def validate(self, mood: str) -> str:
        """Validate and normalise a mood string."""
        return validate_mood(mood)

    def is_positive(self, mood: str) -> bool:
        """Return True if *mood* is positive."""
        return is_positive(mood)

    def is_negative(self, mood: str) -> bool:
        """Return True if *mood* is negative."""
        return is_negative(mood)
