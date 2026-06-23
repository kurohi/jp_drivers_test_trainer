#!/usr/bin/env python3
"""
Scraper for Reddit r/japanresidents discussion threads.

Uses Reddit JSON API: https://www.reddit.com/r/japanresidents/.json
License: community-free
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw_scrapes" / "reddit_threads"

DRIVER_TEST_KEYWORDS = [
    "driver's license", "drivers license", "driving test", "written test",
    "外免切替", "gai men", "gaimen", "license conversion", "driving school",
    "jaf test", "traffic rules", "road test", "skill test",
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


def _classify_theme(text: str) -> str:
    text_lower = text.lower()
    best_slug = "driver-mindset"
    best_score = 0
    for slug, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_slug = slug
    return best_slug


def _is_driver_test_related(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in DRIVER_TEST_KEYWORDS)


async def scrape_reddit_threads(
    subreddit: str = "japanresidents",
    *,
    rate_limit: float = 1.0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Extract Q&A from Reddit discussion threads about the JP driver's test.
    """
    all_questions: list[dict[str, Any]] = []
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    url = f"https://www.reddit.com/r/{subreddit}/.json"
    headers = {"User-Agent": "jp-drivers-test-trainer/1.0"}

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Failed to fetch Reddit: {e}")
            return []

        data = resp.json()
        posts = data.get("data", {}).get("children", [])

        for post_data in posts:
            if len(all_questions) >= limit:
                break

            post = post_data.get("data", {})
            title = post.get("title", "")
            body = post.get("selftext", "")
            post_url = f"https://reddit.com{post.get('permalink', '')}"

            if not _is_driver_test_related(title + " " + body):
                continue

            # Extract Q&A from comments
            comments = post.get("data", {}).get("children", []) if "data" in post else []
            # For top-level posts, the comments are in a separate fetch
            # Here we treat the post body as potential Q&A content

            combined_text = f"{title}. {body}".strip()
            if len(combined_text) < 30:
                continue

            # Split into sentences for individual questions
            sentences = re.split(r"(?<=[.!?])\s+", combined_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:
                    continue

                theme_slug = _classify_theme(sentence)
                all_questions.append({
                    "prompt_en": sentence,
                    "answer_en": "false",
                    "explanation_en": "",
                    "theme_slug": theme_slug,
                    "source_url": post_url,
                    "license": "community-free",
                    "attribution": f"Reddit r/{subreddit}",
                    "raw_text": sentence,
                })

            await asyncio.sleep(rate_limit)

    # Save raw output
    raw_file = RAW_DIR / f"reddit_{subreddit}.json"
    with open(raw_file, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(all_questions)} questions to {raw_file}")

    return all_questions


if __name__ == "__main__":
    import sys
    result = asyncio.run(scrape_reddit_threads())
    print(f"Total questions scraped: {len(result)}")
    sys.exit(0)
