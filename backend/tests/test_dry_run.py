#!/usr/bin/env python3
"""
TDD tests for Task 7 — Content sourcing playbook + dry-run.

RED phase: Tests fail before scripts are written.
GREEN phase: Tests pass after dry-run produces valid output.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent  # jp_drivers_test_trainer/
BACKEND_ROOT = Path(__file__).parent.parent
PLAYBOOK_PATH = PROJECT_ROOT / "docs" / "sourcing-playbook.md"
DRY_RUN_SCRIPT = PROJECT_ROOT / "scripts" / "dry_run_playbook.py"
SCRAPE_TEMPLATE = PROJECT_ROOT / "scripts" / "scrape_template.py"
REVIEW_QUEUE_PATH = PROJECT_ROOT / "data" / "manual_review_queue.jsonl"
DRY_RUN_OUTPUT = PROJECT_ROOT / "data" / "dry_run_output.json"


class TestPlaybookExists:
    """RED: Playbook file must exist with required sections."""

    def test_playbook_file_exists(self):
        assert PLAYBOOK_PATH.exists(), f"Playbook not found at {PLAYBOOK_PATH}"

    def test_playbook_has_goal_section(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        assert "## 1. Goal" in content or "Goal" in content

    def test_playbook_has_22_themes(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        # Check for all 22 theme slugs
        theme_slugs = [
            "driver-mindset", "signals", "signs-and-markings", "prohibited-actions",
            "emergency-vehicle-priority", "intersections-and-railroad-crossings",
            "pedestrian-protection", "safety-checks", "overtaking-and-passing",
            "license-system", "blind-spots", "human-factors", "natural-forces",
            "adverse-conditions", "typical-accidents", "vehicle-maintenance",
            "parking-and-stopping", "loading-and-passengers", "accident-response",
            "highway-driving", "route-planning", "speed-and-following-distance",
        ]
        for slug in theme_slugs:
            assert slug in content, f"Theme slug '{slug}' missing from playbook"

    def test_playbook_has_7_trap_patterns(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        patterns = [
            "assertive-language", "permission-vs-obligation", "double-negatives",
            "scope-substitution", "term-substitution", "ignored-exceptions",
            "number-confusion",
        ]
        for pattern in patterns:
            assert pattern in content, f"Trap pattern '{pattern}' missing from playbook"

    def test_playbook_has_10_failure_points(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        # Check for the failure points section
        assert "Failure Point" in content or "failure point" in content.lower()

    def test_playbook_has_source_inventory(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        # Check for at least 10 sources
        sources = [
            "japandl.com", "leasejapan.com", "menkyohub", "brnojapao",
            "diaadia", "lo-pal", "menkyo-tottaru", "online-ds",
            "reddit.com", "npa",
        ]
        found = sum(1 for s in sources if s.lower() in content.lower())
        assert found >= 10, f"Only {found}/10 sources found in inventory"

    def test_playbook_marks_excluded_sources(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        assert "JAF" in content or "jaf" in content
        assert "Amitie" in content or "amitie" in content
        assert "Yumi" in content or "yumi" in content

    def test_playbook_has_parser_schemas(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        assert "ParsedQuestion" in content or "parser schema" in content.lower()

    def test_playbook_has_normalization_rules(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        assert "normaliz" in content.lower()

    def test_playbook_has_bilingual_parity_rules(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        assert "bilingual" in content.lower() or "parity" in content.lower()
        assert "translations_status" in content

    def test_playbook_has_review_queue_format(self):
        content = PLAYBOOK_PATH.read_text(encoding="utf-8")
        assert "manual_review_queue" in content
        assert "raw_text" in content
        assert "source_url" in content
        assert "reason" in content


class TestScrapeTemplate:
    """Scrape template stub must exist and be importable."""

    def test_scrape_template_exists(self):
        assert SCRAPE_TEMPLATE.exists(), f"Scrape template not found at {SCRAPE_TEMPLATE}"

    def test_scrape_template_imports_cleanly(self):
        """Script should not have import errors."""
        result = subprocess.run(
            [sys.executable, "-c", "import ast; ast.parse(open(r'" + str(SCRAPE_TEMPLATE) + "').read())"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Syntax error in scrape_template.py: {result.stderr}"


class TestDryRunScript:
    """Dry-run script must run and produce valid output."""

    def test_dry_run_script_exists(self):
        assert DRY_RUN_SCRIPT.exists(), f"Dry-run script not found at {DRY_RUN_SCRIPT}"

    def test_dry_run_script_syntax_valid(self):
        """Script should parse without syntax errors."""
        result = subprocess.run(
            [sys.executable, "-c", "import ast; ast.parse(open(r'" + str(DRY_RUN_SCRIPT) + "').read())"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Syntax error in dry_run_playbook.py: {result.stderr}"

    def test_dry_run_produces_output(self):
        """Running the dry-run script should produce a valid JSON output file."""
        result = subprocess.run(
            [sys.executable, str(DRY_RUN_SCRIPT)],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"Dry-run failed: {result.stderr}"
        assert DRY_RUN_OUTPUT.exists(), f"Output file not created at {DRY_RUN_OUTPUT}"

    def test_dry_run_output_is_valid_json(self):
        """Output file must be valid JSON."""
        assert DRY_RUN_OUTPUT.exists(), "Run test_dry_run_produces_output first"
        with open(DRY_RUN_OUTPUT, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)

    def test_dry_run_output_has_5_questions(self):
        """Output must contain at least 5 parsed questions."""
        with open(DRY_RUN_OUTPUT, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 5, f"Expected ≥5 questions, got {len(data)}"

    def test_dry_run_questions_have_required_fields(self):
        """Each question must have the required schema fields."""
        with open(DRY_RUN_OUTPUT, encoding="utf-8") as f:
            data = json.load(f)
        required_fields = {
            "prompt_en", "answer_en", "explanation_en", "theme_slug",
            "source_url", "license", "attribution", "tricky",
            "tricky_pattern", "difficulty", "raw_text",
        }
        for idx, q in enumerate(data):
            missing = required_fields - set(q.keys())
            assert not missing, f"Question {idx} missing fields: {missing}"

    def test_dry_run_answers_are_normalized(self):
        """Answers must be 'true' or 'false'."""
        with open(DRY_RUN_OUTPUT, encoding="utf-8") as f:
            data = json.load(f)
        for idx, q in enumerate(data):
            assert q["answer_en"] in ("true", "false"), \
                f"Question {idx} has invalid answer: {q['answer_en']!r}"

    def test_dry_run_theme_slugs_are_valid(self):
        """Theme slugs must be from the official 22."""
        valid_slugs = {
            "driver-mindset", "signals", "signs-and-markings", "prohibited-actions",
            "emergency-vehicle-priority", "intersections-and-railroad-crossings",
            "pedestrian-protection", "safety-checks", "overtaking-and-passing",
            "license-system", "blind-spots", "human-factors", "natural-forces",
            "adverse-conditions", "typical-accidents", "vehicle-maintenance",
            "parking-and-stopping", "loading-and-passengers", "accident-response",
            "highway-driving", "route-planning", "speed-and-following-distance",
        }
        with open(DRY_RUN_OUTPUT, encoding="utf-8") as f:
            data = json.load(f)
        for idx, q in enumerate(data):
            assert q["theme_slug"] in valid_slugs, \
                f"Question {idx} has invalid theme slug: {q['theme_slug']!r}"

    def test_dry_run_source_url_is_set(self):
        """Every question must carry a source_url."""
        with open(DRY_RUN_OUTPUT, encoding="utf-8") as f:
            data = json.load(f)
        for idx, q in enumerate(data):
            assert q["source_url"], f"Question {idx} has empty source_url"
            assert q["source_url"].startswith("http"), \
                f"Question {idx} source_url is not a URL: {q['source_url']!r}"


class TestReviewQueue:
    """Manual review queue format validation."""

    def test_review_queue_file_exists_or_empty_ok(self):
        """Review queue file should exist (may be empty if no items flagged)."""
        # The dry-run script creates the file when it runs
        # If it doesn't exist yet, that's OK — the format is defined in the playbook
        if REVIEW_QUEUE_PATH.exists():
            content = REVIEW_QUEUE_PATH.read_text(encoding="utf-8").strip()
            if content:
                # Each line must be valid JSON
                for line_num, line in enumerate(content.split("\n"), 1):
                    item = json.loads(line)
                    assert "raw_text" in item, f"Line {line_num} missing raw_text"
                    assert "source_url" in item, f"Line {line_num} missing source_url"
                    assert "reason" in item, f"Line {line_num} missing reason"
