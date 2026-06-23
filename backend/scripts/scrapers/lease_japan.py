#!/usr/bin/env python3
"""
Scraper for Lease Japan written test pages (Test 1, 2, 3).

URL pattern: https://leasejapan.com/en/license-conversion/written-test-guide/test-{N}/
Static HTML — 50 T/F questions per page with reasons.
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
RAW_DIR = PROJECT_ROOT / "data" / "raw_scrapes" / "lease_japan"

# Theme mapping based on question content keywords
THEME_KEYWORDS = {
    "signals": ["signal", "hand signal", "turn signal", "indicator", "arrow signal"],
    "intersections-and-railroad-crossings": ["intersection", "railroad", "crossing", "right turn", "left turn"],
    "pedestrian-protection": ["pedestrian", "crosswalk", "crossing"],
    "blind-spots": ["blind spot", "mirror", "rearview"],
    "safety-checks": ["inspection", "check", "daily check", "brake", "oil"],
    "parking-and-stopping": ["park", "stop", "parking"],
    "overtaking-and-passing": ["overtak", "passing", "pass the vehicle"],
    "highway-driving": ["expressway", "highway", "national expressway"],
    "adverse-conditions": ["rain", "night", "fatigue", "drowsy", "hydroplaning"],
    "driver-mindset": ["confidence", "mindful", "considerate", "caution"],
    "prohibited-actions": ["prohibited", "must not", "forbidden", "not allowed"],
    "emergency-vehicle-priority": ["emergency vehicle", "ambulance", "fire truck"],
    "speed-and-following-distance": ["following distance", "speed", "braking distance"],
    "vehicle-maintenance": ["tire", "engine oil", "coolant", "mechanical failure"],
    "signs-and-markings": ["sign", "marking", "pavement", "centerline", "solid"],
    "human-factors": ["fatigue", "drowsy", "vision", "reaction time"],
    "natural-forces": ["inertia", "centrifugal", "gravity", "steep"],
    "typical-accidents": ["accident", "collision", "crash"],
    "loading-and-passengers": ["cargo", "passenger", "load", "moped"],
    "accident-response": ["breakdown", "accident", "emergency", "warning"],
    "route-planning": ["route", "garage", "planning"],
    "license-system": ["novice driver", "license", "inspection sticker"],
}


def _classify_theme(prompt: str) -> str:
    """Map a question prompt to a theme slug based on keyword matching."""
    prompt_lower = prompt.lower()
    best_slug = "driver-mindset"  # default
    best_score = 0
    for slug, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > best_score:
            best_score = score
            best_slug = slug
    return best_slug


def _normalize_answer(raw: str) -> str:
    """Normalize True/False to 'true'/'false'."""
    cleaned = raw.strip().lower()
    if cleaned in ("true", "yes", "correct", "○", "o"):
        return "true"
    if cleaned in ("false", "no", "incorrect", "×", "x"):
        return "false"
    return cleaned


async def scrape_lease_japan(
    urls: list[str] | None = None,
    *,
    rate_limit: float = 1.0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Scrape Lease Japan written test pages.

    Args:
        urls: List of test URLs. Defaults to Tests 1-3.
        rate_limit: Seconds between requests.
        limit: Max questions per URL (for testing).

    Returns:
        List of ParsedQuestion dicts.
    """
    if urls is None:
        urls = [
            "https://leasejapan.com/en/license-conversion/written-test-guide/test-1/",
            "https://leasejapan.com/en/license-conversion/written-test-guide/test-2/",
            "https://leasejapan.com/en/license-conversion/written-test-guide/test-3/",
        ]

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
            questions = _parse_lease_japan_page(soup, source_url=url, limit=limit)
            all_questions.extend(questions)

            # Save raw output
            source_name = url.rstrip("/").split("/")[-1]
            raw_file = RAW_DIR / f"{source_name}.json"
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(questions)} questions to {raw_file}")

            await asyncio.sleep(rate_limit)

    return all_questions


def _parse_lease_japan_page(
    soup: BeautifulSoup, *, source_url: str, limit: int | None = None
) -> list[dict[str, Any]]:
    """Parse a Lease Japan test page into question dicts."""
    questions: list[dict[str, Any]] = []

    # Strategy: find all paragraphs, group by question pattern
    # Only use <p> elements to avoid catching parent divs with concatenated text
    paragraphs = soup.find_all("p")
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        text = p.get_text(strip=True)

        # Skip nav, footer, menu items
        if not text or len(text) < 20:
            i += 1
            continue

        # Skip page markers like "Page 1 of 10"
        if re.match(r"Page \d+ of \d+", text):
            i += 1
            continue

        # Skip if it's a reason paragraph (belongs to previous question)
        if text.startswith("Reason:"):
            i += 1
            continue

        # Skip navigation/footer content
        if any(skip in text.lower() for skip in [
            "written test practice", "take practice test", "testing resources",
            "lease japan", "about us", "follow us", "language", "our brands",
            "search site", "skip to", "start quiz", "ready to send",
            "written test guide", "guide to japanese", "driving test guide",
            "based on the given images",
        ]):
            i += 1
            continue

        # This might be a question statement
        # Look for the reason in subsequent paragraphs (Test 1 format)
        # OR just use the statement as-is (Test 2/3 image-based format)
        reason_text = ""
        answer_text = ""
        j = i + 1
        while j < len(paragraphs) and j < i + 5:
            next_p = paragraphs[j]
            next_text = next_p.get_text(strip=True)
            if next_text.startswith("Reason:"):
                reason_text = next_text.replace("Reason:", "").strip()
                # Look for True/False in siblings of the reason paragraph
                for sibling in next_p.find_next_siblings(["span", "p", "label"]):
                    sib_text = sibling.get_text(strip=True).lower()
                    if sib_text in ("true", "false"):
                        answer_text = sib_text
                        break
                break
            j += 1

        # For image-based questions (Test 2/3), look for True/False after the statement
        if not reason_text:
            # Check if next paragraphs contain True/False
            for j in range(i + 1, min(i + 4, len(paragraphs))):
                next_text = paragraphs[j].get_text(strip=True).lower()
                if next_text in ("true", "false"):
                    answer_text = next_text
                    break

        # Only accept as a question if it's long enough
        if len(text) >= 20:
            theme_slug = _classify_theme(text)
            questions.append({
                "prompt_en": text,
                "answer_en": _normalize_answer(answer_text or "false"),
                "explanation_en": reason_text,
                "theme_slug": theme_slug,
                "source_url": source_url,
                "license": "rewrite-required",
                "attribution": "Lease Japan",
                "raw_text": text,
            })

            if limit and len(questions) >= limit:
                break

        i += 1

    return questions


if __name__ == "__main__":
    import sys
    result = asyncio.run(scrape_lease_japan())
    print(f"Total questions scraped: {len(result)}")
    sys.exit(0)
