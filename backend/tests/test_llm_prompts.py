"""TDD tests for LLM prompts and answer parsers."""

import pytest

from src.llm.answer_parser import parse_rag_answer, parse_study_plan
from src.llm.exceptions import StudyPlanParseError
from src.llm.prompts import (
    RAG_TEACHER_SYSTEM,
    RAG_TEACHER_USER_TEMPLATE,
    STUDY_PLAN_SYSTEM,
    STUDY_PLAN_USER_TEMPLATE,
)
from src.schemas.rag import RagSourceOut


# ---------------------------------------------------------------------------
# Prompt scope-lock assertions
# ---------------------------------------------------------------------------


def test_rag_teacher_system_scope_lock():
    """RAG_TEACHER_SYSTEM contains scope-lock strings."""
    assert "外免切替" in RAG_TEACHER_SYSTEM
    assert "I can only answer about the JP driver's test. Please rephrase." in RAG_TEACHER_SYSTEM
    assert "Sources:" in RAG_TEACHER_SYSTEM


def test_rag_teacher_user_template_scope_lock():
    """RAG_TEACHER_USER_TEMPLATE contains placeholders and source citation instruction."""
    assert "{context_block}" in RAG_TEACHER_USER_TEMPLATE
    assert "{user_question}" in RAG_TEACHER_USER_TEMPLATE
    assert "Sources:" in RAG_TEACHER_USER_TEMPLATE


def test_study_plan_system_scope_lock():
    """STUDY_PLAN_SYSTEM contains scope-lock and JSON schema definition."""
    assert "STRICTLY the JSON schema" in STUDY_PLAN_SYSTEM
    assert "no prose" in STUDY_PLAN_SYSTEM
    assert '"days"' in STUDY_PLAN_SYSTEM
    assert '"theme_ids"' in STUDY_PLAN_SYSTEM


def test_study_plan_user_template_scope_lock():
    """STUDY_PLAN_USER_TEMPLATE contains all required placeholders."""
    assert "{weak_stats}" in STUDY_PLAN_USER_TEMPLATE
    assert "{available_days}" in STUDY_PLAN_USER_TEMPLATE
    assert "{hours_per_day}" in STUDY_PLAN_USER_TEMPLATE
    assert "{current_date}" in STUDY_PLAN_USER_TEMPLATE


# ---------------------------------------------------------------------------
# parse_rag_answer — well-formed inputs (3 cases)
# ---------------------------------------------------------------------------


def _make_chunk_pool() -> dict[int, RagSourceOut]:
    return {
        1: RagSourceOut(
            source_url="https://example.com/1",
            title="Signals Basics",
            snippet="Red means stop.",
        ),
        3: RagSourceOut(
            source_url="https://example.com/3",
            title="Intersection Rules",
            snippet="Yield to pedestrians.",
        ),
        7: RagSourceOut(
            source_url="https://example.com/7",
            title="Speed Limits",
            snippet="Urban limit is 40 km/h.",
        ),
    }


def test_parse_rag_answer_with_sources():
    """Well-formed: answer text + Sources line with valid indices."""
    pool = _make_chunk_pool()
    raw = (
        "At intersections, you must always yield to pedestrians "
        "crossing the road. The urban speed limit is 40 km/h.\n\n"
        "Sources: [3, 7]"
    )

    result = parse_rag_answer(raw, pool)

    assert "yield to pedestrians" in result.answer
    assert "40 km/h" in result.answer
    assert len(result.sources) == 2
    assert result.sources[0].title == "Intersection Rules"
    assert result.sources[1].title == "Speed Limits"


def test_parse_rag_answer_with_single_source():
    """Well-formed: answer with a single source index."""
    pool = _make_chunk_pool()
    raw = "Red lights mean you must come to a complete stop.\n\nSources: [1]"

    result = parse_rag_answer(raw, pool)

    assert len(result.sources) == 1
    assert result.sources[0].source_url == "https://example.com/1"


def test_parse_rag_answer_no_sources_line():
    """Well-formed: answer without any Sources line → empty sources list."""
    pool = _make_chunk_pool()
    raw = "This is the answer without any source citation."

    result = parse_rag_answer(raw, pool)

    assert result.answer == raw
    assert result.sources == []


# ---------------------------------------------------------------------------
# parse_rag_answer — malformed inputs (3 cases)
# ---------------------------------------------------------------------------


def test_parse_rag_answer_empty_sources_brackets():
    """Malformed: Sources line with empty brackets → empty sources."""
    pool = _make_chunk_pool()
    raw = "Some answer text.\n\nSources: []"

    result = parse_rag_answer(raw, pool)

    assert result.sources == []
    assert "Some answer text" in result.answer


