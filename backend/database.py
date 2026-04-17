from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# For now use a local SQLite file; can be swapped to Postgres via env later.
DB_PATH = Path("guidance_demo.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Import models so they are registered with Base before create_all.
# This import is intentionally placed here to avoid circular import issues.
try:  # pragma: no cover - side-effect import
    import models  # noqa: F401
except Exception:
    # During initial tooling or model definition this may fail; create_all is
    # also called from startup_event as a fallback.
    models = None  # type: ignore[assignment]

# Create tables eagerly for local development; in production a migration
# system (Alembic) is recommended.
Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Session:
    """Provide a transactional scope around a series of operations."""

    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
