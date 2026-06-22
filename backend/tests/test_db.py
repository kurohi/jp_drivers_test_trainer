"""
TDD tests for DB schema, migrations, and 22-theme seed.

RED PHASE: These tests define the expected behavior.
They will FAIL until we implement:
- backend/src/db.py
- backend/src/models/*
- backend/src/migrations/0001_initial.sql
- backend/scripts/apply_migrations.py
- backend/scripts/seed_themes.py
"""
import os
import pytest
import sqlite3
from pathlib import Path

# Project root is backend/
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "jp_drivers.sqlite"
MIGRATIONS_DIR = PROJECT_ROOT / "src" / "migrations"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_db():
    """Wipe the SQLite file before each test so we start fresh."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    # Ensure data/ dir exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    yield
    # Leave DB intact after test for inspection


@pytest.fixture
def raw_conn():
    """Raw sqlite3 connection with sqlite-vec loaded."""
    import sqlite_vec

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Test: migration creates all 9 entities
# ---------------------------------------------------------------------------

def test_nine_entities_exist_after_migration(raw_conn):
    """
    After running 0001_initial.sql, the following 9 tables/views must exist:
      1. themes
      2. questions
      3. attempts
      4. attempt_answers
      5. study_plans
      6. rag_documents
      7. rag_chunks
      8. skill_modules
      9. vec_chunks
    """
    # Apply migration via subprocess so we exercise the actual script
    import subprocess
    result = subprocess.run(
        ["uv", "run", "python", "scripts/apply_migrations.py"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Migration script failed: {result.stderr}"

    # Verify all 9 entities exist
    raw_conn.row_factory = sqlite3.Row
    cur = raw_conn.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY name"
    )
    rows = {r["name"] for r in cur.fetchall()}

    expected = {
        "themes",
        "questions",
        "attempts",
        "attempt_answers",
        "study_plans",
        "rag_documents",
        "rag_chunks",
        "skill_modules",
        "vec_chunks",
    }
    assert expected.issubset(rows), f"Missing entities: {expected - rows}"


# ---------------------------------------------------------------------------
# Test: sqlite-vec loads correctly
# ---------------------------------------------------------------------------

def test_sqlite_vec_loads(raw_conn):
    """sqlite-vec extension must load without error on every new connection."""
    # vec_chunks table must be a virtual table using vec0
    raw_conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(embedding float[768])"
    )
    cur = raw_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='vec_chunks'"
    )
    row = cur.fetchone()
    assert row is not None, "vec_chunks virtual table not created"

    # sqlite-vec version must be reported
    ver = raw_conn.execute("SELECT vec_version()").fetchone()[0]
    assert ver is not None and len(ver) > 0, "vec_version() returned empty"


# ---------------------------------------------------------------------------
# Test: seed produces exactly 22 root themes
# ---------------------------------------------------------------------------

def test_seed_produces_22_root_themes(raw_conn):
    """
    After running migrations AND seed_themes.py, there must be exactly
    22 themes with parent_id IS NULL (root themes, no parent).
    These are the official driver-test subject domains.
    """
    # Apply migration first
    import subprocess
    mig_result = subprocess.run(
        ["uv", "run", "python", "scripts/apply_migrations.py"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert mig_result.returncode == 0, f"Migration failed: {mig_result.stderr}"

    # Run seed
    seed_result = subprocess.run(
        ["uv", "run", "python", "scripts/seed_themes.py"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    assert seed_result.returncode == 0, f"Seed script failed: {seed_result.stderr}"

    # Count root themes (parent_id IS NULL)
    raw_conn.row_factory = sqlite3.Row
    cur = raw_conn.execute(
        "SELECT COUNT(*) as cnt FROM themes WHERE parent_id IS NULL"
    )
    count = cur.fetchone()["cnt"]
    assert count == 22, f"Expected 22 root themes, got {count}"

    # Verify the exact 22 slugs are present
    cur = raw_conn.execute("SELECT slug FROM themes WHERE parent_id IS NULL ORDER BY slug")
    slugs = {r["slug"] for r in cur.fetchall()}

    expected_slugs = {
        "driver-mindset",
        "signals",
        "signs-and-markings",
        "prohibited-actions",
        "emergency-vehicle-priority",
        "intersections-and-railroad-crossings",
        "pedestrian-protection",
        "safety-checks",
        "overtaking-and-passing",
        "license-system",
        "blind-spots",
        "human-factors",
        "natural-forces",
        "adverse-conditions",
        "typical-accidents",
        "vehicle-maintenance",
        "parking-and-stopping",
        "loading-and-passengers",
        "accident-response",
        "highway-driving",
        "route-planning",
        "speed-and-following-distance",
    }
    assert slugs == expected_slugs, f"Mismatched slugs: {slugs ^ expected_slugs}"


# ---------------------------------------------------------------------------
# Test: themes have bilingual names
# ---------------------------------------------------------------------------

def test_root_themes_have_bilingual_names(raw_conn):
    """Each root theme must have both name_en and name_pt populated."""
    import subprocess
    subprocess.run(
        ["uv", "run", "python", "scripts/apply_migrations.py"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
    )
    subprocess.run(
        ["uv", "run", "python", "scripts/seed_themes.py"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
    )

    raw_conn.row_factory = sqlite3.Row
    cur = raw_conn.execute(
        "SELECT name_en, name_pt FROM themes WHERE parent_id IS NULL"
    )
    rows = cur.fetchall()
    for r in rows:
        assert r["name_en"], "name_en must not be empty"
        assert r["name_pt"], "name_pt must not be empty"
        assert len(r["name_en"]) > 2, "name_en too short"
        assert len(r["name_pt"]) > 2, "name_pt too short"
