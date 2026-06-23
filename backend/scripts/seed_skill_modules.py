#!/usr/bin/env python3
"""
Seed skill modules from T9 JSONs into the skill_modules table.

Idempotent: DELETE-then-INSERT by slug for each module.
Run after apply_migrations.py:
    uv run python scripts/seed_skill_modules.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "jp_drivers.sqlite"
JSON_DIR = PROJECT_ROOT.parent / "data" / "skill_modules"


def load_module_json(path: Path) -> dict:
    """Parse a skill module JSON and flatten to DB-ready dict."""
    with open(path) as f:
        raw = json.load(f)

    overview = raw["overview"]
    pro_tip = raw["pro_tip"]

    return {
        "slug": raw["slug"],
        "name_en": raw["name_en"],
        "name_pt": raw["name_pt"],
        "sort_order": raw["sort_order"],
        "overview_en": overview["en"],
        "overview_pt": overview["pt"],
        "svg_path": raw.get("svg_path"),
        "correct_trajectory_json": json.dumps(raw["correct_trajectory"], ensure_ascii=False),
        "wrong_trajectory_json": json.dumps(raw["wrong_trajectory"], ensure_ascii=False),
        "common_mistakes_json": json.dumps(raw["common_mistakes"], ensure_ascii=False),
        "checklist_json": json.dumps(raw["checklist"], ensure_ascii=False),
        "pro_tip_en": pro_tip["en"],
        "pro_tip_pt": pro_tip["pt"],
    }


def main() -> int:
    if not DB_PATH.exists():
        print("Database not found. Run apply_migrations.py first.")
        return 1

    json_files = sorted(JSON_DIR.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {JSON_DIR}")
        return 1

    import sqlite_vec

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())

    INSERT_SQL = """
        INSERT INTO skill_modules (
            slug, name_en, name_pt, sort_order,
            overview_en, overview_pt, svg_path,
            correct_trajectory_json, wrong_trajectory_json,
            common_mistakes_json, checklist_json,
            pro_tip_en, pro_tip_pt
        ) VALUES (
            :slug, :name_en, :name_pt, :sort_order,
            :overview_en, :overview_pt, :svg_path,
            :correct_trajectory_json, :wrong_trajectory_json,
            :common_mistakes_json, :checklist_json,
            :pro_tip_en, :pro_tip_pt
        )
    """

    for jf in json_files:
        mod = load_module_json(jf)
        slug = mod["slug"]

        # Idempotent: delete existing, then insert
        conn.execute("DELETE FROM skill_modules WHERE slug = ?", (slug,))
        conn.execute(INSERT_SQL, mod)
        print(f"  Seeded: {slug}")

    conn.commit()

    # Verify
    cur = conn.execute("SELECT COUNT(*) FROM skill_modules")
    count = cur.fetchone()[0]
    print(f"\nSkill modules in DB: {count}")

    conn.close()
    print("Seed completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
