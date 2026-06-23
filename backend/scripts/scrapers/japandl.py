#!/usr/bin/env python3
"""
Scraper for JapanDL.com practice exam papers.

URL pattern: https://japandl.com/en/exam/paper-{paper_id}
SPA with JS rendering — use Apify rag-web-browser or Playwright.
License: rewrite-required
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
RAW_DIR = PROJECT_ROOT / "data" / "raw_scrapes" / "japandl"

# Known paper IDs from the playbook
PAPER_IDS = [
    "paper-1775192489399-6ljeo",  # Gaimen Kirikae
    "paper-1775194229450-7704g",  # Learner's
]

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


async def scrape_japandl(
    paper_ids: list[str] | None = None,
    *,
    rate_limit: float = 1.0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Scrape JapanDL.com practice exam papers.

    Note: JapanDL is a SPA. This scraper attempts direct HTTP fetch first,
    but may need Playwright/Apify for full JS rendering.
    """
    if paper_ids is None:
        paper_ids = PAPER_IDS

    all_questions: list[dict[str, Any]] = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        for paper_id in paper_ids:
            url = f"https://japandl.com/en/exam/{paper_id}"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                print(f"Failed to fetch {url}: {e}")
                continue

            soup = BeautifulSoup(resp.text, "lxml")
            questions = _parse_japandl_page(soup, source_url=url, paper_id=paper_id, limit=limit)
            all_questions.extend(questions)

            raw_file = RAW_DIR / f"{paper_id}.json"
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(questions)} questions to {raw_file}")

            await asyncio.sleep(rate_limit)

    return all_questions


def _parse_japandl_page(
    soup: BeautifulSoup, *, source_url: str, paper_id: str, limit: int | None = None
) -> list[dict[str, Any]]:
    """Parse JapanDL page into question dicts."""
    questions: list[dict[str, Any]] = []

    # JapanDL renders questions via JS. Try to find question containers.
    # Look for div elements with question-like content
    for div in soup.find_all(["div", "section"]):
        text = div.get_text(strip=True)
        if len(text) < 50:
            continue

        # Look for T/F question patterns
        if any(indicator in text.lower() for indicator in ["true", "false", "正しい", "誤り"]):
            # Extract the question statement (first substantial paragraph)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if not lines:
                continue

            prompt = lines[0]
            if len(prompt) < 20:
                continue

            theme_slug = _classify_theme(prompt)
            questions.append({
                "prompt_en": prompt,
                "answer_en": "false",  # default, needs parsing
                "explanation_en": "",
                "theme_slug": theme_slug,
                "source_url": source_url,
                "license": "rewrite-required",
                "attribution": "JapanDL",
                "raw_text": text[:500],
            })

            if limit and len(questions) >= limit:
                break

    return questions


if __name__ == "__main__":
    import sys
    result = asyncio.run(scrape_japandl())
    print(f"Total questions scraped: {len(result)}")
    sys.exit(0)
