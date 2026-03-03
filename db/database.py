"""
db/database.py — SQLAlchemy engine, session factory, and table initialization.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from core.config import settings
from core.logging_config import get_logger
from db.models import Base

logger = get_logger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
# check_same_thread=False is only needed for SQLite + multi-thread (e.g. Streamlit)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,          # set True for SQL query debugging
    pool_pre_ping=True,  # detect stale connections
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db() -> None:
    """
    Create all tables that don't exist yet.
    Called at application startup (app.py + main.py).
    For schema evolution use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized — all tables ready.")


@contextmanager
def get_db() -> Session:
    """
    Context manager yielding a DB session and guaranteeing cleanup.

    Usage:
        with get_db() as db:
            repo.create_session(db, "chat")
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
