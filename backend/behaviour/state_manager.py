"""State Manager.

Maintains and persists the overall behavioural state
across sessions.
"""

import logging

logger = logging.getLogger(__name__)


class StateManager:
    """Persists and restores the full behavioural state."""

    def save_state(self) -> None:
        """Persist the current behavioural state to storage."""
        pass

    def load_state(self) -> None:
        """Restore a previously saved behavioural state."""
        pass

    def reset_state(self) -> None:
        """Reset the behavioural state to defaults."""
        pass
