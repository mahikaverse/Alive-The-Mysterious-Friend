"""Memory ranking.

Scores and ranks memories by relevance and importance
to surface the most meaningful content for prompt building.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Weights for multi-factor ranking
_SIMILARITY_WEIGHT = 0.5
_RECENCY_WEIGHT = 0.25
_IMPORTANCE_WEIGHT = 0.25


class MemoryRanking:
    """Ranks memory items by relevance and importance.

    Combines three signals:
    1. Semantic similarity (from ChromaDB cosine distance)
    2. Recency (newer memories rank higher)
    3. Importance score (from ImportanceScorer)
    """

    def __init__(
        self,
        similarity_weight: float = _SIMILARITY_WEIGHT,
        recency_weight: float = _RECENCY_WEIGHT,
        importance_weight: float = _IMPORTANCE_WEIGHT,
    ) -> None:
        total = similarity_weight + recency_weight + importance_weight
        if total > 0:
            self._sim_w = similarity_weight / total
            self._rec_w = recency_weight / total
            self._imp_w = importance_weight / total
        else:
            self._sim_w = _SIMILARITY_WEIGHT
            self._rec_w = _RECENCY_WEIGHT
            self._imp_w = _IMPORTANCE_WEIGHT

    def rank(self, memories: list[dict], context: dict | None = None) -> list[dict]:
        """Rank a list of memories based on relevance to the current context.

        Parameters
        ----------
        memories : list[dict]
            Memories to rank. Each should have 'distance' (from ChromaDB),
            'content', and optionally 'metadata' with 'importance' and
            'created_at'.
        context : dict | None
            Optional context for relevance scoring.

        Returns
        -------
        list[dict]
            Memories sorted by combined score (highest first), each
            with a 'relevance_score' field added.
        """
        if not memories:
            return []

        scored = []
        for memory in memories:
            score = self.score(memory, context)
            memory_copy = dict(memory)
            memory_copy["relevance_score"] = score
            scored.append(memory_copy)

        scored.sort(key=lambda m: m["relevance_score"], reverse=True)
        return scored

    def score(self, memory: dict, context: dict | None = None) -> float:
        """Compute a single relevance score for a memory.

        Parameters
        ----------
        memory : dict
            The memory to score.
        context : dict | None
            Optional context.

        Returns
        -------
        float
            Combined relevance score between 0.0 and 1.0.
        """
        similarity = self._similarity_score(memory)
        recency = self._recency_score(memory)
        importance = self._importance_score(memory)

        combined = (
            self._sim_w * similarity
            + self._rec_w * recency
            + self._imp_w * importance
        )

        return round(min(combined, 1.0), 4)

    def _similarity_score(self, memory: dict) -> float:
        """Convert ChromaDB cosine distance to a similarity score."""
        distance = memory.get("distance", 1.0)
        return max(0.0, 1.0 - min(distance, 1.0))

    def _recency_score(self, memory: dict) -> float:
        """Score based on how recently the memory was created."""
        metadata = memory.get("metadata", {})
        created_at_str = metadata.get("created_at", "")

        if not created_at_str:
            return 0.5

        try:
            created_at = datetime.fromisoformat(created_at_str)
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            age_hours = max((now - created_at).total_seconds() / 3600, 0)

            if age_hours < 1:
                return 1.0
            elif age_hours < 24:
                return 0.9
            elif age_hours < 168:  # 1 week
                return 0.7
            elif age_hours < 720:  # 1 month
                return 0.5
            else:
                return 0.3
        except (ValueError, TypeError):
            return 0.5

    def _importance_score(self, memory: dict) -> float:
        """Extract importance score from memory metadata."""
        metadata = memory.get("metadata", {})
        importance = metadata.get("importance", 0.0)

        if isinstance(importance, (int, float)):
            return max(0.0, min(float(importance), 1.0))
        return 0.5
