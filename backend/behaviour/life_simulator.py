"""Life Stream.

Simulates a fictional daily life with activities,
personal experiences, and events.

Implements the LifeSimulator Protocol defined in
backend/controllers/interfaces.py and integrates with the
ConversationController pipeline.

Design
------
Stateful generator that maintains a rolling window of recent
activities and generates new events based on a simulated daily
rhythm.  The character can reference these events naturally in
conversation to feel more alive.

Time-of-day is driven by an internal turn counter (not wall-clock
time) so that behaviour is deterministic and reproducible within a
single session.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Activity pools by time-of-day category
# ---------------------------------------------------------------------------

_ACTIVITIES: dict[str, tuple[str, ...]] = {
    "morning": (
        "Woke up to sunlight streaming through the window",
        "Made a fresh cup of coffee",
        "Checked the weather outside",
        "Read the morning news",
        "Stretched and got ready for the day",
    ),
    "afternoon": (
        "Had a productive work session",
        "Took a walk around the neighbourhood",
        "Met a friend for lunch",
        "Worked on a creative project",
        "Learned something new today",
    ),
    "evening": (
        "Cooked dinner from scratch",
        "Watched the sunset",
        "Read a few chapters of a book",
        "Listened to a great album",
        "Reflected on the day",
    ),
    "night": (
        "Had a late-night conversation",
        "Stargazed for a while",
        "Worked on a hobby",
        "Enjoyed some quiet time",
        "Thought about tomorrow",
    ),
    "general": (
        "Discovered a new song I love",
        "Had an interesting thought",
        "Saw something beautiful outside",
        "Tried a new recipe",
        "Organized my workspace",
        "Found an old photo that made me smile",
        "Had a moment of peace",
        "Dreamed about something interesting",
        "Learned a fun fact",
        "Made someone smile today",
    ),
}

# Emotional flavour appended to activities (with leading space for grammar).
_EMOTIONAL_TAGS: tuple[str, ...] = (
    ". It felt really nice",
    ". It was oddly satisfying",
    ". I enjoyed that moment",
    ". It gave me something to think about",
    ". It was a small but meaningful thing",
)

# Time-of-day rotation order — cycles through these in sequence.
_TIME_CYCLE: tuple[str, ...] = ("morning", "afternoon", "evening", "night")

# How often (in turns) to generate a new event.
_EVENT_INTERVAL: int = 3

# Seeded event count on first call.
_SEED_COUNT: int = 3

# Maximum events in the rolling window.
_MAX_RECENT_EVENTS: int = 15

# Maximum event history.
_MAX_EVENT_HISTORY: int = 100

# How many recent events to track for deduplication.
_DEDUP_WINDOW: int = 30


class LifeSimulator:
    """Generates and manages fictional life events.

    Maintains an internal event log and generates new activities
    based on a simulated daily rhythm.  ``get_recent_events()`` returns
    a rolling window of the most recent activities that the character
    can reference in conversation.
    """

    def __init__(self) -> None:
        self._recent_events: deque[str] = deque(maxlen=_MAX_RECENT_EVENTS)
        self._event_history: deque[str] = deque(maxlen=_MAX_EVENT_HISTORY)
        self._seen_recent: deque[str] = deque(maxlen=_DEDUP_WINDOW)
        self._turn_count: int = 0
        self._time_index: int = 0
        self._initialised: bool = False
        logger.info("LifeSimulator ready")

    # ------------------------------------------------------------------
    # Protocol method
    # ------------------------------------------------------------------

    async def get_recent_events(self) -> list[str]:
        """Return the most recent life events.

        Returns
        -------
        list[str]
            A list of recent activity strings, ordered from most recent
            to oldest.  The controller assigns this to
            ``ctx.life_events.recent_activities``.
        """
        if not self._initialised:
            self._seed_initial_events()
            self._initialised = True

        self._turn_count += 1
        if self._turn_count % _EVENT_INTERVAL == 0:
            event = self._generate_event()
            self._add_event(event)

        return list(self._recent_events)

    # ------------------------------------------------------------------
    # Legacy helpers (kept for backward compatibility)
    # ------------------------------------------------------------------

    def get_event_history(self) -> list[str]:
        """Return the full event history."""
        return list(self._event_history)

    def add_event(self, event: str) -> None:
        """Record a new life event externally."""
        if isinstance(event, str) and event.strip():
            self._add_event(event.strip())

    # ------------------------------------------------------------------
    # Internal — event generation
    # ------------------------------------------------------------------

    def _generate_event(self) -> str:
        """Generate a single life event, avoiding recent duplicates."""
        time_of_day = _TIME_CYCLE[self._time_index % len(_TIME_CYCLE)]
        self._time_index += 1

        pool = _ACTIVITIES.get(time_of_day, _ACTIVITIES["general"])

        # Prefer activities not seen recently
        unseen = [a for a in pool if a not in self._seen_recent]
        if not unseen:
            # All activities seen recently — pick randomly from full pool
            unseen = list(pool)

        activity = unseen[self._turn_count % len(unseen)]

        # Occasionally append an emotional tag
        if self._turn_count % 4 == 0:
            tag = _EMOTIONAL_TAGS[self._turn_count % len(_EMOTIONAL_TAGS)]
            activity = f"{activity}{tag}"

        return activity

    def _seed_initial_events(self) -> None:
        """Seed the event log with a few initial activities."""
        for _ in range(_SEED_COUNT):
            event = self._generate_event()
            self._add_event(event)

    def _add_event(self, event: str) -> None:
        """Add an event to the rolling window, history, and dedup tracker."""
        self._recent_events.append(event)
        self._event_history.append(event)
        self._seen_recent.append(event)

    # ------------------------------------------------------------------
    # Internal — utilities
    # ------------------------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        """Return the full simulator state (for testing/debugging)."""
        return {
            "recent_events": list(self._recent_events),
            "event_history": list(self._event_history),
            "turn_count": self._turn_count,
        }
