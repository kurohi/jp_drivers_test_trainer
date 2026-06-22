#!/usr/bin/env python3
"""
Scraper template for JP Driver's Test Trainer content ingestion.

T14 fills this with actual scraper implementations for each free source
listed in docs/sourcing-playbook.md.

Each scraper function should:
1. Fetch the source URL (httpx, Playwright, or Apify)
2. Parse the HTML/PDF/text into ParsedQuestion objects
3. Return a list of ParsedQuestion dicts
4. Write any ambiguous items to data/manual_review_queue.jsonl

Usage:
    uv run python scripts/scrape_template.py --source lease-japan
    uv run python scripts/scrape_template.py --source japandl
    uv run python scripts/scrape_template.py --source github-kevincobain
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent
REVIEW_QUEUE_PATH = PROJECT_ROOT / "data" / "manual_review_queue.jsonl"

# The 22 official theme slugs (from seed_themes.py)
THEME_SLUGS = {
    "driver-mindset", "signals", "signs-and-markings", "prohibited-actions",
    "emergency-vehicle-priority", "intersections-and-railroad-crossings",
    "pedestrian-protection", "safety-checks", "overtaking-and-passing",
    "license-system", "blind-spots", "human-factors", "natural-forces",
    "adverse-conditions", "typical-accidents", "vehicle-maintenance",
    "parking-and-stopping", "loading-and-passengers", "accident-response",
    "highway-driving", "route-planning", "speed-and-following-distance",
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


def normalize_answer(raw: str) -> str:
    """Normalize answer values to 'true' or 'false'."""
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


# ---------------------------------------------------------------------------
# Scraper stubs — T14 fills these with actual implementations
# ---------------------------------------------------------------------------

def scrape_lease_japan(url: str, *, limit: int | None = None) -> list[dict[str, Any]]:
    """
    Scrape Lease Japan written test pages (Test 1, 2, 3).

    URL pattern: https://leasejapan.com/en/license-conversion/written-test-guide/test-{N}/
    Returns list of ParsedQuestion dicts.
    """
    # TODO: Implement with httpx + BeautifulSoup
    # 1. Fetch URL
    # 2. Parse HTML — each question is a statement + True/False + Reason
    # 3. Map to ParsedQuestion schema
    # 4. Run detect_tricky() on each prompt
    raise NotImplementedError("T14: implement Lease Japan scraper")


def scrape_japandl(paper_url: str, *, limit: int | None = None) -> list[dict[str, Any]]:
    """
    Scrape JapanDL.com practice exam papers.

    URL pattern: https://japandl.com/en/exam/paper-{paper_id}
    Requires JS rendering (Playwright or Apify).
    """
    # TODO: Implement with Playwright or Apify rag-web-browser
    raise NotImplementedError("T14: implement JapanDL scraper")


def scrape_github_tsv() -> list[dict[str, Any]]:
    """
    Download and parse questions.tsv from kevincobain2000's GitHub repo.

    URL: https://raw.githubusercontent.com/kevincobain2000/japan-drivers-license-practice-test-questions-english/master/questions.tsv
    MIT-licensed — best license in inventory.
    """
    # TODO: Implement with httpx + csv/tsv parser
    raise NotImplementedError("T14: implement GitHub TSV scraper")


def scrape_reddit_threads(subreddit: str = "japanresidents", *, limit: int = 20) -> list[dict[str, Any]]:
    """
    Extract Q&A from Reddit discussion threads about the JP driver's test.

    Uses Reddit JSON API: https://www.reddit.com/r/{subreddit}/.json
    """
    # TODO: Implement with httpx + Reddit JSON API
    raise NotImplementedError("T14: implement Reddit scraper")


def scrape_npa_pdfs(urls: list[str]) -> list[dict[str, Any]]:
    """
    Parse NPA English-language PDFs from prefecture websites.

    Requires pypdf or pdfplumber.
    """
    # TODO: Implement with pypdf/pdfplumber
    raise NotImplementedError("T14: implement NPA PDF scraper")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="JP Drivers Test content scraper")
    parser.add_argument(
        "--source",
        choices=["lease-japan", "japandl", "github-kevincobain", "reddit", "npa-pdfs"],
        required=True,
        help="Which source to scrape",
    )
    parser.add_argument("--url", default="", help="Source URL (if applicable)")
    parser.add_argument("--limit", type=int, default=None, help="Max questions to fetch")
    args = parser.parse_args()

    scrapers = {
        "lease-japan": lambda: scrape_lease_japan(args.url, limit=args.limit),
        "japandl": lambda: scrape_japandl(args.url, limit=args.limit),
        "github-kevincobain": scrape_github_tsv,
        "reddit": scrape_reddit_threads,
        "npa-pdfs": lambda: scrape_npa_pdfs([args.url] if args.url else []),
    }

    try:
        questions = scrapers[args.source]()
        print(f"Scraped {len(questions)} questions from {args.source}")
        return 0
    except NotImplementedError as e:
        print(f"TODO: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
