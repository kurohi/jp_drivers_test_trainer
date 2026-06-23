#!/usr/bin/env python3
"""
Normalization pipeline for JP Driver's Test Trainer content ingestion.

Pipeline: read raw → parse to QuestionListItem → dedup → tag → translate → persist

Usage:
    uv run python backend/scripts/normalize.py --source github_tsv
    uv run python backend/scripts/normalize.py --source lease_japan
    uv run python backend/scripts/normalize.py --source all
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw_scrapes"
REVIEW_QUEUE_PATH = DATA_DIR / "manual_review_queue.jsonl"
DB_PATH = PROJECT_ROOT / "data" / "jp_drivers.sqlite"

# Add backend/src to path for imports
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "src"))

from config import Settings
from llm.provider import OllamaClient
from models.question import Question
from models.theme import Theme

# ---------------------------------------------------------------------------
# Tricky-pattern regexes (from sourcing-playbook.md §10)
# ---------------------------------------------------------------------------

TRICKY_PATTERNS: dict[str, re.Pattern[str] | None] = {
    "assertive-language": re.compile(
        r"\b(always|never|must|only|all|none|every|no one|under all circumstances)\b",
        re.IGNORECASE,
    ),
    "permission-vs-obligation": re.compile(
        r"\b(may|might|allowed to|permitted to|can)\b.*\b(stop|yield|proceed|pass|turn)\b",
        re.IGNORECASE,
    ),
    "double-negatives": re.compile(
        r"\bnot\b.*\b(prohibited|forbidden|illegal|restricted|banned|allowed|permitted)\b",
        re.IGNORECASE,
    ),
    "scope-substitution": re.compile(
        r"\b(5|10|15|20|30|50)\s*(meters?|m)\b",
        re.IGNORECASE,
    ),
    "term-substitution": None,  # Semantic check — implement separately
    "ignored-exceptions": re.compile(
        r"\b(prohibited|not allowed|forbidden|must not|shall not)\b(?!(.*\b(except|unless|however|but)\b))",
        re.IGNORECASE | re.DOTALL,
    ),
    "number-confusion": re.compile(
        r"\b(\d+)\s*/\s*(\d+)\b",
        re.IGNORECASE,
    ),
}

# ---------------------------------------------------------------------------
# Theme slug → id mapping (loaded from DB)
# ---------------------------------------------------------------------------

THEME_SLUGS = {
    "driver-mindset", "signals", "signs-and-markings", "prohibited-actions",
    "emergency-vehicle-priority", "intersections-and-railroad-crossings",
    "pedestrian-protection", "safety-checks", "overtaking-and-passing",
    "license-system", "blind-spots", "human-factors", "natural-forces",
    "adverse-conditions", "typical-accidents", "vehicle-maintenance",
    "parking-and-stopping", "loading-and-passengers", "accident-response",
    "highway-driving", "route-planning", "speed-and-following-distance",
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ParsedQuestion:
    """Intermediate representation before ORM conversion."""
    prompt_en: str
    answer_en: str
    explanation_en: str
    theme_slug: str
    source_url: str
    license: str
    attribution: str
    raw_text: str = ""
    tricky: bool = False
    tricky_pattern: str | None = None
    difficulty: int = 3
    prompt_pt: str = ""
    answer_pt: str = ""
    explanation_pt: str = ""
    translations_status: str = "missing"


@dataclass
class DedupResult:
    """Result of deduplication pass."""
    unique: list[ParsedQuestion] = field(default_factory=list)
    near_dups: list[dict[str, Any]] = field(default_factory=list)
    exact_dups_skipped: int = 0


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Apply text normalization rules from playbook §9.2."""
    if not text:
        return ""
    # Strip leading/trailing whitespace
    text = text.strip()
    # Normalize multiple spaces to single space
    text = re.sub(r"\s+", " ", text)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Convert smart quotes to straight quotes
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    # Normalize em-dashes and en-dashes to hyphens
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    return text