def test_parse_rag_answer_nonexistent_source_index():
    """Malformed: Sources line references index not in pool → skipped."""
    pool = _make_chunk_pool()
    raw = "Answer text.\n\nSources: [99, 3]"

    result = parse_rag_answer(raw, pool)

    # Index 99 is not in pool, only 3 should be resolved
    assert len(result.sources) == 1
    assert result.sources[0].title == "Intersection Rules"


def test_parse_rag_answer_garbage_sources_line():
    """Malformed: Sources line with non-numeric garbage → empty sources."""
    pool = _make_chunk_pool()
    raw = "Answer text.\n\nSources: [abc, xyz, !@#]"

    result = parse_rag_answer(raw, pool)

    assert result.sources == []


# ---------------------------------------------------------------------------
# parse_study_plan — well-formed inputs (3 cases)
# ---------------------------------------------------------------------------

WEAK_THEMES = [1, 3, 7]


def test_parse_study_plan_plain_json():
    """Well-formed: plain JSON without fences."""
    raw = (
        '{"days": ['
        '{"date": "2026-06-24", "theme_ids": [1, 3], "question_count": 30, '
        '"focus_note_en": "Study signals and intersections.", '
        '"focus_note_pt": "Estude sinais e cruzamentos."}, '
        '{"date": "2026-06-25", "theme_ids": [7], "question_count": 20, '
        '"focus_note_en": "Review speed limits.", '
        '"focus_note_pt": "Revise limites de velocidade."}'
        ']}'
    )

    result = parse_study_plan(raw, WEAK_THEMES)

    assert result.source == "llm-generated"
    assert len(result.days) == 2
    assert result.days[0].theme_ids == [1, 3]
    assert result.days[1].theme_ids == [7]


def test_parse_study_plan_with_json_fences():
    """Well-formed: JSON wrapped in ```json fences → fences stripped."""
    raw = (
        "```json\n"
        '{"days": ['
        '{"date": "2026-06-24", "theme_ids": [1], "question_count": 25, '
        '"focus_note_en": "Focus on signals.", '
        '"focus_note_pt": "Foque em sinais."}'
        ']}\n'
        "```"
    )

    result = parse_study_plan(raw, WEAK_THEMES)

    assert len(result.days) == 1
    assert result.days[0].theme_ids == [1]


def test_parse_study_plan_with_markdown_fences_no_lang():
    """Well-formed: JSON wrapped in ``` fences (no lang tag) → stripped."""
    raw = (
        "```\n"
        '{"days": ['
        '{"date": "2026-06-24", "theme_ids": [3, 7], "question_count": 40, '
        '"focus_note_en": "Intersections and speed.", '
        '"focus_note_pt": "Cruzamentos e velocidade."}'
        ']}\n'
        "```"
    )

    result = parse_study_plan(raw, WEAK_THEMES)

    assert len(result.days) == 1
    assert set(result.days[0].theme_ids) == {3, 7}


# ---------------------------------------------------------------------------
# parse_study_plan — malformed inputs (3 cases, all must raise)
# ---------------------------------------------------------------------------


def test_parse_study_plan_invalid_json():
    """Malformed: not valid JSON → raises StudyPlanParseError."""
    raw = "This is not JSON at all."

    with pytest.raises(StudyPlanParseError) as exc_info:
        parse_study_plan(raw, WEAK_THEMES)

    assert "Failed to parse study plan JSON" in str(exc_info.value)


def test_parse_study_plan_hallucinated_theme_ids():
    """Malformed: theme_ids contains IDs not in weak_theme_ids → raises."""
    raw = (
        '{"days": ['
        '{"date": "2026-06-24", "theme_ids": [1, 99], "question_count": 30, '
        '"focus_note_en": "Hallucinated theme.", '
        '"focus_note_pt": "Tema alucinado."}'
        ']}'
    )

    with pytest.raises(StudyPlanParseError) as exc_info:
        parse_study_plan(raw, WEAK_THEMES)

    assert "hallucinated" in str(exc_info.value).lower()
    assert "99" in str(exc_info.value)


def test_parse_study_plan_missing_days_key():
    """Malformed: JSON without 'days' key → raises StudyPlanParseError."""
    raw = '{"plan": [{"date": "2026-06-24"}]}'

    with pytest.raises(StudyPlanParseError) as exc_info:
        parse_study_plan(raw, WEAK_THEMES)

    assert "'days'" in str(exc_info.value)
