"""Importance scoring.

Evaluates how important a piece of information is
to decide which memories should be retained long-term.
"""

import logging

logger = logging.getLogger(__name__)


class ImportanceScorer:
    """Scores the importance of information for long-term retention."""

    def score(self, content: str, context: dict) -> float:
        """Compute an importance score for the given content."""
        pass

    def should_store(self, score: float, threshold: float = 0.5) -> bool:
        """Determine whether content exceeds the storage threshold."""
        pass
