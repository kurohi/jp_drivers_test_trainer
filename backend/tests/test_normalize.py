"""
TDD tests for the normalization pipeline.

Uses local fixtures — NEVER hits live sites or Ollama in tests.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rapidfuzz import fuzz

# Add scripts to path
PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

import sys
sys.path.insert(0, str(SCRIPTS_DIR))

# Import normalize module functions
from normalize import (
    TRICKY_PATTERNS,
    ParsedQuestion,
    DedupResult,
    _dedup_key,
    deduplicate,
    detect_tricky,
    normalize_answer,
    normalize_text,
    raw_to_parsed,
    tag_tricky,
    enqueue_review,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_raw_questions():
    """Load sample raw questions from fixture."""
    fixture_path = FIXTURES_DIR / "lease_japan_test1.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_parsed_questions(sample_raw_questions):
    """Convert raw fixtures to ParsedQuestion objects."""
    return raw_to_parsed(sample_raw_questions)


@pytest.fixture
def github_raw_questions():
    """Load GitHub TSV fixture questions."""
    fixture_path = FIXTURES_DIR / "github_tsv_questions.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mixed_source_questions(sample_raw_questions, github_raw_questions):
    """Combine questions from multiple sources."""
    return sample_raw_questions + github_raw_questions


# ---------------------------------------------------------------------------
# Text normalization tests
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_strips_whitespace(self):
        assert normalize_text("  hello  world  ") == "hello world"

    def test_normalizes_multiple_spaces(self):
        assert normalize_text("hello   world") == "hello world"

    def test_removes_html_tags(self):
        assert normalize_text("<p>hello</p> world") == "hello world"

    def test_converts_smart_quotes(self):
        assert normalize_text("\u2018hello\u2019") == "'hello'"
        assert normalize_text("\u201chello\u201d") == '"hello"'

    def test_normalizes_dashes(self):
        assert normalize_text("hello\u2014world") == "hello-world"
        assert normalize_text("hello\u2013world") == "hello-world"

    def test_empty_string(self):
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""

    def test_preserves_normal_text(self):
        assert normalize_text("Hello world") == "Hello world"

    def test_handles_newlines(self):
        assert normalize_text("hello\nworld") == "hello world"


class TestNormalizeAnswer:
    @pytest.mark.parametrize("raw,expected", [
        ("true", "true"),
        ("True", "true"),
        ("TRUE", "true"),
        ("yes", "true"),
        ("Yes", "true"),
        ("correct", "true"),
        ("○", "true"),
        ("false", "false"),
        ("False", "false"),
        ("FALSE", "false"),
        ("no", "false"),
        ("No", "false"),
        ("incorrect", "false"),
        ("×", "false"),
        ("x", "false"),
    ])
    def test_normalizes_common_values(self, raw, expected):
        assert normalize_answer(raw) == expected

    def test_preserves_unknown(self):
        result = normalize_answer("pending")
        assert result == "pending"

    def test_handles_whitespace(self):
        assert normalize_answer("  true  ") == "true"
        assert normalize_answer("  FALSE  ") == "false"


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------

class TestDedupKey:
    def test_lowercase_and_strip_punct(self):
        assert _dedup_key("Hello, World!") == "hello world"

    def test_handles_special_chars(self):
        assert _dedup_key("Driver's license") == "drivers license"

    def test_empty_string(self):
        assert _dedup_key("") == ""

    def test_handles_unicode(self):
        assert _dedup_key("Pedestrian's right-of-way!") == "pedestrians rightofway"


class TestDeduplicate:
    def test_removes_exact_dups(self, sample_parsed_questions):
        dup = ParsedQuestion(
            prompt_en=sample_parsed_questions[0].prompt_en,
            answer_en="true",
            explanation_en="dup",
            theme_slug="signals",
            source_url="https://example.com",
            license="open-source",
            attribution="Test",
        )
        questions = sample_parsed_questions + [dup]

        result = deduplicate(questions)
        assert result.exact_dups_skipped >= 1

    def test_flags_near_dups(self):
        q1 = ParsedQuestion(
            prompt_en="Drivers must always stop at red lights.",
            answer_en="true",
            explanation_en="",
            theme_slug="signals",
            source_url="https://example.com/1",
            license="open-source",
            attribution="Test",
        )
        q2 = ParsedQuestion(
            prompt_en="Drivers must always stop at red light.",
            answer_en="true",
            explanation_en="",
            theme_slug="signals",
            source_url="https://example.com/2",
            license="open-source",
            attribution="Test",
        )

        result = deduplicate([q1, q2], near_dup_threshold=85.0)
        assert len(result.unique) + len(result.near_dups) == 2

    def test_respects_existing_keys(self):
        q = ParsedQuestion(
            prompt_en="Drivers must stop at red lights.",
            answer_en="true",
            explanation_en="",
            theme_slug="signals",
            source_url="https://example.com",
            license="open-source",
            attribution="Test",
        )
        existing = {_dedup_key(q.prompt_en)}
        result = deduplicate([q], existing_keys=existing)
        assert result.exact_dups_skipped == 1
        assert len(result.unique) == 0

    def test_empty_list(self):
        result = deduplicate([])
        assert result.unique == []
        assert result.exact_dups_skipped == 0

    def test_all_unique_questions(self):
        questions = [
            ParsedQuestion(
                prompt_en=prompt,
                answer_en="true",
                explanation_en="",
                theme_slug="signals",
                source_url=f"https://example.com/{i}",
                license="open-source",
                attribution="Test",
            )
            for i, prompt in enumerate([
                "Drivers must stop at red traffic signals.",
                "Pedestrians have priority at marked crossings.",
                "Emergency vehicles require immediate yielding.",
                "Tire pressure affects vehicle handling.",
                "Seatbelts protect occupants during collisions.",
            ])
        ]
        result = deduplicate(questions)
        assert len(result.unique) == 5
        assert result.exact_dups_skipped == 0
        assert len(result.near_dups) == 0


# ---------------------------------------------------------------------------
# Tricky pattern tests
# ---------------------------------------------------------------------------

class TestDetectTricky:
    def test_assertive_language(self):
        tricky, pattern = detect_tricky("Drivers must always stop at red lights.")
        assert tricky is True
        assert "assertive-language" in pattern

    def test_permission_vs_obligation(self):
        tricky, pattern = detect_tricky("Drivers may stop at the intersection.")
        assert tricky is True
        assert "permission-vs-obligation" in pattern

    def test_double_negatives(self):
        tricky, pattern = detect_tricky("It is not prohibited to park here.")
        assert tricky is True
        assert "double-negatives" in pattern

    def test_scope_substitution(self):
        tricky, pattern = detect_tricky("Stop within 30 meters of the crossing.")
        assert tricky is True
        assert "scope-substitution" in pattern

    def test_ignored_exceptions(self):
        tricky, pattern = detect_tricky("Overtaking is prohibited on highways.")
        assert tricky is True
        assert "ignored-exceptions" in pattern

    def test_number_confusion(self):
        tricky, pattern = detect_tricky("You need 45/50 points to pass.")
        assert tricky is True
        assert "number-confusion" in pattern

    def test_no_tricky_pattern(self):
        tricky, pattern = detect_tricky("Drivers should check their mirrors.")
        assert tricky is False
        assert pattern is None

    def test_multiple_patterns(self):
        tricky, pattern = detect_tricky(
            "Drivers must always stop within 30 meters of the crossing."
        )
        assert tricky is True
        assert pattern is not None
        patterns = pattern.split(",")
        assert len(patterns) >= 2

    def test_assertive_language_variants(self):
        """Test various assertive language patterns."""
        for word in ["always", "never", "must", "only", "all", "none", "every"]:
            tricky, pattern = detect_tricky(f"Drivers {word} stop at red lights.")
            assert tricky is True, f"Failed for word: {word}"
            assert "assertive-language" in pattern

    def test_ignored_exceptions_with_exception(self):
        """Test that ignored-exceptions doesn't match when exception is present."""
        tricky, pattern = detect_tricky(
            "Overtaking is prohibited except when visibility is clear."
        )
        # Should still match because the regex uses negative lookahead
        # but the exception word is present, so it should NOT match ignored-exceptions
        assert "ignored-exceptions" not in (pattern or "")


