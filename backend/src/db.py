"""
SQLAlchemy 2 async engine + session for JP Drivers Test Trainer.

Design decisions:
- Raw SQL migrations (not Alembic) — simpler for SQLite-only projects.
- sqlite-vec extension loaded on every connection via sync_engine "connect" hook.
- DB path is resolved relative to project root (backend/).

Migrations are applied via scripts/apply_migrations.py which reads
backend/src/migrations/*.sql in order and executes them against the DB.
"""
from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------------------------
# Engine & session maker
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent  # backend/ -> project root
DB_PATH = PROJECT_ROOT / "data" / "jp_drivers.sqlite"
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DB_URL, echo=False)

# sqlite-vec extension must be loaded on EVERY connection.
# The sync_engine "connect" event fires for each connection created.
@event.listens_for(engine.sync_engine, "connect")
def _load_vec_on_connect(db_api_conn, connection_record) -> None:  # type: ignore[arg-type]
    import sqlite_vec

    db_api_conn.enable_load_extension(True)
    db_api_conn.load_extension(sqlite_vec.loadable_path())


async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async session."""
    async with async_session_maker() as session:
        yield session


# ---------------------------------------------------------------------------
# Base class for ORM models
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass
