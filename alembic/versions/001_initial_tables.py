"""initial tables

Revision ID: 001_initial
Revises:
Create Date: 2026-07-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create memory_records table
    op.create_table(
        "memory_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), server_default="general"),
        sa.Column("importance", sa.Float(), server_default="0.0"),
        sa.Column("conversation_id", sa.String(36), server_default=""),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_memory_records_conversation_id", "memory_records", ["conversation_id"])

    # Create conversation_logs table
    op.create_table(
        "conversation_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), server_default=""),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_conversation_logs_session_id", "conversation_logs", ["session_id"])


def downgrade() -> None:
    op.drop_table("conversation_logs")
    op.drop_table("memory_records")
