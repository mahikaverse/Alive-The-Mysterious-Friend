"""Memory ranking.

Scores and ranks memories by relevance and importance
to surface the most meaningful content for prompt building.
"""

import logging

logger = logging.getLogger(__name__)


class MemoryRanking:
    """Ranks memory items by relevance and importance."""

    def rank(self, memories: list, context: dict) -> list:
        """Rank a list of memories based on relevance to the current context."""
        pass

    def score(self, memory: dict, context: dict) -> float:
        """Compute a single relevance score for a memory."""
        pass
