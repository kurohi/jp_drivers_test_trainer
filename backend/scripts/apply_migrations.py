#!/usr/bin/env python3
"""
Apply all SQL migrations in src/migrations/ in order.

Each file must be named like 000N_description.sql.
Run from the backend/ directory:
    uv run python scripts/apply_migrations.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Project root is backend/
PROJECT_ROOT = Path(__file__).parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "src" / "migrations"
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "jp_drivers.sqlite"


def _load_vec(conn: sqlite3.Connection) -> None:
    """Load sqlite-vec on the given connection."""
    import sqlite_vec

    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found in", MIGRATIONS_DIR)
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    _load_vec(conn)
    conn.execute("PRAGMA foreign_keys = ON")

    for mig_path in migration_files:
        print(f"Applying migration: {mig_path.name}")
        sql = mig_path.read_text()
        conn.executescript(sql)
        conn.commit()

    conn.close()
    print("All migrations applied successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
