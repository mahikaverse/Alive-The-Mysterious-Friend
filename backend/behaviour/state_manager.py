"""State Manager.

Internal utility for the Behaviour Layer that validates, snapshots,
and manages combined behaviour state across the emotion, relationship,
and life-simulation modules.

Design
------
This is a **Person 4 internal utility**, not a pipeline module.  It has
no Protocol in ``interfaces.py`` and is not called by the controller.
Other behaviour modules may optionally use it for:

- validating state consistency after mutations
- capturing point-in-time snapshots for debugging/auditing
- maintaining a bounded history of state changes for long conversations
- providing safe access to state fields with defensive fallbacks

The class is designed to be instantiated once per conversation session
and reused across pipeline turns.  It is **not** thread-safe for
concurrent access to the same instance; each request should have its
own ``StateManager``.
"""

from __future__ import annotations

import copy
import logging
from collections import deque
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

_MAX_HISTORY: int = 50
_SNAPSHOT_INTERVAL: int = 1

# Valid mood values — matches EmotionState and ResponseValidator vocabulary.
_VALID_MOODS: frozenset[str] = frozenset({
    "neutral", "happy", "excited", "hopeful", "joyful",
    "calm", "thoughtful", "curious", "bored", "tired",
    "exhausted", "confused", "sad", "angry", "frustrated",
    "anxious", "stressed",
})

# Field boundaries — matches Pydantic Field constraints in state.py.
_FIELD_BOUNDS: dict[str, tuple[float, float]] = {
    "trust":           (0.0, 1.0),
    "stress":          (0.0, 1.0),
    "energy":          (0.0, 1.0),
    "confidence":      (0.0, 1.0),
    "curiosity":       (0.0, 1.0),
    "friendship_score": (0.0, 1.0),
}

# Relationship fields that must be non-negative integers.
_INT_FIELDS: frozenset[str] = frozenset({"conversation_count"})


# ---------------------------------------------------------------------------
# Snapshot model
# ---------------------------------------------------------------------------

class BehaviourSnapshot(BaseModel):
    """Point-in-time capture of the full behaviour state."""

    turn: int = 0
    emotion: dict[str, Any] = Field(default_factory=dict)
    relationship: dict[str, Any] = Field(default_factory=dict)
    life_events: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

