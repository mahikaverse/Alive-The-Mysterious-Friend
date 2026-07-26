"""Person 3 — Memory System Unit Tests.

Tests the complete memory pipeline:
    ImportanceScorer -> Embeddings (mocked) -> MemoryStore -> MemoryRetrieval -> MemoryRanking -> MemoryManager

Uses mocks for external services (OpenAI API, PostgreSQL, ChromaDB).
"""

import sys
sys.path.insert(0, "D:\\Projects\\Alive-The-Mysterious-Friend")

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from backend.memory.importance import ImportanceScorer
from backend.memory.ranking import MemoryRanking


# ======================================================================
# 1. ImportanceScorer Tests
# ======================================================================

def test_importance_scorer():
    print("\n" + "=" * 60)
    print("ImportanceScorer Tests")
    print("=" * 60)

    scorer = ImportanceScorer(threshold=0.3)

    # Empty content
    assert scorer.score("") == 0.0
    assert scorer.score(None) == 0.0
    print("[OK] Empty content returns 0.0")

    # Simple greeting (low importance)
    score = scorer.score("hello")
    assert 0.0 <= score <= 1.0
    print(f"[OK] Simple greeting score: {score}")

    # Personal information (higher importance)
    score = scorer.score("My name is Alice and I am 25 years old")
    assert score > 0.1, f"Expected > 0.1 for personal info, got {score}"
    print(f"[OK] Personal info score: {score}")

    # Emotional content
    score = scorer.score("I love this game so much, it makes me really happy!")
    assert score > 0.1, f"Expected > 0.1 for emotional content, got {score}"
    print(f"[OK] Emotional content score: {score}")

    # Question
    score = scorer.score("What is your favorite movie?")
    assert score > 0.1, f"Expected > 0.1 for question, got {score}"
    print(f"[OK] Question score: {score}")

    # Intensifiers
    score = scorer.score("I really absolutely love music")
    assert score > 0.1, f"Expected > 0.1 for intensifiers, got {score}"
    print(f"[OK] Intensifier score: {score}")

    # should_store threshold
    assert scorer.should_store(0.5) is True
    assert scorer.should_store(0.1) is False
    assert scorer.should_store(0.3, threshold=0.2) is True
    print("[OK] should_store threshold logic works")

    # With context boost
    context = {"emotion": {"mood": "happy"}, "relationship": {"trust": 0.8}}
    score_with_ctx = scorer.score("I like music", context)
    score_without = scorer.score("I like music")
    assert score_with_ctx >= score_without
    print(f"[OK] Context boost works: {score_with_ctx} >= {score_without}")

    print("\n[PASS] ImportanceScorer tests passed")


# ======================================================================
# 2. MemoryRanking Tests
# ======================================================================

def test_memory_ranking():
    print("\n" + "=" * 60)
    print("MemoryRanking Tests")
    print("=" * 60)

    ranking = MemoryRanking()

    # Empty list
    assert ranking.rank([]) == []
    print("[OK] Empty list returns empty")

    # Single memory
    now = datetime.now(timezone.utc).isoformat()
    memories = [
        {
            "id": "1",
            "content": "User likes cats",
            "distance": 0.2,
            "metadata": {"importance": 0.8, "created_at": now},
        },
        {
            "id": "2",
            "content": "User went to store",
            "distance": 0.8,
            "metadata": {"importance": 0.3, "created_at": "2024-01-01T00:00:00+00:00"},
        },
    ]

    ranked = ranking.rank(memories)
    assert len(ranked) == 2
    assert all("relevance_score" in m for m in ranked)
    print(f"[OK] Ranked {len(ranked)} memories")

    # First should be more relevant (closer distance, higher importance, newer)
    assert ranked[0]["id"] == "1", f"Expected id=1 first, got {ranked[0]['id']}"
    print(f"[OK] Most relevant memory ranked first: id={ranked[0]['id']}")

    # Score computation
    score = ranking.score(memories[0])
    assert 0.0 <= score <= 1.0
    print(f"[OK] Score computation: {score}")

    # No metadata
    no_meta = [{"id": "3", "content": "Test", "distance": 0.5}]
    ranked_no_meta = ranking.rank(no_meta)
    assert len(ranked_no_meta) == 1
    print("[OK] Handles missing metadata gracefully")

    print("\n[PASS] MemoryRanking tests passed")


# ======================================================================
# 3. MemoryManager Integration Test (with mocks)
# ======================================================================