def normalize_answer(raw: str) -> str:
    """Normalize answer values to 'true' or 'false' (playbook §9.1)."""
    truthy = {"true", "yes", "correct", "○", "o"}
    falsy = {"false", "no", "incorrect", "×", "x"}
    cleaned = raw.strip().lower()
    if cleaned in truthy:
        return "true"
    if cleaned in falsy:
        return "false"
    # Fallback: check substring
    if any(t in cleaned for t in truthy):
        return "true"
    if any(f in cleaned for f in falsy):
        return "false"
    return cleaned


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _dedup_key(prompt: str) -> str:
    """Generate a dedup key: lowercase + strip punctuation."""
    return re.sub(r"[^\w\s]", "", prompt.lower()).strip()


def deduplicate(
    questions: list[ParsedQuestion],
    existing_keys: set[str] | None = None,
    near_dup_threshold: float = 85.0,
) -> DedupResult:
    """
    Deduplicate questions.

    - Exact dedup: lowercase + strip punctuation → compare
    - Near-dup: rapidfuzz ratio > threshold → flag for manual review
    """
    if existing_keys is None:
        existing_keys = set()

    result = DedupResult()
    seen_keys: set[str] = set(existing_keys)

    for q in questions:
        key = _dedup_key(q.prompt_en)

        if key in seen_keys:
            result.exact_dups_skipped += 1
            continue

        # Check near-dups against already-accepted questions
        is_near_dup = False
        for accepted in result.unique:
            accepted_key = _dedup_key(accepted.prompt_en)
            ratio = fuzz.ratio(key, accepted_key)
            if ratio > near_dup_threshold:
                result.near_dups.append({
                    "raw_text": q.prompt_en,
                    "source_url": q.source_url,
                    "reason": f"near-duplicate ({ratio:.0f}% similar to existing question)",
                })
                is_near_dup = True
                break

        if is_near_dup:
            continue

        seen_keys.add(key)
        result.unique.append(q)

    return result


# ---------------------------------------------------------------------------
# Tricky-pattern tagger
# ---------------------------------------------------------------------------

def detect_tricky(prompt: str) -> tuple[bool, str | None]:
    """Apply the 7-pattern tricky tagger to a question prompt."""
    matched: list[str] = []
    for pattern_slug, pattern in TRICKY_PATTERNS.items():
        if pattern is None:
            continue
        if pattern.search(prompt):
            matched.append(pattern_slug)
    if matched:
        return True, ",".join(matched)
    return False, None


def tag_tricky(questions: list[ParsedQuestion]) -> list[ParsedQuestion]:
    """Tag questions with tricky patterns."""
    for q in questions:
        tricky, pattern = detect_tricky(q.prompt_en)
        q.tricky = tricky
        q.tricky_pattern = pattern
        if tricky:
            q.difficulty = 4 if len(pattern.split(",")) == 1 else 5
        else:
            q.difficulty = 2
    return questions


# ---------------------------------------------------------------------------
# Translation via Ollama
# ---------------------------------------------------------------------------

TRANSLATE_PROMPT_EN_TO_PT = textwrap.dedent("""\
Translate the following Japanese driver's license test question from English to Portuguese (Brazil).
Only output the translation, nothing else.

English: {text}
Portuguese:""")

TRANSLATE_ANSWER_PROMPT = textwrap.dedent("""\
Translate the following answer/explanation from English to Portuguese (Brazil).
Only output the translation, nothing else.

English: {text}
Portuguese:""")

PARAPHRASE_PROMPT = textwrap.dedent("""\
Rewrite the following driver's license test question in different words while preserving the exact meaning and true/false answer.
Only output the rewritten question, nothing else.

Original: {text}
Rewritten:""")


async def translate_questions(
    questions: list[ParsedQuestion],
    ollama: OllamaClient,
    *,
    batch_size: int = 5,
) -> list[ParsedQuestion]:
    """Translate questions to PT using Ollama."""
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        tasks = []
        for q in batch:
            tasks.append(_translate_single(q, ollama))
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(0.5)  # Rate limit

    return questions


