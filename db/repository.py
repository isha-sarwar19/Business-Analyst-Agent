"""
db/repository.py — Repository pattern: all DB CRUD operations live here.
No business logic — just data access.
"""
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from db.models import ChatSession, PRDVersion
from core.logging_config import get_logger

logger = get_logger(__name__)


# ── ChatSession ───────────────────────────────────────────────────────────────

def create_session(db: Session, phase: str = "chat") -> ChatSession:
    """Create and persist a new ChatSession row."""
    session = ChatSession(
        id=str(uuid4()),
        phase=phase,
        session_metadata={}
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info("Session created | id=%s | phase=%s", session.id, phase)
    return session


def get_session(db: Session, session_id: str) -> ChatSession | None:
    """Fetch a ChatSession by UUID string."""
    return db.get(ChatSession, session_id)


def update_session_phase(db: Session, session_id: str, phase: str) -> None:
    """
    Update the phase of an existing session.
    SQLAlchemy's onupdate=func.now() on updated_at fires automatically.
    """
    session = db.get(ChatSession, session_id)
    if session:
        session.phase = phase
        db.commit()
        logger.info("Session phase updated | id=%s | phase=%s", session_id, phase)
    else:
        logger.warning("update_session_phase: session not found | id=%s", session_id)


# ── PRDVersion ────────────────────────────────────────────────────────────────

def save_prd_version(
    db: Session,
    session_id: str,
    prd_json: dict,
    pdf_path: str,
    project_name: str
) -> PRDVersion:
    """
    Persist a new PRDVersion row with a transactionally safe version number.

    Version increment is done inside the same transaction:
      next_version = MAX(version_number) + 1  (for this session)
    If no prior versions exist, starts at 1.
    The ix_prd_session_version composite index makes the MAX() scan fast.
    """
    # Compute next version_number inside the open transaction
    result = db.execute(
        select(func.max(PRDVersion.version_number)).where(
            PRDVersion.session_id == session_id
        )
    ).scalar()

    next_version = (result or 0) + 1

    prd = PRDVersion(
        id=str(uuid4()),
        session_id=session_id,
        version_number=next_version,
        project_name=project_name,
        prd_json=prd_json,
        pdf_path=pdf_path,
    )
    db.add(prd)
    db.commit()
    db.refresh(prd)
    logger.info(
        "PRD version saved | session=%s | version=%d | project=%s | pdf=%s",
        session_id, next_version, project_name, pdf_path
    )
    return prd


def get_prd_versions(db: Session, session_id: str) -> list[PRDVersion]:
    """
    Return all PRD versions for a session, ordered ascending.
    Uses ix_prd_session_id index for performance.
    """
    return (
        db.query(PRDVersion)
        .filter(PRDVersion.session_id == session_id)
        .order_by(PRDVersion.version_number.asc())
        .all()
    )


def get_latest_prd(db: Session, session_id: str) -> PRDVersion | None:
    """Return the most recent PRDVersion for a session."""
    return (
        db.query(PRDVersion)
        .filter(PRDVersion.session_id == session_id)
        .order_by(PRDVersion.version_number.desc())
        .first()
    )
