"""TDD round-trip validation for all Pydantic schemas.

Tests:
1. Every *Out schema round-trips: model_dump_json -> model_validate -> identical
2. QuestionListItem does NOT have answer_en/answer_pt/explanation_en/explanation_pt fields
3. QuestionDetail (inherit from QuestionListItem) DOES have those fields
"""

from datetime import date, datetime

import pytest
from pydantic import BaseModel

from src.schemas import (
    AttemptAnswerOut,
    AttemptResultOut,
    AttemptStartIn,
    AttemptSubmitIn,
    AnswerItem,
    Difficulty,
    Language,
    PlanDay,
    QuestionDetail,
    QuestionListItem,
    RagAnswerOut,
    RagQueryIn,
    RagSourceOut,
    SkillModuleOut,
    StudyPlanGenerateIn,
    StudyPlanOut,
    ThemeOut,
    ThemeTreeOut,
    WeakThemeStat,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def round_trip(schema_cls: type[BaseModel], instance: BaseModel) -> BaseModel:
    """Dump to JSON and re-parse; assert equality."""
    json_str = instance.model_dump_json()
    parsed = schema_cls.model_validate_json(json_str)
    assert parsed == instance, f"Round-trip failed for {schema_cls.__name__}"
    return parsed


# ---------------------------------------------------------------------------
# Theme schemas
# ---------------------------------------------------------------------------


class TestThemeSchemas:
    def test_theme_out_round_trip(self):
        t = ThemeOut(
            id=1,
            slug="traffic-signs",
            name_en="Traffic Signs",
            name_pt="Sinais de Trânsito",
            parent_id=None,
            sort_order=0,
        )
        round_trip(ThemeOut, t)

    def test_theme_out_with_parent(self):
        t = ThemeOut(
            id=2,
            slug="regulatory-signs",
            name_en="Regulatory Signs",
            name_pt="Sinais Regulamentares",
            parent_id=1,
            sort_order=1,
        )
        round_trip(ThemeOut, t)

    def test_theme_tree_out_round_trip(self):
        child = ThemeTreeOut(
            id=2,
            slug="regulatory",
            name_en="Regulatory",
            name_pt="Regulamentar",
            parent_id=1,
            sort_order=1,
            children=[],
        )
        parent = ThemeTreeOut(
            id=1,
            slug="signs",
            name_en="Signs",
            name_pt="Sinais",
            parent_id=None,
            sort_order=0,
            children=[child],
        )
        round_trip(ThemeTreeOut, parent)


# ---------------------------------------------------------------------------
# Question schemas — CRITICAL: no answer leakage
# ---------------------------------------------------------------------------


class TestQuestionSchemas:
    def test_question_list_item_round_trip(self):
        q = QuestionListItem(
            id=1,
            theme_id=3,
            prompt_en="What does a red octagon sign mean?",
            prompt_pt="O que significa um sinal vermelho octogonal?",
            tricky=False,
            tricky_pattern=None,
            difficulty=0.5,
            translations_status="complete",
        )
        round_trip(QuestionListItem, q)

    def test_question_list_item_with_tricky_pattern(self):
        q = QuestionListItem(
            id=2,
            theme_id=3,
            prompt_en="This is a tricky question",
            prompt_pt="Esta é uma pergunta complicada",
            tricky=True,
            tricky_pattern="misleading-color",
            difficulty=0.75,
            translations_status="en_only",
        )
        round_trip(QuestionListItem, q)

    def test_question_list_item_does_not_have_answer_fields(self):
        """CRITICAL: QuestionListItem must NOT expose answers in mock-test UI."""
        fields = set(QuestionListItem.model_fields.keys())
        leak_fields = {"answer_en", "answer_pt", "explanation_en", "explanation_pt"}
        intersection = fields & leak_fields
        assert not intersection, (
            f"QuestionListItem leaks answer fields: {intersection}. "
            "These fields must only exist in QuestionDetail."
        )

    def test_question_detail_round_trip(self):
        q = QuestionDetail(
            id=1,
            theme_id=3,
            prompt_en="What does a red octagon sign mean?",
            prompt_pt="O que significa um sinal vermelho octogonal?",
            tricky=False,
            tricky_pattern=None,
            difficulty=0.5,
            translations_status="complete",
            answer_en="Stop",
            answer_pt="Pare",
            explanation_en="A red octagon universally means Stop.",
            explanation_pt="Um octógono vermelho significa universalmente Pare.",
        )
        round_trip(QuestionDetail, q)

    def test_question_detail_has_answer_fields(self):
        """QuestionDetail SHOULD have answer fields (for admin/review UIs)."""
        fields = set(QuestionDetail.model_fields.keys())
        assert "answer_en" in fields
        assert "answer_pt" in fields
        assert "explanation_en" in fields
        assert "explanation_pt" in fields

    def test_difficulty_literal_values(self):
        """Difficulty must be one of the allowed Literal values."""
        for d in [0.0, 0.25, 0.5, 0.75, 1.0]:
            q = QuestionListItem(
                id=1,
                theme_id=1,
                prompt_en="test",
                prompt_pt="teste",
                tricky=False,
                tricky_pattern=None,
                difficulty=d,
                translations_status="complete",
            )
            assert q.difficulty == d


# ---------------------------------------------------------------------------
# Attempt schemas
# ---------------------------------------------------------------------------


class TestAttemptSchemas:
    def test_attempt_start_in_defaults(self):
        inp = AttemptStartIn(language="en")
        assert inp.theme_ids is None
        assert inp.question_count == 50
        assert inp.tricky_ratio == 0.5
        assert inp.time_limit_seconds == 1800
        assert inp.seed is None

    def test_attempt_start_in_round_trip(self):
        inp = AttemptStartIn(
            language="pt",
            theme_ids=[1, 2, 3],
            question_count=25,
            tricky_ratio=0.25,
            time_limit_seconds=900,
            seed=42,
        )
        round_trip(AttemptStartIn, inp)

    def test_answer_item_round_trip(self):
        a = AnswerItem(question_id=5, user_answer="true", time_spent_ms=1234)
        round_trip(AnswerItem, a)

    def test_answer_item_false_answer(self):
        a = AnswerItem(question_id=6, user_answer="false", time_spent_ms=None)
        round_trip(AnswerItem, a)

    def test_attempt_submit_in_round_trip(self):
        inp = AttemptSubmitIn(
            answers=[
                AnswerItem(question_id=1, user_answer="true", time_spent_ms=500),
                AnswerItem(question_id=2, user_answer="false", time_spent_ms=None),
            ]
        )
        round_trip(AttemptSubmitIn, inp)

    def test_attempt_answer_out_round_trip(self):
        a = AttemptAnswerOut(
            question_id=1,
            is_correct=True,
            user_answer="true",
            correct_answer="true",
            explanation_en="Correct!",
            explanation_pt="Correto!",
        )
        round_trip(AttemptAnswerOut, a)

    def test_attempt_result_out_round_trip(self):
        result = AttemptResultOut(
            attempt_id=1,
            score=38,
            max_score=50,
            passed=False,
            tricky_ratio_actual=0.52,
            boundary_score=45,
            answers=[
                AttemptAnswerOut(
                    question_id=1,
                    is_correct=True,
                    user_answer="true",
                    correct_answer="true",
                    explanation_en="Correct!",
                    explanation_pt="Correto!",
                ),
            ],
        )
        round_trip(AttemptResultOut, result)


# ---------------------------------------------------------------------------
# Study plan schemas
# ---------------------------------------------------------------------------


class TestStudyPlanSchemas:
    def test_study_plan_generate_in_defaults(self):
        inp = StudyPlanGenerateIn()
        assert inp.available_days == 7
        assert inp.hours_per_day == 1.5

    def test_study_plan_generate_in_round_trip(self):
        inp = StudyPlanGenerateIn(available_days=14, hours_per_day=2.0)
        round_trip(StudyPlanGenerateIn, inp)

    def test_weak_theme_stat_round_trip(self):
        s = WeakThemeStat(
            theme_id=3,
            name_en="Road Signs",
            wrong_count=7,
            total_attempts=20,
        )
        round_trip(WeakThemeStat, s)

    def test_plan_day_round_trip(self):
        day = PlanDay(
            date=date(2026, 6, 25),
            theme_ids=[1, 2],
            question_count=30,
            focus_note_en="Focus on regulatory signs",
            focus_note_pt="Foco em sinais regulamentares",
        )
        round_trip(PlanDay, day)

    def test_study_plan_out_round_trip(self):
        plan = StudyPlanOut(
            id=1,
            created_at="2026-06-23T10:00:00",
            source="llm-generated",
            days=[
                PlanDay(
                    date=date(2026, 6, 25),
                    theme_ids=[1],
                    question_count=15,
                    focus_note_en="Basics",
                    focus_note_pt="Básicos",
                ),
            ],
        )
        round_trip(StudyPlanOut, plan)

    def test_study_plan_source_literal(self):
        for src in ["default-beginner", "llm-generated"]:
            plan = StudyPlanOut(
                id=1,
                created_at="2026-06-23T10:00:00",
                source=src,  # type: ignore
                days=[],
            )
            assert plan.source == src


# ---------------------------------------------------------------------------
# RAG schemas
# ---------------------------------------------------------------------------


class TestRagSchemas:
    def test_rag_query_in_defaults(self):
        q = RagQueryIn(question="What does a yield sign look like?", language="en")
        assert q.k == 5

    def test_rag_query_in_round_trip(self):
        q = RagQueryIn(question="Quel est ce panneau?", language="pt", k=10)
        round_trip(RagQueryIn, q)

    def test_rag_source_out_round_trip(self):
        s = RagSourceOut(
            source_url="https://example.com/signs",
            title="Traffic Signs Guide",
            snippet="A yield sign is a downward-pointing triangle...",
        )
        round_trip(RagSourceOut, s)

    def test_rag_answer_out_round_trip(self):
        a = RagAnswerOut(
            answer="A yield sign is a downward-pointing triangle.",
            sources=[
                RagSourceOut(
                    source_url="https://example.com/signs",
                    title="Traffic Signs Guide",
                    snippet="A yield sign is a downward-pointing triangle...",
                ),
            ],
        )
        round_trip(RagAnswerOut, a)


# ---------------------------------------------------------------------------
# Skill schema
# ---------------------------------------------------------------------------


class TestSkillSchema:
    def test_skill_module_out_round_trip(self):
        s = SkillModuleOut(
            id=1,
            slug="yield-signs",
            name_en="Yield Signs",
            name_pt="Sinais de Cedência",
            sort_order=1,
            overview_en="Learn about yield signs",
            overview_pt="Aprenda sobre sinais de cedência",
            svg_path="/assets/skills/yield-signs.svg",
            correct_trajectory_json='{"pattern": "triangle-down"}',
            wrong_trajectory_json='{"pattern": "circle-red"}',
            common_mistakes_json='["confusing-with-stop"]',
            checklist_json='["identify-shape","identify-color"]',
            pro_tip_en="Look for the upside-down triangle shape.",
            pro_tip_pt="Procure a forma de triângulo invertido.",
        )
        round_trip(SkillModuleOut, s)


# ---------------------------------------------------------------------------
# UI meta types
# ---------------------------------------------------------------------------


class TestUiMeta:
    def test_language_literal(self):
        for lang in ["en", "pt"]:
            assert lang in Language.__args__  # type: ignore

    def test_difficulty_literal_values(self):
        expected = (0.0, 0.25, 0.5, 0.75, 1.0)
        assert Difficulty.__args__ == expected  # type: ignore
