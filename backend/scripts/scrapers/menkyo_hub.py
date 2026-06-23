#!/usr/bin/env python3
"""
Scraper for MenkyoHub community Q&A.

URL: https://menkyohub.com
Forum structure — community-contributed Q&A.
License: community-free
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw_scrapes" / "menkyo_hub"

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


async def scrape_menkyo_hub(
    urls: list[str] | None = None,
    *,
    rate_limit: float = 1.0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Scrape MenkyoHub community Q&A pages."""
    if urls is None:
        urls = ["https://menkyohub.com"]

    all_questions: list[dict[str, Any]] = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                print(f"Failed to fetch {url}: {e}")
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            questions = _parse_menkyo_hub_page(soup, source_url=url, limit=limit)
            all_questions.extend(questions)

            raw_file = RAW_DIR / "menkyohub_main.json"
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(questions)} questions to {raw_file}")

            await asyncio.sleep(rate_limit)

    return all_questions


def _parse_menkyo_hub_page(
    soup: BeautifulSoup, *, source_url: str, limit: int | None = None
) -> list[dict[str, Any]]:
    """Parse MenkyoHub forum page into question dicts."""
    questions: list[dict[str, Any]] = []

    # Look for article/post elements
    for article in soup.find_all(["article", "div"], class_=re.compile(r"post|question|qa|thread", re.I)):
        text = article.get_text(strip=True)
        if len(text) < 50:
            continue

        # Extract Q&A pairs
        lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 20]
        if len(lines) < 2:
            continue

        prompt = lines[0]
        # Look for answer indicators
        answer = "false"
        explanation = ""
        for line in lines[1:]:
            if any(w in line.lower() for w in ["true", "false", "correct", "wrong", "answer"]):
                answer = "true" if any(w in line.lower() for w in ["true", "correct"]) else "false"
                explanation = line
                break

        theme_slug = _classify_theme(prompt)
        questions.append({
            "prompt_en": prompt,
            "answer_en": answer,
            "explanation_en": explanation,
            "theme_slug": theme_slug,
            "source_url": source_url,
            "license": "community-free",
            "attribution": "MenkyoHub Community",
            "raw_text": text[:500],
        })

        if limit and len(questions) >= limit:
            break

    return questions


if __name__ == "__main__":
    import sys
    result = asyncio.run(scrape_menkyo_hub())
    print(f"Total questions scraped: {len(result)}")
    sys.exit(0)
