"""SQLAlchemy engine, session factory and schema creation.

SQLite is still the database; SQLAlchemy is the layer on top. One Session per
request via the `get_db` dependency - FastAPI runs sync `def` handlers in a
threadpool, so a shared Session would not be safe.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker

from config import DB_PATH
from models import Base, Profile

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    # SQLite refuses cross-thread use by default; the threadpool hands a
    # connection to whichever worker runs the request.
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _record) -> None:
    """SQLAlchemy pools connections, so PRAGMAs must be set per connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,  # keeps attributes readable after commit()
    class_=Session,
)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding one Session per request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create any missing tables, guarantee the singleton profile row, seed."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        if session.scalar(select(Profile).where(Profile.id == 1)) is None:
            session.add(Profile(id=1))
            session.commit()

    # Imported here rather than at module top: seed imports this module.
    from seed import seed_if_empty

    seed_if_empty()


def next_display_order(session: Session, model: type) -> int:
    """Append new rows at the end, leaving gaps of 10 to insert between items."""
    current = session.scalar(select(func.max(model.display_order)))
    return int(current or 0) + 10
