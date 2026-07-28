"""Memory Manager.

Coordinates storage, retrieval, and ranking of memories
across the memory subsystem. This is the primary class
that satisfies the MemoryEngine Protocol.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from backend.memory.embeddings import Embeddings
from backend.memory.importance import ImportanceScorer
from backend.memory.memory_store import MemoryStore
from backend.memory.ranking import MemoryRanking
from backend.memory.retrieval import MemoryRetrieval

logger = logging.getLogger(__name__)


class MemoryManager:
    """High-level interface for the entire memory subsystem.

    Coordinates embeddings, storage, retrieval, importance scoring,
    and ranking to provide a simple ``retrieve`` / ``store`` / ``update``
    interface that satisfies the MemoryEngine Protocol.

    Usage::

        manager = MemoryManager(
            embeddings=embeddings,
            store=store,
            retrieval=retrieval,
            scorer=scorer,
            ranking=ranking,
        )
        memories = await manager.retrieve(conversation, current_message)
        await manager.store(conversation, response_text)
    """

    def __init__(
        self,
        embeddings: Embeddings,
        store: MemoryStore,
        retrieval: MemoryRetrieval,
        scorer: ImportanceScorer,
        ranking: MemoryRanking,
        top_k: int = 5,
    ) -> None:
        self._embeddings = embeddings
        self._store = store
        self._retrieval = retrieval
        self._scorer = scorer
        self._ranking = ranking
        self._top_k = top_k
        logger.info("MemoryManager ready (top_k=%d)", self._top_k)

    async def retrieve(self, conversation: list[dict], current_message: str) -> list[dict]:
        """Retrieve the most relevant memories for the current context.

        Parameters
        ----------
        conversation : list[dict]
            Full conversation history.
        current_message : str
            The latest user message.

        Returns
        -------
        list[dict]
            Ranked list of relevant memory dicts with 'content',
            'relevance_score', and 'id' fields.
        """
        try:
            query = self._build_query(conversation, current_message)
            if not query:
                return []

            raw_memories = await asyncio.to_thread(
                self._retrieval.hybrid_search, query, self._top_k * 2
            )

            if not raw_memories:
                return []

            context = self._build_context(conversation)
            ranked = await asyncio.to_thread(
                self._ranking.rank, raw_memories, context
            )

            top_memories = ranked[:self._top_k]

            formatted = []
            for mem in top_memories:
                formatted.append({
                    "id": mem.get("id", ""),
                    "content": mem.get("content", ""),
                    "relevance_score": mem.get("relevance_score", 0.0),
                    "category": mem.get("metadata", {}).get("category", "general"),
                })

            logger.debug(
                "Retrieved %d memories for query '%s...'",
                len(formatted),
                query[:50],
            )
            return formatted
        except Exception as exc:
            logger.error("Memory retrieval failed: %s", exc)
            return []

    async def store(self, conversation: list[dict], response: str) -> None:
        """Store important information derived from a conversation turn.

        Evaluates the last user message and the assistant response
        for importance, then stores significant content.

        Parameters
        ----------
        conversation : list[dict]
            Full conversation history.
        response : str
            The assistant's validated response.
        """
        try:
            user_message = self._extract_last_user_message(conversation)
            if not user_message and not response:
                return

            content_to_evaluate = self._combine_for_storage(user_message, response)
            context = self._build_context(conversation)
            importance = self._scorer.score(content_to_evaluate, context)

            if not self._scorer.should_store(importance):
                logger.debug(
                    "Content below importance threshold (%.3f) — skipping storage",
                    importance,
                )
                return

            conversation_id = self._generate_conversation_id(conversation)

            memory_entry = {
                "id": str(uuid.uuid4()),
                "content": content_to_evaluate,
                "category": self._categorize(content_to_evaluate),
                "importance": importance,
                "conversation_id": conversation_id,
                "tags": self._extract_tags(content_to_evaluate),
                "metadata": {
                    "source": "conversation",
                    "turn_count": len(conversation),
                },
            }

            memory_id = await asyncio.to_thread(
                self._store.save, memory_entry
            )
            if memory_id:
                logger.info(
                    "Memory stored: id=%s, importance=%.3f, category=%s",
                    memory_id,
                    importance,
                    memory_entry["category"],
                )
        except Exception as exc:
            logger.error("Memory storage failed: %s", exc)

    async def update(self, memory_id: str, updates: dict) -> None:
        """Update an existing memory record.

        Parameters
        ----------
        memory_id : str
            The memory to update.
        updates : dict
            Fields to update.
        """
        try:
            success = await asyncio.to_thread(
                self._store.update, memory_id, updates
            )
            if success:
                logger.debug("Memory updated: %s", memory_id)
            else:
                logger.warning("Memory update failed — not found: %s", memory_id)
        except Exception as exc:
            logger.error("Memory update failed for %s: %s", memory_id, exc)

    async def forget(self, memory_id: str) -> None:
        """Remove a memory from the store.

        Parameters
        ----------
        memory_id : str
            The memory to delete.
        """
        try:
            success = await asyncio.to_thread(
                self._store.delete, memory_id
            )
            if success:
                logger.debug("Memory forgotten: %s", memory_id)
            else:
                logger.warning("Memory forget failed — not found: %s", memory_id)
        except Exception as exc:
            logger.error("Memory forget failed for %s: %s", memory_id, exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_query(self, conversation: list[dict], current_message: str) -> str:
        """Build a search query from the current context."""
        if current_message and current_message.strip():
            return current_message.strip()

        if conversation:
            for msg in reversed(conversation):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    content = msg.get("content", "")
                    if content and content.strip():
                        return content.strip()

        return ""

    def _build_context(self, conversation: list[dict]) -> dict:
        """Build a context dict for scoring from conversation history."""
        return {
            "conversation_length": len(conversation),
            "turn_count": len([m for m in conversation if isinstance(m, dict) and m.get("role") == "user"]),
        }

    def _extract_last_user_message(self, conversation: list[dict]) -> str:
        """Extract the last user message from the conversation."""
        for msg in reversed(conversation):
            if isinstance(msg, dict) and msg.get("role") == "user":
                return msg.get("content", "")
        return ""

    def _combine_for_storage(self, user_message: str, response: str) -> str:
        """Combine user message and response for storage."""
        parts = []
        if user_message and user_message.strip():
            parts.append(f"User: {user_message.strip()}")
        if response and response.strip():
            parts.append(f"Alive: {response.strip()}")
        return "\n".join(parts)

    def _generate_conversation_id(self, conversation: list[dict]) -> str:
        """Generate a stable conversation ID from the message history."""
        if not conversation:
            return str(uuid.uuid4())

        first_msg = conversation[0] if conversation else {}
        content = first_msg.get("content", "") if isinstance(first_msg, dict) else ""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"conv_{hash(content) % 100000:05d}_{timestamp}"

    def _categorize(self, content: str) -> str:
        """Assign a category to the memory based on content."""
        text = content.lower()

        if any(w in text for w in ("name", "age", "birthday", "born", "live")):
            return "personal"
        if any(w in text for w in ("love", "hate", "feel", "emotion", "happy", "sad")):
            return "emotional"
        if any(w in text for w in ("hobby", "music", "movie", "game", "sport")):
            return "interest"
        if any(w in text for w in ("work", "job", "school", "university", "career")):
            return "activity"
        if any(w in text for w in ("family", "friend", "mother", "father")):
            return "relationship"
        if "?" in content:
            return "question"

        return "general"

    def _extract_tags(self, content: str) -> dict:
        """Extract simple tags from content."""
        text = content.lower()
        tags = {}

        topic_keywords = {
            "personal": ("name", "age", "birthday", "born", "live"),
            "emotional": ("love", "hate", "feel", "emotion", "happy", "sad"),
            "interest": ("hobby", "music", "movie", "game", "sport"),
            "work": ("work", "job", "school", "university", "career"),
            "family": ("family", "friend", "mother", "father"),
        }

        for tag, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                tags[tag] = True

        return tags