class ValidationResult:
    """Result of a state validation check."""

    __slots__ = ("is_valid", "errors", "warnings")

    def __init__(
        self,
        is_valid: bool = True,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def __repr__(self) -> str:
        status = "VALID" if self.is_valid else "INVALID"
        return (
            f"ValidationResult({status}, "
            f"errors={len(self.errors)}, warnings={len(self.warnings)})"
        )


# ---------------------------------------------------------------------------
# State Manager
# ---------------------------------------------------------------------------

class StateManager:
    """Manages combined behaviour state for a single conversation session.

    Usage::

        sm = StateManager()
        # After each pipeline turn:
        snapshot = sm.capture(emotion_dict, relationship_dict, life_dict)
        result = sm.validate(snapshot)
        if not result.is_valid:
            logger.warning("State issues: %s", result.errors)

    Thread safety
    -------------
    Each ``StateManager`` instance is **not** safe for concurrent access
    from multiple asyncio tasks.  Create one instance per request / per
    conversation session.
    """

    def __init__(self, max_history: int = _MAX_HISTORY) -> None:
        self._turn: int = 0
        self._max_history: int = max(1, max_history)
        self._history: deque[BehaviourSnapshot] = deque(maxlen=self._max_history)
        self._last_snapshot: BehaviourSnapshot | None = None
        logger.info("StateManager ready (max_history=%d)", self._max_history)

    # ------------------------------------------------------------------
    # Public API — capture
    # ------------------------------------------------------------------

    def capture(
        self,
        emotion: dict[str, Any] | None = None,
        relationship: dict[str, Any] | None = None,
        life_events: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BehaviourSnapshot:
        """Capture a point-in-time snapshot of the behaviour state.

        Parameters
        ----------
        emotion:
            Serialised ``EmotionState`` (from ``model_dump()``).
        relationship:
            Serialised ``RelationshipState`` (from ``model_dump()``).
        life_events:
            Serialised ``LifeContext`` (from ``model_dump()``).
        metadata:
            Optional extra data to attach to the snapshot.

        Returns
        -------
        BehaviourSnapshot
            A frozen copy of the state at this turn.
        """
        self._turn += 1

        snapshot = BehaviourSnapshot(
            turn=self._turn,
            emotion=self._defensive_copy(emotion or {}),
            relationship=self._defensive_copy(relationship or {}),
            life_events=self._defensive_copy(life_events or {}),
            metadata=self._defensive_copy(metadata or {}),
        )

        self._history.append(snapshot)
        self._last_snapshot = snapshot

        logger.debug(
            "State captured at turn %d (history=%d)",
            self._turn,
            len(self._history),
        )
        return snapshot

    # ------------------------------------------------------------------
    # Public API — validate
    # ------------------------------------------------------------------

    def validate(self, snapshot: BehaviourSnapshot | None = None) -> ValidationResult:
        """Validate the behaviour state for consistency and correctness.

        Parameters
        ----------
        snapshot:
            The snapshot to validate.  If ``None``, validates the most
            recent capture.

        Returns
        -------
        ValidationResult
            Contains ``is_valid``, ``errors``, and ``warnings``.
        """
        target = snapshot or self._last_snapshot
        if target is None:
            return ValidationResult(
                is_valid=False,
                errors=["No state captured yet — call capture() first"],
            )

        errors: list[str] = []
        warnings: list[str] = []

        self._validate_emotion(target.emotion, errors, warnings)
        self._validate_relationship(target.relationship, errors, warnings)
        self._validate_life_events(target.life_events, errors, warnings)
        self._validate_cross_consistency(target, errors, warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Public API — safe access
    # ------------------------------------------------------------------

    def get_emotion_field(
        self,
        field: str,
        default: Any = None,
        snapshot: BehaviourSnapshot | None = None,
    ) -> Any:
        """Safely access a field from the emotion state.

        Returns *default* if the field is missing or the snapshot
        has no emotion data.
        """
        target = snapshot or self._last_snapshot
        if target is None:
            return default
        return target.emotion.get(field, default)

    def get_relationship_field(
        self,
        field: str,
        default: Any = None,
        snapshot: BehaviourSnapshot | None = None,
    ) -> Any:
        """Safely access a field from the relationship state."""
        target = snapshot or self._last_snapshot
        if target is None:
            return default
        return target.relationship.get(field, default)

    def get_mood(self, snapshot: BehaviourSnapshot | None = None) -> str:
        """Return the current mood, falling back to 'neutral'."""
        mood = self.get_emotion_field("mood", "neutral", snapshot)
        return str(mood).lower().strip() if mood else "neutral"

    def get_trust(self, snapshot: BehaviourSnapshot | None = None) -> float:
        """Return the current trust level, clamped to [0.0, 1.0]."""
        return self._safe_float(
            self.get_relationship_field("trust", 0.0, snapshot),
            0.0,
        )

    def get_friendship(self, snapshot: BehaviourSnapshot | None = None) -> float:
        """Return the current friendship score, clamped to [0.0, 1.0]."""
        return self._safe_float(
            self.get_relationship_field("friendship_score", 0.0, snapshot),
            0.0,
        )

    def get_energy(self, snapshot: BehaviourSnapshot | None = None) -> float:
        """Return the current energy level, clamped to [0.0, 1.0]."""
        return self._safe_float(
            self.get_emotion_field("energy", 0.7, snapshot),
            0.7,
        )

    def get_conversation_count(self, snapshot: BehaviourSnapshot | None = None) -> int:
        """Return the total conversation count."""
        target = snapshot or self._last_snapshot
        if target is None:
            return 0
        count = target.relationship.get("conversation_count", 0)
        return max(0, int(count)) if isinstance(count, (int, float)) else 0

    # ------------------------------------------------------------------
    # Public API — history
    # ------------------------------------------------------------------

    def get_history(self) -> list[BehaviourSnapshot]:
        """Return a copy of the state history."""
        return list(self._history)

    def get_last_snapshot(self) -> BehaviourSnapshot | None:
        """Return the most recent snapshot, or None."""
        return self._last_snapshot

    def get_turn(self) -> int:
        """Return the current turn number."""
        return self._turn

    def get_field_delta(
        self,
        category: str,
        field: str,
        turns_back: int = 1,
    ) -> float | None:
        """Return the change in a numeric field over *turns_back* turns.

        Parameters
        ----------
        category:
            One of ``"emotion"``, ``"relationship"``, ``"life_events"``.
        field:
            The field name within the category dict.
        turns_back:
            How many turns to look back (1 = previous turn).

        Returns
        -------
        float or None
            The delta (current - previous), or ``None`` if insufficient
            history exists.
        """
        if len(self._history) < turns_back + 1:
            return None

        current = self._history[-1]
        previous = self._history[-(turns_back + 1)]

        current_data = getattr(current, category, {})
        previous_data = getattr(previous, category, {})

        current_val = current_data.get(field)
        previous_val = previous_data.get(field)

        if not isinstance(current_val, (int, float)) or not isinstance(previous_val, (int, float)):
            return None

        return float(current_val) - float(previous_val)

    # ------------------------------------------------------------------
    # Public API — reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset the state manager to its initial state."""
        self._turn = 0
        self._history.clear()
        self._last_snapshot = None
        logger.info("StateManager reset")

    # ------------------------------------------------------------------
    # Internal — validation
    # ------------------------------------------------------------------

    def _validate_emotion(
        self,
        data: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate the emotion state dict."""
        if not data:
            warnings.append("Emotion state is empty")
            return

        mood = data.get("mood", "neutral")
        if isinstance(mood, str) and mood.lower().strip() not in _VALID_MOODS:
            warnings.append(f"Unknown mood '{mood}' — not in known vocabulary")

        for field, (lo, hi) in _FIELD_BOUNDS.items():
            if field in data:
                val = data[field]
                if not isinstance(val, (int, float)):
                    errors.append(f"emotion.{field} must be numeric, got {type(val).__name__}")
                elif val < lo or val > hi:
                    errors.append(f"emotion.{field} out of range: {val} (expected [{lo}, {hi}])")

    def _validate_relationship(
        self,
        data: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate the relationship state dict."""
        if not data:
            warnings.append("Relationship state is empty")
            return

        for field, (lo, hi) in _FIELD_BOUNDS.items():
            if field in data:
                val = data[field]
                if not isinstance(val, (int, float)):
                    errors.append(f"relationship.{field} must be numeric, got {type(val).__name__}")
                elif val < lo or val > hi:
                    errors.append(f"relationship.{field} out of range: {val} (expected [{lo}, {hi}])")

        count = data.get("conversation_count")
        if count is not None:
            if not isinstance(count, (int, float)):
                errors.append(
                    f"relationship.conversation_count must be int, got {type(count).__name__}"
                )
            elif count < 0:
                errors.append(
                    f"relationship.conversation_count negative: {count}"
                )

        experiences = data.get("shared_experiences")
        if experiences is not None and not isinstance(experiences, list):
            errors.append(
                f"relationship.shared_experiences must be list, got {type(experiences).__name__}"
            )

    def _validate_life_events(
        self,
        data: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate the life events state dict."""
        if not data:
            warnings.append("Life events state is empty")
            return

        for key in ("recent_activities", "ongoing_events", "daily_routine"):
            if key in data:
                val = data[key]
                if not isinstance(val, list):
                    errors.append(f"life_events.{key} must be list, got {type(val).__name__}")

    def _validate_cross_consistency(
        self,
        snapshot: BehaviourSnapshot,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate cross-field consistency across categories."""
        emotion = snapshot.emotion
        relationship = snapshot.relationship

        # Trust consistency: emotion.trust and relationship.trust should
        # not diverge by more than 0.5 (they model related but distinct
        # concepts, so some divergence is expected).
        e_trust = emotion.get("trust")
        r_trust = relationship.get("trust")
        if isinstance(e_trust, (int, float)) and isinstance(r_trust, (int, float)):
            if abs(e_trust - r_trust) > 0.5:
                warnings.append(
                    f"Trust divergence: emotion.trust={e_trust:.2f} vs "
                    f"relationship.trust={r_trust:.2f} (delta={abs(e_trust - r_trust):.2f})"
                )

        # High stress + high energy is unusual but not invalid.
        stress = emotion.get("stress")
        energy = emotion.get("energy")
        if isinstance(stress, (int, float)) and isinstance(energy, (int, float)):
            if stress > 0.8 and energy > 0.8:
                warnings.append(
                    f"Unusual combination: high stress ({stress:.2f}) + high energy ({energy:.2f})"
                )

        # Negative friendship with high conversation count suggests
        # a deteriorating relationship.
        friendship = relationship.get("friendship_score")
        count = relationship.get("conversation_count")
        if isinstance(friendship, (int, float)) and isinstance(count, (int, float)):
            if friendship < 0.2 and count > 5:
                warnings.append(
                    f"Low friendship ({friendship:.2f}) after {int(count)} conversations "
                    "— relationship may be deteriorating"
                )

    # ------------------------------------------------------------------
    # Internal — utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _defensive_copy(data: Any) -> dict[str, Any]:
        """Return a deep copy of *data* as a dict, or an empty dict on failure.

        If *data* is not a dict-like object, returns an empty dict.
        """
        if not isinstance(data, dict):
            return {}
        try:
            return copy.deepcopy(data)
        except Exception:
            logger.debug("Defensive copy failed -- returning shallow copy")
            return dict(data)

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Convert *value* to float, clamping to [0.0, 1.0]."""
        try:
            result = float(value)
        except (TypeError, ValueError):
            return default
        if result < 0.0:
            return 0.0
        if result > 1.0:
            return 1.0
        return result
