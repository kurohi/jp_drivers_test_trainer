#!/usr/bin/env python3
"""
Dry-run playbook validator for JP Driver's Test Trainer.

Fetches 5 sample questions from ONE free source (Lease Japan Test 1)
and parses them into the ParsedQuestion schema shape.

Usage:
    cd backend && uv run python ../scripts/dry_run_playbook.py

Output:
    - Prints 5 parsed questions as JSON to stdout
    - Writes review queue items to data/manual_review_queue.jsonl
    - Exits 0 on success, 1 on failure
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).parent.parent
REVIEW_QUEUE_PATH = PROJECT_ROOT / "data" / "manual_review_queue.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "dry_run_output.json"

# Lease Japan Test 1 URL — 50 T/F questions with reasons
SAMPLE_URL = "https://leasejapan.com/en/license-conversion/written-test-guide/test-1/"

# Theme keyword → slug mapping for auto-classification
THEME_KEYWORDS = {
    "novice driver sign": "license-system",
    "following distance": "speed-and-following-distance",
    "overtak": "overtaking-and-passing",
    "pedestrian": "pedestrian-protection",
    "expressway": "highway-driving",
    "parking": "parking-and-stopping",
    "hand signal": "signals",
    "police officer": "signals",
    "traffic sign": "signs-and-markings",
    "breakdown": "accident-response",
    "revers": "parking-and-stopping",
    "centerline": "signs-and-markings",
    "tire": "vehicle-maintenance",
    "intersection": "intersections-and-railroad-crossings",
    "braking": "speed-and-following-distance",
    "blind spot": "blind-spots",
    "coolant": "vehicle-maintenance",
    "garage": "parking-and-stopping",
    "trailer": "highway-driving",
    "bus": "emergency-vehicle-priority",
    "mountain": "adverse-conditions",
    "heavy cargo": "natural-forces",
    "moped": "license-system",
    "engine oil": "vehicle-maintenance",
    "rain": "adverse-conditions",
    "signal": "signals",
    "cargo": "loading-and-passengers",
    "railroad": "intersections-and-railroad-crossings",
    "steering": "vehicle-maintenance",
    "automatic transmission": "vehicle-maintenance",
    "fatigue": "human-factors",
    "drowsy": "human-factors",
    "inspection sticker": "vehicle-maintenance",
    "safety zone": "pedestrian-protection",
    "streetcar": "intersections-and-railroad-crossings",
    "side strip": "highway-driving",
    "standing wave": "natural-forces",
    "hydroplaning": "adverse-conditions",
    "right of way": "intersections-and-railroad-crossings",
    "two-wheeled": "blind-spots",
}

# Tricky-pattern regexes (from sourcing-playbook.md §10)
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
    "term-substitution": None,
    "ignored-exceptions": re.compile(
        r"\b(prohibited|not allowed|forbidden|must not|shall not)\b(?!(.*\b(except|unless|however|but)\b))",
        re.IGNORECASE | re.DOTALL,
    ),
    "number-confusion": re.compile(
        r"\b(\d+)\s*/\s*(\d+)\b",
        re.IGNORECASE,
    ),
}


def detect_tricky(prompt: str) -> tuple[bool, str | None]:
    """Apply the 7-pattern tricky tagger."""
    matched: list[str] = []
    for pattern_slug, pattern in TRICKY_PATTERNS.items():
        if pattern is None:
            continue
        if pattern.search(prompt):
            matched.append(pattern_slug)
    if matched:
        return True, ",".join(matched)
    return False, None


def classify_theme(prompt: str) -> str:
    """Auto-classify a question into one of the 22 themes by keyword matching."""
    prompt_lower = prompt.lower()
    for keyword, slug in THEME_KEYWORDS.items():
        if keyword.lower() in prompt_lower:
            return slug
    return "driver-mindset"  # Default fallback


def normalize_answer(raw: str) -> str:
    """Normalize answer values to 'true' or 'false'."""
    truthy = {"true", "yes", "correct", "○", "o"}
    falsy = {"false", "no", "incorrect", "×", "x"}
    cleaned = raw.strip().lower()
    if cleaned in truthy:
        return "true"
    if cleaned in falsy:
        return "false"
    if any(t in cleaned for t in truthy):
        return "true"
    if any(f in cleaned for f in falsy):
        return "false"
    return raw.strip()


def enqueue_review(raw_text: str, source_url: str, reason: str) -> None:
    """Append an item to the manual-review queue."""
    REVIEW_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW_QUEUE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "raw_text": raw_text,
            "source_url": source_url,
            "reason": reason,
        }, ensure_ascii=False) + "\n")


def parse_lease_japan(html: str, source_url: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """
    Parse Lease Japan Test 1/2/3 HTML into ParsedQuestion dicts.

    Page uses Forminator quiz plugin. Structure per question:
    - <div class="forminator-question" id="question-...">
      - <span class="forminator-legend">QUESTION TEXT</span>
      - <div class="forminator-question--description"><p>Reason: EXPLANATION</p></div>
      - <label class="forminator-answer"><span class="forminator-answer--name">True</span></label>
      - <label class="forminator-answer"><span class="forminator-answer--name">False</span></label>
    """
    soup = BeautifulSoup(html, "lxml")
    questions: list[dict[str, Any]] = []

    # Find all question blocks
    question_divs = soup.find_all("div", class_="forminator-question")

    for q_div in question_divs:
        if len(questions) >= limit:
            break

        # Extract question text from forminator-legend
        legend = q_div.find("span", class_="forminator-legend")
        if not legend:
            continue
        prompt = legend.get_text(separator=" ", strip=True)
        if len(prompt) < 20:
            continue

        # Extract reason/explanation from forminator-question--description
        desc_div = q_div.find("div", class_="forminator-question--description")
        explanation = ""
        if desc_div:
            raw_reason = desc_div.get_text(separator=" ", strip=True)
            if raw_reason.lower().startswith("reason:"):
                explanation = raw_reason[len("Reason:"):].strip()
            else:
                explanation = raw_reason.strip()

        # Extract True/False options
        answer_labels = q_div.find_all("span", class_="forminator-answer--name")
        options = [label.get_text(strip=True) for label in answer_labels]

        if not prompt:
            continue

        # Determine answer from the reason text
        answer = _infer_answer(prompt, explanation)

        tricky, tricky_pattern = detect_tricky(prompt)
        theme_slug = classify_theme(prompt)

        question = {
            "prompt_en": prompt,
            "answer_en": answer,
            "explanation_en": explanation,
            "theme_slug": theme_slug,
            "source_url": source_url,
            "license": "rewrite-required",
            "attribution": "Lease Japan — Written Test Practice",
            "tricky": tricky,
            "tricky_pattern": tricky_pattern,
            "difficulty": 4 if tricky else 2,
            "raw_text": prompt,
        }
        questions.append(question)

        # Flag tricky questions for review
        if tricky:
            enqueue_review(prompt, source_url, f"tricky pattern: {tricky_pattern}")

    return questions


def _infer_answer(statement: str, reason: str) -> str:
    """
    Infer True/False answer from the reason text.

    Lease Japan format: the reason explains the correct answer.
    If the reason contradicts the statement → false.
    If the reason supports/explains the rule → true.
    """
    statement_lower = statement.lower()
    reason_lower = reason.lower()

    contradiction_patterns = [
        r"regardless of",
        r"not\b.*\b(required|necessary|permitted|allowed|must|need)",
        r"prohibited",
        r"forbidden",
        r"shall not",
        r"must not",
        r"should not",
        r"need not",
        r"is called the .* phenomenon",
        r"have the right of way",
        r"\blonger\b",
        r"\bshorter\b",
        r"permitted to pass",
        r"expected to keep",
        r"considered a mechanical failure",
        r"not be utilized",
        r"not be driven",
        r"not impede",
        r"must yield",
        r"should yield",
        r"are prohibited",
        r"is prohibited",
        r"may proceed",
        r"are permitted",
        r"is permitted",
        r"can pass",
        r"may pass",
    ]

    for pattern in contradiction_patterns:
        if re.search(pattern, reason_lower):
            return "false"

    support_patterns = [
        r"this distance",
        r"drivers should remain",
        r"to prevent",
        r"to maintain",
        r"to ensure",
        r"lane assignments",
        r"driving etiquette",
        r"the designated time",
        r"one should drive",
        r"this is necessary",
        r"this distance.*necessary",
        r"remain mindful",
        r"should remain",
    ]

    for pattern in support_patterns:
        if re.search(pattern, reason_lower):
            return "true"

    return "true"


def main() -> int:
    """Fetch 5 sample questions from Lease Japan Test 1 and parse them."""
    print(f"Fetching sample questions from: {SAMPLE_URL}")

    try:
        resp = httpx.get(SAMPLE_URL, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        return 1

    html = resp.text
    questions = parse_lease_japan(html, SAMPLE_URL, limit=5)

    if not questions:
        print("ERROR: No questions parsed. Check HTML structure.", file=sys.stderr)
        return 1

    # Output
    print(f"\nParsed {len(questions)} sample questions:")
    print("=" * 60)

    for idx, q in enumerate(questions, 1):
        print(f"\n--- Question {idx} ---")
        print(f"  Prompt: {q['prompt_en'][:80]}...")
        print(f"  Answer: {q['answer_en']}")
        print(f"  Theme: {q['theme_slug']}")
        print(f"  Tricky: {q['tricky']} ({q['tricky_pattern'] or 'none'})")
        print(f"  Difficulty: {q['difficulty']}")

    # Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    print(f"\nOutput saved to: {OUTPUT_PATH}")

    # Review queue status
    if REVIEW_QUEUE_PATH.exists():
        with open(REVIEW_QUEUE_PATH, encoding="utf-8") as f:
            review_count = sum(1 for _ in f)
        print(f"Manual review queue: {review_count} items at {REVIEW_QUEUE_PATH}")
    else:
        print("Manual review queue: empty (no items flagged)")

    print("\nDry-run completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
