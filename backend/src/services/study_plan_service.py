"""Study plan service — weak theme stats, default plan, LLM generation."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.question import Question
from models.theme import Theme
from src.api.repositories.attempt_repo import AttemptRepo
from src.api.repositories.study_plan_repo import StudyPlanRepo
from src.api.repositories.theme_repo import ThemeRepo
from src.config import Settings
from src.llm.answer_parser import parse_study_plan
from src.llm.exceptions import OllamaUnavailableError, StudyPlanParseError
from src.llm.prompts import STUDY_PLAN_SYSTEM, STUDY_PLAN_USER_TEMPLATE
from src.llm.provider import OllamaClient
from src.schemas.study_plan import PlanDay, StudyPlanOut, WeakThemeStat

logger = logging.getLogger(__name__)

ALL_22_THEME_IDS = list(range(1, 23))


class StudyPlanService:
    """Business logic for study plan generation and persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.attempt_repo = AttemptRepo(session)
        self.theme_repo = ThemeRepo(session)
        self.study_plan_repo = StudyPlanRepo(session)

    async def weak_theme_stats(self) -> list[WeakThemeStat]:
        """Compute per-theme wrong-count stats from the past 30 days.

        Returns a list of WeakThemeStat sorted by wrong_count descending.
        Only includes themes that have at least one wrong answer.
        """
        attempts = await self.attempt_repo.list_recent_with_answers(days=30)

        question_ids = {
            aa.question_id
            for attempt in attempts
            for aa in attempt.answers
        }
        if not question_ids:
            return []

        q_result = await self.session.execute(
            select(Question.id, Question.theme_id).where(
                Question.id.in_(question_ids)
            )
        )
        question_theme_map: dict[int, int] = {
            row[0]: row[1] for row in q_result.all()
        }

        theme_ids_seen = set(question_theme_map.values())
        t_result = await self.session.execute(
            select(Theme.id, Theme.name_en).where(Theme.id.in_(theme_ids_seen))
        )
        theme_name_map: dict[int, str] = {
            row[0]: row[1] for row in t_result.all()
        }

        theme_stats: dict[int, dict[str, int]] = {}
        for attempt in attempts:
            for answer in attempt.answers:
                theme_id = question_theme_map.get(answer.question_id)
                if theme_id is None:
                    continue
                if theme_id not in theme_stats:
                    theme_stats[theme_id] = {"wrong": 0, "total": 0}
                theme_stats[theme_id]["total"] += 1
                if not answer.is_correct:
                    theme_stats[theme_id]["wrong"] += 1

        return sorted(
            [
                WeakThemeStat(
                    theme_id=tid,
                    name_en=theme_name_map.get(tid, f"Theme {tid}"),
                    wrong_count=stats["wrong"],
                    total_attempts=stats["total"],
                )
                for tid, stats in theme_stats.items()
                if stats["wrong"] > 0
            ],
            key=lambda x: x.wrong_count,
            reverse=True,
        )

    def build_default_beginner_plan(
        self, available_days: int = 14
    ) -> StudyPlanOut:
        """Build a 14-day beginner plan covering all 22 themes evenly."""
        today = date.today()
        themes_per_day = 22 // available_days
        extra = 22 % available_days

        days: list[PlanDay] = []
        theme_idx = 0
        for day_offset in range(available_days):
            count = themes_per_day + (1 if day_offset < extra else 0)
            day_themes = ALL_22_THEME_IDS[theme_idx : theme_idx + count]
            theme_idx += count

            days.append(
                PlanDay(
                    date=today + timedelta(days=day_offset),
                    theme_ids=day_themes,
                    question_count=20,
                    focus_note_en=f"Review themes: {', '.join(f'Theme {t}' for t in day_themes)}",
                    focus_note_pt=f"Revisar temas: {', '.join(f'Tema {t}' for t in day_themes)}",
                )
            )

        return StudyPlanOut(
            id=0,
            created_at="",
            source="default-beginner",
            days=days,
        )

    async def generate_study_plan(
        self,
        available_days: int = 7,
        hours_per_day: float = 1.5,
        ollama_client: OllamaClient | None = None,
        settings: Settings | None = None,
    ) -> StudyPlanOut:
        """Generate a study plan.

        Flow:
        1. Check weak theme stats from past 30 days.
        2. If empty history → return default 14-day beginner plan.
        3. If history exists → call Ollama with STUDY_PLAN prompts.
        4. Parse LLM response via parse_study_plan.
        5. On StudyPlanParseError → log + fallback to default.
        6. On OllamaUnavailableError → log "ollama_unavailable" + fallback.
        7. Persist the plan via StudyPlanRepo.
        """
        weak_stats = await self.weak_theme_stats()

        if not weak_stats:
            plan = self.build_default_beginner_plan(available_days=14)
            return await self._persist_plan(plan)

        weak_stats_text = "\n".join(
            f"- Theme {s.theme_id} ({s.name_en}): {s.wrong_count} wrong out of {s.total_attempts}"
            for s in weak_stats
        )
        weak_theme_ids = [s.theme_id for s in weak_stats]

        system_prompt = STUDY_PLAN_SYSTEM
        user_prompt = STUDY_PLAN_USER_TEMPLATE.format(
            weak_stats=weak_stats_text,
            available_days=available_days,
            hours_per_day=hours_per_day,
            current_date=date.today().isoformat(),
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        plan: StudyPlanOut | None = None
        if ollama_client is not None:
            try:
                response = await ollama_client.chat(messages)
                plan = parse_study_plan(response, weak_theme_ids)
            except StudyPlanParseError as e:
                logger.warning("study_plan_parse_failed: %s", e)
            except OllamaUnavailableError as e:
                logger.warning("ollama_unavailable: %s", e)

        if plan is None:
            plan = self.build_default_beginner_plan(available_days=14)

        return await self._persist_plan(plan)

    async def _persist_plan(self, plan: StudyPlanOut) -> StudyPlanOut:
        """Persist a study plan and return it with real id/created_at."""
        days_data = []
        for d in plan.days:
            day_dict = d.model_dump()
            day_dict["date"] = day_dict["date"].isoformat()
            days_data.append(day_dict)
        days_json = json.dumps(days_data)
        weak_themes_json = json.dumps(
            [d.theme_ids for d in plan.days]
        ) if plan.days else None

        persisted = await self.study_plan_repo.create(
            days_json=days_json,
            source=plan.source,
            weak_themes_json=weak_themes_json,
        )

        return StudyPlanOut(
            id=persisted.id,
            created_at=persisted.created_at.isoformat(),
            source=persisted.source,
            days=plan.days,
        )
