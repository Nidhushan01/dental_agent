import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from db.models import Base, Appointment


def _ensure_sqlite_dir(database_url: str) -> None:
    """If the URL points to a SQLite file, make sure its parent directory exists.

    This is needed on Render (and any Docker environment) where the working
    directory may not be writable by the non-root app user.  We handle all
    common SQLite URL forms:
        sqlite:///relative/path.db          →  ./relative/path.db
        sqlite:////absolute/path.db         →  /absolute/path.db
        sqlite+pysqlite:///...              →  same rules
    """
    url = database_url.strip()
    if "sqlite" not in url.lower() or ":memory:" in url:
        return  # nothing to do for in-memory or non-SQLite DBs

    # Strip scheme prefix (e.g. "sqlite:///", "sqlite+pysqlite:///")
    # SQLite URLs use 3 slashes for relative and 4 for absolute paths.
    if ":///" in url:
        path_part = url.split(":///", 1)[1]
    else:
        return  # unrecognised format — leave it alone

    if not path_part or path_part == ":memory:":
        return

    db_path = Path(path_part)
    parent = db_path.parent
    if str(parent) not in ("", "."):
        os.makedirs(parent, exist_ok=True)


# Ensure the DB directory exists before SQLAlchemy tries to open the file
_ensure_sqlite_dir(settings.DATABASE_URL)

# SQLite connection
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