class TestTagTricky:
    def test_tags_all_questions(self, sample_parsed_questions):
        tagged = tag_tricky(sample_parsed_questions)
        tricky_count = sum(1 for q in tagged if q.tricky)
        assert tricky_count > 0

    def test_sets_difficulty_for_tricky(self, sample_parsed_questions):
        tagged = tag_tricky(sample_parsed_questions)
        for q in tagged:
            if q.tricky:
                assert q.difficulty in (4, 5)
            else:
                assert q.difficulty in (1, 2, 3)

    def test_sets_tricky_pattern(self, sample_parsed_questions):
        tagged = tag_tricky(sample_parsed_questions)
        for q in tagged:
            if q.tricky:
                assert q.tricky_pattern is not None
                assert len(q.tricky_pattern) > 0
            else:
                assert q.tricky_pattern is None


# ---------------------------------------------------------------------------
# Raw-to-parsed tests
# ---------------------------------------------------------------------------

class TestRawToParsed:
    def test_converts_all_items(self, sample_raw_questions):
        parsed = raw_to_parsed(sample_raw_questions)
        assert len(parsed) == len(sample_raw_questions)

    def test_normalizes_answers(self, sample_raw_questions):
        parsed = raw_to_parsed(sample_raw_questions)
        for q in parsed:
            assert q.answer_en in ("true", "false")

    def test_skips_empty_prompts(self):
        raw = [
            {"prompt_en": "", "answer_en": "true", "explanation_en": "",
             "theme_slug": "signals", "source_url": "https://x.com",
             "license": "open-source", "attribution": "Test"},
            {"prompt_en": "Valid question", "answer_en": "true", "explanation_en": "",
             "theme_slug": "signals", "source_url": "https://x.com",
             "license": "open-source", "attribution": "Test"},
        ]
        parsed = raw_to_parsed(raw)
        assert len(parsed) == 1

    def test_sets_defaults_for_missing_fields(self):
        raw = [
            {"prompt_en": "Test question", "answer_en": "true",
             "theme_slug": "signals", "source_url": "https://x.com",
             "license": "open-source", "attribution": "Test"},
        ]
        parsed = raw_to_parsed(raw)
        assert parsed[0].explanation_en == ""
        assert parsed[0].raw_text == ""

    def test_preserves_source_metadata(self, github_raw_questions):
        parsed = raw_to_parsed(github_raw_questions)
        for q in parsed:
            assert q.source_url
            assert q.license == "open-source"
            assert "kevincobain2000" in q.attribution


