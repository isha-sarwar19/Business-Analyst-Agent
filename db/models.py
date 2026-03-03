"""
db/models.py — SQLAlchemy ORM models for BA Agent.

Uses String(36) primary keys (str(uuid4())) for SQLite compatibility.
PostgreSQL handles these as plain varchar; to use native UUID type on PG,
change Column(String(36)) → Column(UUID(as_uuid=True)) and update default.
"""
from sqlalchemy import (
    Column, String, Integer, DateTime, JSON, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from uuid import uuid4

Base = declarative_base()


class ChatSession(Base):
    """One row per browser/CLI session. Tracks the current phase."""
    __tablename__ = "chat_sessions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="UUID stored as varchar(36) for SQLite compatibility"
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),      # auto-refreshed on every UPDATE
        nullable=False
    )
    phase = Column(String(20), nullable=False, default="chat")  # chat | interview | review
    session_metadata = Column(JSON, nullable=True)              # renamed from 'metadata'


class PRDVersion(Base):
    """One row per generated PRD. version_number auto-increments per session."""
    __tablename__ = "prd_versions"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    session_id = Column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    version_number = Column(Integer, nullable=False)  # incremented in a transaction
    project_name = Column(String(255), nullable=True)
    prd_json = Column(JSON, nullable=True)
    pdf_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ── Indexes for query performance ────────────────────────────────────────────
# Speeds up: get_prd_versions(session_id) and save_prd_version MAX() lookup
Index("ix_prd_session_id", PRDVersion.session_id)
Index("ix_prd_session_version", PRDVersion.session_id, PRDVersion.version_number)
