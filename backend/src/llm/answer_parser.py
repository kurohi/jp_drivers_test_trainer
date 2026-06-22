"""Robust parsers for LLM output — RAG answers and study plans."""

import json
import re

from pydantic import ValidationError

from src.llm.exceptions import StudyPlanParseError
from src.schemas.rag import RagAnswerOut, RagSourceOut
from src.schemas.study_plan import StudyPlanOut


def parse_rag_answer(
    raw_text: str,
    chunk_pool: dict[int, RagSourceOut],
) -> RagAnswerOut:
    """Parse a RAG teacher response into structured output.

    Extracts the prose answer and scans for a "Sources:" line to map
    chunk indices to RagSourceOut objects. Returns sources=[] defensively
    when no "Sources:" line is found.

    Args:
        raw_text: The raw LLM response text.
        chunk_pool: Mapping of chunk index → RagSourceOut for source resolution.

    Returns:
        RagAnswerOut with cleaned answer text and resolved sources.
    """
    # Split off the "Sources:" line if present
    sources_line_match = re.search(
        r"\nSources:\s*\[([^\]]*)\]\s*$", raw_text, re.MULTILINE
    )

    sources: list[RagSourceOut] = []
    answer_text = raw_text

    if sources_line_match:
        # Extract the answer text (everything before the Sources line)
        answer_text = raw_text[: sources_line_match.start()].strip()

        # Parse the index list
        indices_str = sources_line_match.group(1).strip()
        if indices_str:
            for token in indices_str.split(","):
                token = token.strip()
                if token.isdigit():
                    idx = int(token)
                    if idx in chunk_pool:
                        sources.append(chunk_pool[idx])

    return RagAnswerOut(answer=answer_text, sources=sources)


def parse_study_plan(
    raw_text: str,
    weak_theme_ids: list[int],
) -> StudyPlanOut:
    """Parse a study plan LLM response into structured output.

    Strips ```json markdown fences if present, parses JSON, validates
    against the StudyPlanOut schema, and enforces that all theme_ids
    are a subset of the allowed weak_theme_ids.

    Args:
        raw_text: The raw LLM response text (may contain markdown fences).
        weak_theme_ids: The set of allowed theme IDs (from user's weak areas).

    Returns:
        Validated StudyPlanOut.

    Raises:
        StudyPlanParseError: On JSON decode failure, schema validation
            failure, or hallucinated theme_ids not in weak_theme_ids.
    """
    allowed_theme_ids = set(weak_theme_ids)

    # Strip markdown code fences if present
    cleaned = raw_text.strip()
    fence_match = re.match(
        r"```(?:json)?\s*\n(.*?)\n```\s*$", cleaned, re.DOTALL
    )
    if fence_match:
        cleaned = fence_match.group(1).strip()

    # Parse JSON
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise StudyPlanParseError(
            f"Failed to parse study plan JSON: {e}"
        ) from e

    # Validate against Pydantic schema
    # The LLM returns {"days": [...]}, but StudyPlanOut also needs id, created_at, source.
    # We inject defaults for those fields since they are route-layer concerns.
    if not isinstance(data, dict) or "days" not in data:
        raise StudyPlanParseError(
            "Study plan JSON must contain a 'days' key at the top level."
        )

    # Enforce theme_ids ⊆ weak_theme_ids before Pydantic validation
    days_data = data.get("days", [])
    if not isinstance(days_data, list):
        raise StudyPlanParseError("'days' must be a list.")

    for i, day in enumerate(days_data):
        if not isinstance(day, dict):
            raise StudyPlanParseError(
                f"Day {i} is not a valid object."
            )
        day_themes = day.get("theme_ids", [])
        if not isinstance(day_themes, list):
            raise StudyPlanParseError(
                f"Day {i} theme_ids is not a list."
            )
        hallucinated = set(day_themes) - allowed_theme_ids
        if hallucinated:
            raise StudyPlanParseError(
                f"Day {i} contains hallucinated theme_ids not in weak areas: "
                f"{sorted(hallucinated)}. Allowed: {sorted(allowed_theme_ids)}."
            )

    # Build the full StudyPlanOut with injected defaults
    try:
        plan = StudyPlanOut.model_validate(
            {
                "id": 0,  # Placeholder — route layer assigns real ID
                "created_at": "",  # Placeholder — route layer sets timestamp
                "source": "llm-generated",
                "days": days_data,
            }
        )
    except ValidationError as e:
        raise StudyPlanParseError(
            f"Study plan failed schema validation: {e}"
        ) from e

    return plan
