"""Data repositories.

Implements the repository pattern for abstracting
database access behind clean interfaces.
"""

import logging
from typing import Any

from sqlalchemy import select, delete as sa_delete

from backend.database.connection import DatabaseConnection
from backend.database.models import ConversationLog, MemoryRecord

logger = logging.getLogger(__name__)


class MemoryRepository:
    """Repository for memory record persistence."""

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    def add(self, record: dict) -> str:
        """Insert a new memory record and return its ID."""
        session = self._db.get_session()
        if session is None:
            logger.warning("Cannot add memory — no database session")
            return ""
        try:
            db_record = MemoryRecord(
                content=record.get("content", ""),
                category=record.get("category", "general"),
                importance=record.get("importance", 0.0),
                conversation_id=record.get("conversation_id", ""),
                tags=record.get("tags"),
                metadata_=record.get("metadata"),
            )
            if record.get("id"):
                db_record.id = record["id"]
            session.add(db_record)
            session.commit()
            session.refresh(db_record)
            logger.debug("Memory record added: %s", db_record.id)
            return db_record.id
        except Exception as exc:
            session.rollback()
            logger.error("Failed to add memory record: %s", exc)
            raise
        finally:
            session.close()

    def find_by_id(self, record_id: str) -> dict | None:
        """Find a memory record by its identifier."""
        session = self._db.get_session()
        if session is None:
            return None
        try:
            result = session.execute(
                select(MemoryRecord).where(MemoryRecord.id == record_id)
            )
            record = result.scalar_one_or_none()
            return record.to_dict() if record else None
        except Exception as exc:
            logger.error("Failed to find memory record %s: %s", record_id, exc)
            return None
        finally:
            session.close()

    def find_all(self, limit: int = 100) -> list[dict]:
        """Retrieve memory records with a limit."""
        session = self._db.get_session()
        if session is None:
            return []
        try:
            result = session.execute(
                select(MemoryRecord).order_by(MemoryRecord.created_at.desc()).limit(limit)
            )
            return [row.to_dict() for row in result.scalars().all()]
        except Exception as exc:
            logger.error("Failed to list memory records: %s", exc)
            return []
        finally:
            session.close()

    def find_by_conversation(self, conversation_id: str) -> list[dict]:
        """Find all memory records for a conversation."""
        session = self._db.get_session()
        if session is None:
            return []
        try:
            result = session.execute(
                select(MemoryRecord)
                .where(MemoryRecord.conversation_id == conversation_id)
                .order_by(MemoryRecord.created_at.desc())
            )
            return [row.to_dict() for row in result.scalars().all()]
        except Exception as exc:
            logger.error("Failed to find memories for conversation %s: %s", conversation_id, exc)
            return []
        finally:
            session.close()

    def delete(self, record_id: str) -> bool:
        """Delete a memory record by its identifier."""
        session = self._db.get_session()
        if session is None:
            return False
        try:
            result = session.execute(
                sa_delete(MemoryRecord).where(MemoryRecord.id == record_id)
            )
            session.commit()
            deleted = result.rowcount > 0
            if deleted:
                logger.debug("Memory record deleted: %s", record_id)
            return deleted
        except Exception as exc:
            session.rollback()
            logger.error("Failed to delete memory record %s: %s", record_id, exc)
            return False
        finally:
            session.close()

    def update(self, record_id: str, updates: dict) -> bool:
        """Update fields on an existing memory record."""
        session = self._db.get_session()
        if session is None:
            return False
        try:
            result = session.execute(
                select(MemoryRecord).where(MemoryRecord.id == record_id)
            )
            record = result.scalar_one_or_none()
            if record is None:
                return False

            allowed_fields = {"content", "category", "importance", "tags", "metadata_"}
            for key, value in updates.items():
                if key in allowed_fields:
                    setattr(record, key, value)

            session.commit()
            return True
        except Exception as exc:
            session.rollback()
            logger.error("Failed to update memory record %s: %s", record_id, exc)
            return False
        finally:
            session.close()


class ConversationRepository:
    """Repository for conversation log persistence."""

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    def add(self, record: dict) -> str:
        """Insert a new conversation log entry and return its ID."""
        session = self._db.get_session()
        if session is None:
            return ""
        try:
            db_record = ConversationLog(
                session_id=record.get("session_id", ""),
                role=record.get("role", "user"),
                content=record.get("content", ""),
            )
            session.add(db_record)
            session.commit()
            session.refresh(db_record)
            return db_record.id
        except Exception as exc:
            session.rollback()
            logger.error("Failed to add conversation log: %s", exc)
            raise
        finally:
            session.close()

    def find_by_session(self, session_id: str) -> list[dict]:
        """Find all conversation log entries for a session."""
        session = self._db.get_session()
        if session is None:
            return []
        try:
            result = session.execute(
                select(ConversationLog)
                .where(ConversationLog.session_id == session_id)
                .order_by(ConversationLog.created_at.asc())
            )
            return [row.to_dict() for row in result.scalars().all()]
        except Exception as exc:
            logger.error("Failed to find conversation logs for session %s: %s", session_id, exc)
            return []
        finally:
            session.close()