async def _translate_single(q: ParsedQuestion, ollama: OllamaClient) -> None:
    """Translate a single question to PT."""
    try:
        # Translate prompt
        prompt_pt = await ollama.chat([
            {"role": "user", "content": TRANSLATE_PROMPT_EN_TO_PT.format(text=q.prompt_en)},
        ], temperature=0.1, num_predict=500)
        q.prompt_pt = prompt_pt.strip()

        # Translate answer
        answer_pt = await ollama.chat([
            {"role": "user", "content": TRANSLATE_ANSWER_PROMPT.format(text=q.answer_en)},
        ], temperature=0.1, num_predict=100)
        q.answer_pt = answer_pt.strip().lower()
        if "verdadeiro" in q.answer_pt or "sim" in q.answer_pt or "certo" in q.answer_pt:
            q.answer_pt = "verdadeiro"
        else:
            q.answer_pt = "falso"

        # Translate explanation if present
        if q.explanation_en:
            expl_pt = await ollama.chat([
                {"role": "user", "content": TRANSLATE_ANSWER_PROMPT.format(text=q.explanation_en)},
            ], temperature=0.1, num_predict=500)
            q.explanation_pt = expl_pt.strip()
        else:
            q.explanation_pt = ""

        q.translations_status = "machine"
    except Exception as e:
        print(f"Translation failed for question: {e}")
        # Fallback: copy EN to PT
        q.prompt_pt = q.prompt_en
        q.answer_pt = "verdadeiro" if q.answer_en == "true" else "falso"
        q.explanation_pt = q.explanation_en
        q.translations_status = "machine"


async def paraphrase_questions(
    questions: list[ParsedQuestion],
    ollama: OllamaClient,
    *,
    batch_size: int = 5,
) -> list[ParsedQuestion]:
    """Paraphrase rewrite-required questions."""
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        tasks = []
        for q in batch:
            if q.license == "rewrite-required":
                tasks.append(_paraphrase_single(q, ollama))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(0.5)

    return questions


async def _paraphrase_single(q: ParsedQuestion, ollama: OllamaClient) -> None:
    """Paraphrase a single question."""
    try:
        rewritten = await ollama.chat([
            {"role": "user", "content": PARAPHRASE_PROMPT.format(text=q.prompt_en)},
        ], temperature=0.3, num_predict=500)
        q.prompt_en = rewritten.strip()
        q.license = "paraphrased"
    except Exception as e:
        print(f"Paraphrase failed: {e}")


# ---------------------------------------------------------------------------
# Manual review queue
# ---------------------------------------------------------------------------

def enqueue_review(raw_text: str, source_url: str, reason: str) -> None:
    """Append an item to the manual-review queue."""
    REVIEW_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_QUEUE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "raw_text": raw_text,
            "source_url": source_url,
            "reason": reason,
        }, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Persistence — uses QuestionRepo.bulk_create from T8
# ---------------------------------------------------------------------------

async def persist_questions(
    questions: list[ParsedQuestion],
    theme_slug_to_id: dict[str, int],
) -> int:
    """Persist questions to SQLite via QuestionRepo.bulk_create (T8)."""
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

    if not DB_PATH.exists():
        print("Database not found.")
        return 0

    # Set up async engine for SQLite
    db_url = f"sqlite+aiosqlite:///{DB_PATH}"
    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    created = 0
    async with async_session() as session:
        # Import ORM model and repo
        from models.question import Question
        from api.repositories.question_repo import QuestionRepo

        repo = QuestionRepo(session)
        orm_questions = []

        for q in questions:
            theme_id = theme_slug_to_id.get(q.theme_slug)
            if theme_id is None:
                continue

            # Ensure required fields
            source_url = q.source_url or "unknown"
            license_val = q.license or "rewrite-required"
            attribution = q.attribution or "Unknown"
            prompt_pt = q.prompt_pt or q.prompt_en
            answer_pt = q.answer_pt or ("verdadeiro" if q.answer_en == "true" else "falso")
            explanation_pt = q.explanation_pt or q.explanation_en

            orm_q = Question(
                theme_id=theme_id,
                prompt_en=q.prompt_en,
                prompt_pt=prompt_pt,
                answer_en=q.answer_en,
                answer_pt=answer_pt,
                explanation_en=q.explanation_en,
                explanation_pt=explanation_pt,
                tricky=q.tricky,
                tricky_pattern=q.tricky_pattern,
                difficulty=q.difficulty,
                translations_status=q.translations_status,
                source_url=source_url,
                license=license_val,
                attribution=attribution,
            )
            orm_questions.append(orm_q)

        if orm_questions:
            await repo.bulk_create(orm_questions)
            await session.commit()
            created = len(orm_questions)

    await engine.dispose()
    return created


