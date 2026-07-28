"""Memory Store.

Provides the low-level persistence layer for memory records
using ChromaDB for vector storage and PostgreSQL for metadata.
"""

import logging
import uuid
from datetime import datetime, timezone

import chromadb

from backend.database.connection import DatabaseConnection
from backend.database.repositories import MemoryRepository
from backend.memory.embeddings import Embeddings

logger = logging.getLogger(__name__)


class MemoryStore:
    """Dual-store persistence layer for memory records.

    ChromaDB holds the vector embeddings for similarity search.
    PostgreSQL holds the structured metadata via MemoryRepository.
    """

    def __init__(
        self,
        embeddings: Embeddings,
        db: DatabaseConnection,
        chroma_path: str = "./chroma_db",
        collection_name: str = "alive_memories",
    ) -> None:
        self._embeddings = embeddings
        self._db = db
        self._repo = MemoryRepository(db)

        try:
            self._chroma_client = chromadb.PersistentClient(path=chroma_path)
            self._collection = self._chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "MemoryStore ready (chroma_path=%s, collection=%s)",
                chroma_path,
                collection_name,
            )
        except Exception as exc:
            logger.error("Failed to initialize ChromaDB: %s", exc)
            self._collection = None

    def save(self, memory: dict) -> str:
        """Persist a new memory record to both stores.

        Parameters
        ----------
        memory : dict
            Must contain 'content'. Optional: 'category', 'importance',
            'conversation_id', 'tags', 'metadata'.

        Returns
        -------
        str
            The memory record ID, or empty string on failure.
        """
        memory_id = memory.get("id") or str(uuid.uuid4())
        content = memory.get("content", "")

        if not content or not content.strip():
            logger.warning("Cannot save empty memory")
            return ""

        try:
            db_id = self._repo.add({
                "id": memory_id,
                "content": content,
                "category": memory.get("category", "general"),
                "importance": memory.get("importance", 0.0),
                "conversation_id": memory.get("conversation_id", ""),
                "tags": memory.get("tags"),
                "metadata": memory.get("metadata"),
            })

            if self._collection is not None:
                vector = self._embeddings.embed(content)
                self._collection.add(
                    ids=[memory_id],
                    embeddings=[vector],
                    documents=[content],
                    metadatas=[{
                        "category": memory.get("category", "general"),
                        "importance": memory.get("importance", 0.0),
                        "conversation_id": memory.get("conversation_id", ""),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }],
                )

            logger.debug("Memory saved: %s", memory_id)
            return memory_id
        except Exception as exc:
            logger.error("Failed to save memory: %s", exc)
            return ""

    def get(self, memory_id: str) -> dict | None:
        """Retrieve a single memory record by identifier."""
        try:
            record = self._repo.find_by_id(memory_id)
            if record is None:
                return None

            if self._collection is not None:
                chroma_result = self._collection.get(ids=[memory_id])
                if chroma_result and chroma_result["embeddings"]:
                    record["embedding"] = chroma_result["embeddings"][0]

            return record
        except Exception as exc:
            logger.error("Failed to get memory %s: %s", memory_id, exc)
            return None

    def delete(self, memory_id: str) -> bool:
        """Delete a memory record from both stores."""
        try:
            db_deleted = self._repo.delete(memory_id)

            if self._collection is not None:
                try:
                    self._collection.delete(ids=[memory_id])
                except Exception:
                    pass

            if db_deleted:
                logger.debug("Memory deleted: %s", memory_id)
            return db_deleted
        except Exception as exc:
            logger.error("Failed to delete memory %s: %s", memory_id, exc)
            return False

    def list_all(self, limit: int = 100) -> list[dict]:
        """Return all stored memory records."""
        return self._repo.find_all(limit=limit)

    def search_vectors(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """Search ChromaDB for similar vectors.

        Parameters
        ----------
        query_vector : list[float]
            The embedding vector to search against.
        top_k : int
            Number of results to return.

        Returns
        -------
        list[dict]
            List of matching records with ids, documents, distances, metadatas.
        """
        if self._collection is None:
            return []

        try:
            count = self._collection.count()
            if count == 0:
                return []

            actual_k = min(top_k, count)
            results = self._collection.query(
                query_embeddings=[query_vector],
                n_results=actual_k,
                include=["documents", "distances", "metadatas"],
            )

            memories = []
            if results and results["ids"] and results["ids"][0]:
                for i, mem_id in enumerate(results["ids"][0]):
                    memories.append({
                        "id": mem_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    })

            return memories
        except Exception as exc:
            logger.error("Vector search failed: %s", exc)
            return []

    def update(self, memory_id: str, updates: dict) -> bool:
        """Update an existing memory record."""
        try:
            db_updated = self._repo.update(memory_id, updates)

            if self._collection is not None and "content" in updates:
                vector = self._embeddings.embed(updates["content"])
                self._collection.update(
                    ids=[memory_id],
                    embeddings=[vector],
                    documents=[updates["content"]],
                )

            return db_updated
        except Exception as exc:
            logger.error("Failed to update memory %s: %s", memory_id, exc)
            return False