# ---------------------------------------------------------------------------
# Manual review queue tests
# ---------------------------------------------------------------------------

class TestEnqueueReview:
    def test_appends_to_queue(self, tmp_path):
        """Test that review items are appended to the queue file."""
        # Temporarily override the queue path
        import normalize
        original_path = normalize.REVIEW_QUEUE_PATH
        test_path = tmp_path / "test_review_queue.jsonl"
        normalize.REVIEW_QUEUE_PATH = test_path

        try:
            enqueue_review("Test question", "https://example.com", "test reason")
            assert test_path.exists()

            with open(test_path, encoding="utf-8") as f:
                lines = f.readlines()
            assert len(lines) == 1

            item = json.loads(lines[0])
            assert item["raw_text"] == "Test question"
            assert item["source_url"] == "https://example.com"
            assert item["reason"] == "test reason"
        finally:
            normalize.REVIEW_QUEUE_PATH = original_path


# ---------------------------------------------------------------------------
# Integration-style tests (no DB, no Ollama)
# ---------------------------------------------------------------------------

class TestPipelineIntegration:
    def test_full_pipeline_without_persist(self, sample_raw_questions):
        """Test the full pipeline up to (but not including) persistence."""
        # Parse
        parsed = raw_to_parsed(sample_raw_questions)
        assert len(parsed) > 0

        # Dedup
        result = deduplicate(parsed)
        assert len(result.unique) > 0

        # Tag
        tagged = tag_tricky(result.unique)
        tricky_count = sum(1 for q in tagged if q.tricky)
        assert tricky_count > 0

        # Verify all questions have required fields
        for q in tagged:
            assert q.prompt_en
            assert q.answer_en in ("true", "false")
            assert q.theme_slug
            assert q.source_url
            assert q.license
            assert q.attribution

    def test_mixed_source_pipeline(self, mixed_source_questions):
        """Test pipeline with questions from multiple sources."""
        parsed = raw_to_parsed(mixed_source_questions)
        assert len(parsed) > 0

        result = deduplicate(parsed)
        assert len(result.unique) > 0

        tagged = tag_tricky(result.unique)
        # Verify license diversity
        licenses = {q.license for q in tagged}
        assert len(licenses) >= 1  # At least one license type

    def test_all_themes_represented(self, sample_raw_questions, github_raw_questions):
        """Test that combined sources cover multiple themes."""
        combined = sample_raw_questions + github_raw_questions
        parsed = raw_to_parsed(combined)
        themes = {q.theme_slug for q in parsed}
        assert len(themes) >= 5  # At least 5 themes from fixtures

    def test_tricky_ratio_in_fixtures(self, sample_raw_questions):
        """Test that fixture questions have some tricky questions."""
        parsed = raw_to_parsed(sample_raw_questions)
        tagged = tag_tricky(parsed)
        tricky_count = sum(1 for q in tagged if q.tricky)
        # Fixtures should have some tricky questions
        assert tricky_count > 0

    def test_parsed_question_defaults(self):
        """Test ParsedQuestion default values."""
        q = ParsedQuestion(
            prompt_en="Test",
            answer_en="true",
            explanation_en="",
            theme_slug="signals",
            source_url="https://example.com",
            license="open-source",
            attribution="Test",
        )
        assert q.tricky is False
        assert q.tricky_pattern is None
        assert q.difficulty == 3
        assert q.prompt_pt == ""
        assert q.translations_status == "missing"