def load_theme_map() -> dict[str, int]:
    """Load theme slug → id mapping from DB."""
    import sqlite3
    import sqlite_vec

    if not DB_PATH.exists():
        print("Database not found. Run apply_migrations.py and seed_themes.py first.")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())

    cursor = conn.execute("SELECT slug, id FROM themes WHERE parent_id IS NULL")
    slug_to_id = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return slug_to_id


def load_existing_dedup_keys() -> set[str]:
    """Load existing question dedup keys from DB."""
    import sqlite3
    import sqlite_vec

    if not DB_PATH.exists():
        return set()

    conn = sqlite3.connect(str(DB_PATH))
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())

    cursor = conn.execute("SELECT prompt_en FROM questions")
    keys = {_dedup_key(row[0]) for row in cursor.fetchall()}
    conn.close()
    return keys


# ---------------------------------------------------------------------------
# Source loaders
# ---------------------------------------------------------------------------

def load_raw_source(source: str) -> list[dict[str, Any]]:
    """Load raw JSON from a source's scrape directory."""
    source_dir = RAW_DIR / source
    if not source_dir.exists():
        print(f"Raw directory not found: {source_dir}")
        return []

    all_items: list[dict[str, Any]] = []
    for json_file in sorted(source_dir.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                all_items.extend(data)
            elif isinstance(data, dict):
                all_items.append(data)

    return all_items


def raw_to_parsed(raw_items: list[dict[str, Any]]) -> list[ParsedQuestion]:
    """Convert raw dicts to ParsedQuestion objects."""
    questions = []
    for item in raw_items:
        q = ParsedQuestion(
            prompt_en=normalize_text(item.get("prompt_en", "")),
            answer_en=normalize_answer(item.get("answer_en", "false")),
            explanation_en=normalize_text(item.get("explanation_en", "")),
            theme_slug=item.get("theme_slug", "driver-mindset"),
            source_url=item.get("source_url", ""),
            license=item.get("license", "rewrite-required"),
            attribution=item.get("attribution", ""),
            raw_text=item.get("raw_text", ""),
        )
        if q.prompt_en:
            questions.append(q)
    return questions


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def run_pipeline(source: str, *, translate: bool = True, paraphrase: bool = True) -> dict[str, int]:
    """
    Run the full normalization pipeline for a source.

    Returns stats dict.
    """
    print(f"\n{'='*60}")
    print(f"Pipeline: {source}")
    print(f"{'='*60}")

    # Step 1: Load raw data
    print("\n[1/6] Loading raw data...")
    raw_items = load_raw_source(source)
    print(f"  Loaded {len(raw_items)} raw items")

    if not raw_items:
        print("  No raw data found. Run the scraper first.")
        return {"loaded": 0, "parsed": 0, "unique": 0, "tagged_tricky": 0, "persisted": 0}

    # Step 2: Parse to ParsedQuestion
    print("\n[2/6] Parsing to ParsedQuestion...")
    parsed = raw_to_parsed(raw_items)
    print(f"  Parsed {len(parsed)} questions")

    # Step 3: Deduplicate
    print("\n[3/6] Deduplicating...")
    existing_keys = load_existing_dedup_keys()
    dedup_result = deduplicate(parsed, existing_keys=existing_keys)
    print(f"  Unique: {len(dedup_result.unique)}")
    print(f"  Exact dups skipped: {dedup_result.exact_dups_skipped}")
    print(f"  Near-dups flagged: {len(dedup_result.near_dups)}")

    # Write near-dups to review queue
    for nd in dedup_result.near_dups:
        enqueue_review(nd["raw_text"], nd["source_url"], nd["reason"])

    questions = dedup_result.unique

    # Step 4: Tag tricky patterns
    print("\n[4/6] Tagging tricky patterns...")
    questions = tag_tricky(questions)
    tricky_count = sum(1 for q in questions if q.tricky)
    tricky_pct = (tricky_count / len(questions) * 100) if questions else 0
    print(f"  Tricky: {tricky_count} ({tricky_pct:.1f}%)")

    # Flag assertive-language matches for review
    for q in questions:
        if q.tricky_pattern and "assertive-language" in q.tricky_pattern:
            enqueue_review(q.prompt_en, q.source_url, f"assertive-language pattern match; verify accuracy")

    # Step 5: Translate + Paraphrase
    if translate or paraphrase:
        print("\n[5/6] Translating/Paraphrasing via Ollama...")
        settings = Settings()
        ollama = OllamaClient(settings)

        if paraphrase:
            rewrite_questions = [q for q in questions if q.license == "rewrite-required"]
            if rewrite_questions:
                print(f"  Paraphrasing {len(rewrite_questions)} rewrite-required questions...")
                questions = await paraphrase_questions(rewrite_questions, ollama)

        if translate:
            print(f"  Translating {len(questions)} questions to PT...")
            questions = await translate_questions(questions, ollama)

        await ollama.close()

    # Step 6: Persist
    print("\n[6/6] Persisting to database...")
    theme_map = load_theme_map()
    persisted = await persist_questions(questions, theme_map)
    print(f"  Persisted {persisted} questions")

    # Summary
    print(f"\n{'='*60}")
    print(f"Pipeline complete for {source}")
    print(f"  Loaded: {len(raw_items)}")
    print(f"  Parsed: {len(parsed)}")
    print(f"  Unique after dedup: {len(questions)}")
    print(f"  Tricky: {tricky_count} ({tricky_pct:.1f}%)")
    print(f"  Persisted: {persisted}")
    print(f"{'='*60}")

    return {
        "loaded": len(raw_items),
        "parsed": len(parsed),
        "unique": len(questions),
        "tagged_tricky": tricky_count,
        "persisted": persisted,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="JP Drivers Test normalization pipeline")
    parser.add_argument(
        "--source",
        default="all",
        help="Source to process (or 'all' for all sources)",
    )
    parser.add_argument(
        "--no-translate",
        action="store_true",
        help="Skip Ollama translation",
    )
    parser.add_argument(
        "--no-paraphrase",
        action="store_true",
        help="Skip Ollama paraphrasing",
    )
    args = parser.parse_args()

    sources = ["all"] if args.source == "all" else [args.source]

    if "all" in sources:
        # Discover all source directories
        sources = [d.name for d in RAW_DIR.iterdir() if d.is_dir()]

    total_stats = {
        "loaded": 0, "parsed": 0, "unique": 0, "tagged_tricky": 0, "persisted": 0
    }

    for source in sources:
        stats = asyncio.run(run_pipeline(
            source,
            translate=not args.no_translate,
            paraphrase=not args.no_paraphrase,
        ))
        for key in total_stats:
            total_stats[key] += stats[key]

    print(f"\n{'='*60}")
    print(f"TOTALS across all sources")
    print(f"{'='*60}")
    for key, val in total_stats.items():
        print(f"  {key}: {val}")

    # Verify targets
    print(f"\n{'='*60}")
    print(f"TARGET VERIFICATION")
    print(f"{'='*60}")

    # Count total questions in DB
    import sqlite3
    import sqlite_vec

    db_path = DB_PATH
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.enable_load_extension(True)
        conn.load_extension(sqlite_vec.loadable_path())

        total_q = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        tricky_q = conn.execute("SELECT COUNT(*) FROM questions WHERE tricky = 1").fetchone()[0]
        themes_with_q = conn.execute(
            "SELECT COUNT(DISTINCT theme_id) FROM questions"
        ).fetchone()[0]
        tricky_pct = (tricky_q / total_q * 100) if total_q > 0 else 0

        print(f"  Total questions in DB: {total_q} (target: ≥660)")
        print(f"  Tricky questions: {tricky_q} ({tricky_pct:.1f}%, target: ≥40%)")
        print(f"  Themes with questions: {themes_with_q} (target: 22)")

        if total_q >= 660:
            print("  ✅ Question count target met")
        else:
            print(f"  ❌ Need {660 - total_q} more questions")

        if tricky_pct >= 40:
            print("  ✅ Tricky ratio target met")
        else:
            print(f"  ❌ Need more tricky questions (current: {tricky_pct:.1f}%)")

        if themes_with_q >= 22:
            print("  ✅ All themes covered")
        else:
            print(f"  ❌ {22 - themes_with_q} themes still empty")

        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
