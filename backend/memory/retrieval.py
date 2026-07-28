"""Memory retrieval.

Implements semantic and similarity-based retrieval
of relevant memories from the vector store.
"""

import logging

from backend.memory.embeddings import Embeddings
from backend.memory.memory_store import MemoryStore

logger = logging.getLogger(__name__)


class MemoryRetrieval:
    """Semantic retrieval engine for querying relevant memories.

    Uses ChromaDB cosine similarity via MemoryStore.search_vectors()
    to find memories that are semantically close to the query.
    """

    def __init__(self, store: MemoryStore, embeddings: Embeddings) -> None:
        self._store = store
        self._embeddings = embeddings

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search for memories semantically similar to the query.

        Parameters
        ----------
        query : str
            The text to search for.
        top_k : int
            Maximum number of results.

        Returns
        -------
        list[dict]
            Matching memories with content, distance, and metadata.
        """
        if not query or not query.strip():
            return []

        try:
            query_vector = self._embeddings.embed(query)
            results = self._store.search_vectors(query_vector, top_k=top_k)
            logger.debug("Semantic search returned %d results for query '%s...'", len(results), query[:50])
            return results
        except Exception as exc:
            logger.error("Semantic search failed: %s", exc)
            return []

    def hybrid_search(self, query: str, top_k: int = 5) -> list[dict]:
        """Combine semantic and keyword-based search for better results.

        Runs semantic search, then re-ranks results by also considering
        keyword overlap between the query and memory content.

        Parameters
        ----------
        query : str
            The text to search for.
        top_k : int
            Maximum number of results.

        Returns
        -------
        list[dict]
            Re-ranked matching memories.
        """
        results = self.search(query, top_k=top_k * 2)

        if not results:
            return []

        query_words = set(query.lower().split())

        for memory in results:
            content_words = set(memory.get("content", "").lower().split())
            keyword_overlap = len(query_words & content_words) / max(len(query_words), 1)
            distance = memory.get("distance", 1.0)
            semantic_score = 1.0 - min(distance, 1.0)
            memory["hybrid_score"] = 0.7 * semantic_score + 0.3 * keyword_overlap

        results.sort(key=lambda m: m.get("hybrid_score", 0), reverse=True)
        return results[:top_k]

    def search_by_tags(self, tags: list[str], top_k: int = 10) -> list[dict]:
        """Retrieve memories matching a set of tags.

        Parameters
        ----------
        tags : list[str]
            Tags to filter by.
        top_k : int
            Maximum number of results.

        Returns
        -------
        list[dict]
            Memories that contain any of the specified tags.
        """
        if not tags:
            return []

        try:
            all_memories = self._store.list_all(limit=500)
            tag_set = {t.lower() for t in tags}

            matched = []
            for memory in all_memories:
                memory_tags = memory.get("tags") or {}
                if isinstance(memory_tags, dict):
                    memory_tag_set = {v.lower() for v in memory_tags.values() if isinstance(v, str)}
                elif isinstance(memory_tags, list):
                    memory_tag_set = {str(v).lower() for v in memory_tags}
                else:
                    memory_tag_set = set()

                if tag_set & memory_tag_set:
                    matched.append(memory)

            logger.debug("Tag search found %d results for tags %s", len(matched), tags)
            return matched[:top_k]
        except Exception as exc:
            logger.error("Tag search failed: %s", exc)
            return []
