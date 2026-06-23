#!/usr/bin/env python3
"""
Scraper for kevincobain2000's GitHub repo with MIT-licensed questions.

URL: https://raw.githubusercontent.com/kevincobain2000/japan-drivers-license-practice-test-questions-english/master/questions.tsv
TSV format: question\t\tanswer\texplanation
License: open-source (MIT)
"""
from __future__ import annotations

import asyncio
import csv
import io
import json
import re
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw_scrapes" / "github_tsv"

TSV_URL = "https://raw.githubusercontent.com/kevincobain2000/japan-drivers-license-practice-test-questions-english/master/questions.tsv"

THEME_KEYWORDS = {
    "signals": ["signal", "turn signal", "indicator"],
    "intersections-and-railroad-crossings": ["intersection", "railroad", "crossing"],
    "pedestrian-protection": ["pedestrian", "crosswalk"],
    "blind-spots": ["blind spot", "mirror"],
    "safety-checks": ["check", "inspection", "safety"],
    "parking-and-stopping": ["park", "stop"],
    "overtaking-and-passing": ["overtak", "pass"],
    "highway-driving": ["expressway", "highway"],
    "adverse-conditions": ["rain", "night", "wet"],
    "driver-mindset": ["confidence", "caution"],
    "prohibited-actions": ["prohibited", "must not"],
    "emergency-vehicle-priority": ["emergency", "ambulance"],
    "speed-and-following-distance": ["speed", "distance"],
    "vehicle-maintenance": ["tire", "oil", "engine"],
    "signs-and-markings": ["sign", "marking"],
    "human-factors": ["fatigue", "drowsy"],
    "natural-forces": ["inertia", "gravity"],
    "typical-accidents": ["accident", "collision"],
    "loading-and-passengers": ["cargo", "passenger"],
    "accident-response": ["breakdown", "accident"],
    "route-planning": ["route", "garage"],
    "license-system": ["license", "novice"],
}


def _classify_theme(prompt: str) -> str:
    prompt_lower = prompt.lower()
    best_slug = "driver-mindset"
    best_score = 0
    for slug, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > best_score:
            best_score = score
            best_slug = slug
    return best_slug


def _normalize_answer(raw: str) -> str:
    cleaned = raw.strip().lower()
    if cleaned in ("true", "yes", "correct", "○", "o"):
        return "true"
    if cleaned in ("false", "no", "incorrect", "×", "x"):
        return "false"
    return cleaned


async def scrape_github_tsv(
    *,
    rate_limit: float = 1.0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Download and parse questions.tsv from kevincobain2000's GitHub repo.
    """
    all_questions: list[dict[str, Any]] = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            resp = await client.get(TSV_URL)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Failed to fetch TSV: {e}")
            return []

        # Parse TSV — format: question\t\tanswer\texplanation
        # The TSV has an empty column between question and answer
        reader = csv.reader(io.StringIO(resp.text), delimiter="\t")
        for row in reader:
            if len(row) < 3:
                continue

            question_text = row[0].strip()
            if len(question_text) < 10:
                continue

            # Answer is typically in column 2 (index 2)
            answer_raw = row[2].strip() if len(row) > 2 else "false"
            explanation = row[3].strip() if len(row) > 3 else ""

            # Skip image-only questions
            if question_text.startswith("img-"):
                continue

            theme_slug = _classify_theme(question_text)
            all_questions.append({
                "prompt_en": question_text,
                "answer_en": _normalize_answer(answer_raw),
                "explanation_en": explanation if explanation != "Correct" else "",
                "theme_slug": theme_slug,
                "source_url": TSV_URL,
                "license": "open-source",
                "attribution": "kevincobain2000/japan-drivers-license-practice-test-questions-english (MIT)",
                "raw_text": question_text,
            })

            if limit and len(all_questions) >= limit:
                break

        await asyncio.sleep(rate_limit)

    # Save raw output
    raw_file = RAW_DIR / "github_tsv.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(all_questions)} questions to {raw_file}")

    return all_questions


if __name__ == "__main__":
    import sys
    result = asyncio.run(scrape_github_tsv())
    print(f"Total questions scraped: {len(result)}")
    sys.exit(0)
