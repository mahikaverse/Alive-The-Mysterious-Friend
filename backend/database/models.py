"""Database ORM models.

Defines the SQLAlchemy ORM models for memory records,
conversation logs, and persistent state.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared base class for all ORM models."""


class MemoryRecord(Base):
    """Persistent memory record stored in PostgreSQL.

    The actual vector embedding lives in ChromaDB; this table
    stores the metadata, content, and importance score.
    """

    __tablename__ = "memory_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general")
    importance: Mapped[float] = mapped_column(Float, default=0.0)
    conversation_id: Mapped[str] = mapped_column(String(36), default="")
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "importance": self.importance,
            "conversation_id": self.conversation_id,
            "tags": self.tags or {},
            "metadata": self.metadata_ or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ConversationLog(Base):
    """Conversation turn log for historical reference."""

    __tablename__ = "conversation_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(String(36), index=True, default="")
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