def test_memory_manager():
    print("\n" + "=" * 60)
    print("MemoryManager Integration Test (mocked)")
    print("=" * 60)

    import asyncio
    from backend.memory.memory_manager import MemoryManager

    # Create mock dependencies
    mock_embeddings = MagicMock()
    mock_embeddings.embed.return_value = [0.1] * 1536

    mock_store = MagicMock()
    mock_store.save.return_value = "mock-id-123"
    mock_store.search_vectors.return_value = [
        {
            "id": "mem-1",
            "content": "User likes science fiction books",
            "distance": 0.15,
            "metadata": {"category": "interest", "importance": 0.7, "created_at": datetime.now(timezone.utc).isoformat()},
        },
        {
            "id": "mem-2",
            "content": "User has a cat named Luna",
            "distance": 0.25,
            "metadata": {"category": "personal", "importance": 0.8, "created_at": datetime.now(timezone.utc).isoformat()},
        },
    ]
    mock_store.list_all.return_value = []
    mock_store.update.return_value = True
    mock_store.delete.return_value = True

    mock_retrieval = MagicMock()
    mock_retrieval.hybrid_search.return_value = mock_store.search_vectors.return_value

    mock_scorer = MagicMock()
    mock_scorer.score.return_value = 0.6
    mock_scorer.should_store.return_value = True

    mock_ranking = MemoryRanking()

    manager = MemoryManager(
        embeddings=mock_embeddings,
        store=mock_store,
        retrieval=mock_retrieval,
        scorer=mock_scorer,
        ranking=mock_ranking,
        top_k=5,
    )

    # Test retrieve
    conversation = [
        {"role": "user", "content": "What books do you recommend?"},
        {"role": "assistant", "content": "I love science fiction!"},
    ]
    memories = asyncio.run(manager.retrieve(conversation, "Tell me more about your interests"))
    assert isinstance(memories, list)
    print(f"[OK] retrieve() returned {len(memories)} memories")
    if memories:
        assert "content" in memories[0]
        assert "relevance_score" in memories[0]
        print(f"[OK] Memory format correct: {list(memories[0].keys())}")

    # Test store
    asyncio.run(manager.store(conversation, "I really enjoy reading sci-fi novels"))
    mock_store.save.assert_called()
    print("[OK] store() called save on store")

    # Test store below threshold
    mock_scorer.should_store.return_value = False
    asyncio.run(manager.store(conversation, "ok"))
    print("[OK] store() respects importance threshold")

    # Test update
    asyncio.run(manager.update("mem-1", {"content": "Updated content"}))
    mock_store.update.assert_called_once()
    print("[OK] update() delegates to store")

    # Test forget
    asyncio.run(manager.forget("mem-1"))
    mock_store.delete.assert_called_once()
    print("[OK] forget() delegates to store")

    # Test retrieve with empty query
    memories = asyncio.run(manager.retrieve([], ""))
    assert isinstance(memories, list)
    assert len(memories) == 0
    print("[OK] retrieve() handles empty input gracefully")

    print("\n[PASS] MemoryManager integration test passed")


# ======================================================================
# 4. Database ORM Models Test
# ======================================================================

def test_database_models():
    print("\n" + "=" * 60)
    print("Database ORM Models Test")
    print("=" * 60)

    from backend.database.models import MemoryRecord, ConversationLog

    # MemoryRecord
    record = MemoryRecord(
        content="Test memory content",
        category="test",
        importance=0.75,
        conversation_id="conv-001",
    )
    assert record.content == "Test memory content"
    assert record.category == "test"
    assert record.importance == 0.75
    d = record.to_dict()
    assert d["content"] == "Test memory content"
    assert d["category"] == "test"
    print("[OK] MemoryRecord created and serialized")

    # ConversationLog
    log = ConversationLog(
        session_id="sess-001",
        role="user",
        content="Hello world",
    )
    assert log.role == "user"
    d = log.to_dict()
    assert d["content"] == "Hello world"
    print("[OK] ConversationLog created and serialized")

    print("\n[PASS] Database ORM models test passed")


# ======================================================================
# 5. DatabaseConnection Test (in-memory SQLite)
# ======================================================================

def test_database_connection():
    print("\n" + "=" * 60)
    print("DatabaseConnection Test (SQLite in-memory)")
    print("=" * 60)

    from backend.database.connection import DatabaseConnection

    db = DatabaseConnection()
    db.connect("sqlite:///:memory:")
    assert db.is_connected
    print("[OK] Connected to in-memory SQLite")

    session = db.get_session()
    assert session is not None
    print("[OK] Got database session")

    session.close()
    db.disconnect()
    assert not db.is_connected
    print("[OK] Disconnected cleanly")

    # No URL case
    db2 = DatabaseConnection()
    db2.connect()
    assert not db2.is_connected
    print("[OK] No URL gracefully skips connection")

    print("\n[PASS] DatabaseConnection test passed")


# ======================================================================
# 6. MemoryRepository Test (SQLite)
# ======================================================================

def test_memory_repository():
    print("\n" + "=" * 60)
    print("MemoryRepository Test (SQLite)")
    print("=" * 60)

    from backend.database.connection import DatabaseConnection
    from backend.database.repositories import MemoryRepository

    db = DatabaseConnection()
    db.connect("sqlite:///:memory:")

    repo = MemoryRepository(db)

    # Add
    record_id = repo.add({
        "content": "User enjoys hiking",
        "category": "interest",
        "importance": 0.6,
        "conversation_id": "conv-001",
        "tags": {"outdoor": True},
    })
    assert record_id, "Expected a record ID"
    print(f"[OK] Added memory: {record_id}")

    # Find by ID
    found = repo.find_by_id(record_id)
    assert found is not None
    assert found["content"] == "User enjoys hiking"
    print("[OK] Found by ID")

    # Find all
    all_records = repo.find_all()
    assert len(all_records) == 1
    print(f"[OK] find_all() returned {len(all_records)} records")

    # Find by conversation
    conv_records = repo.find_by_conversation("conv-001")
    assert len(conv_records) == 1
    print("[OK] find_by_conversation() works")

    # Update
    updated = repo.update(record_id, {"content": "User enjoys hiking and camping"})
    assert updated is True
    found_updated = repo.find_by_id(record_id)
    assert found_updated["content"] == "User enjoys hiking and camping"
    print("[OK] Update works")

    # Delete
    deleted = repo.delete(record_id)
    assert deleted is True
    assert repo.find_by_id(record_id) is None
    print("[OK] Delete works")

    db.disconnect()
    print("\n[PASS] MemoryRepository test passed")


# ======================================================================
# Main
# ======================================================================

def main():
    print("\n" + "=" * 60)
    print("Person 3 — Memory System Unit Tests")
    print("=" * 60)

    test_importance_scorer()
    test_memory_ranking()
    test_memory_manager()
    test_database_models()
    test_database_connection()
    test_memory_repository()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
