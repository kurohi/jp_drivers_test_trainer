#!/usr/bin/env python3
"""
Scrape images from leasejapan.com and associate them with DB questions.

Extracts question+image pairs from leasejapan written test pages,
downloads images locally, and updates the DB with local image paths.

The leasejapan quiz pages use the Forminator WordPress plugin with:
  <div class="forminator-question [forminator-last]">
    <span class="forminator-legend">QUESTION TEXT</span>
    <div class="forminator-image" aria-hidden="true">
      <img src="IMAGE_URL" />
    </div>
    <label class="forminator-answer">True</label>
    <label class="forminator-answer">False</label>
  </div>

Usage:
    uv run python backend/scripts/scrape_images.py
"""
from __future__ import annotations

import asyncio
import difflib
import re
import sqlite3
import sys
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATIC_IMAGES_DIR = PROJECT_ROOT / "static" / "images" / "questions"
DB_PATH = PROJECT_ROOT / "data" / "jp_drivers.sqlite"

STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

LEASEJAPAN_URLS = [
    "https://leasejapan.com/en/license-conversion/written-test-guide/test-1/",
    "https://leasejapan.com/en/license-conversion/written-test-guide/test-2/",
    "https://leasejapan.com/en/license-conversion/written-test-guide/test-3/",
]


def extract_questions_with_images(html: str, source_url: str) -> list[dict]:
    """Parse Forminator quiz HTML and extract questions that have images.

    Returns list of dicts: {prompt_en, image_url, source_url}
    """
    pairs = []

    # Regex to match each forminator-question block (handles both
    # "forminator-question" and "forminator-question forminator-last")
    question_pattern = re.compile(
        r'<div[^>]*class="[^"]*forminator-question[^"]*"[^>]*>'
        r'.*?<span[^>]*class="forminator-legend"[^>]*>(.*?)</span>'
        r'.*?<div class="forminator-image"[^>]*>'
        r'\s*<img[^>]+src="([^"]+)"',
        re.DOTALL,
    )

    for m in question_pattern.finditer(html):
        legend_text = m.group(1).strip()
        img_url = m.group(2).strip()

        # Normalize relative URLs
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url.startswith("/"):
            img_url = "https://leasejapan.com" + img_url

        # Decode HTML entities in legend text
        legend_text = (
            legend_text
            .replace("&#8217;", "'")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&#8220;", '"')
            .replace("&#8221;", '"')
            .replace("&#8211;", "–")
            .replace("&#8230;", "…")
        )
        # Remove any remaining HTML tags
        legend_text = re.sub(r'<[^>]+>', '', legend_text).strip()

        pairs.append({
            "prompt_en": legend_text,
            "image_url": img_url,
            "source_url": source_url,
        })

    return pairs


async def download_image(client: httpx.AsyncClient, url: str, filename: str) -> Path | None:
    """Download an image to the static images directory."""
    local_path = STATIC_IMAGES_DIR / filename
    if local_path.exists():
        print(f"  Already exists: {filename}")
        return local_path

    try:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        local_path.write_bytes(resp.content)
        print(f"  Downloaded: {filename}")
        return local_path
    except Exception as e:
        print(f"  FAILED {url}: {e}")
        return None


def image_filename_from_url(url: str) -> str:
    """Extract a clean filename from an image URL."""
    basename = url.rstrip("/").split("/")[-1].split("?")[0]
    return basename or "image.jpg"


async def scrape_leasejapan() -> int:
    """Scrape all leasejapan test pages and update DB with image paths."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # ---- Phase 1: fetch pages and extract pairs ----
        all_pairs: list[dict] = []
        for url in LEASEJAPAN_URLS:
            print(f"\nFetching: {url}")
            try:
                resp = await client.get(url, timeout=30)
                resp.raise_for_status()
                pairs = extract_questions_with_images(resp.text, url)
                print(f"  Found {len(pairs)} question+image pairs")
                all_pairs.extend(pairs)
            except Exception as e:
                print(f"  FAILED to fetch {url}: {e}")

        if not all_pairs:
            print("\nNo question+image pairs found. Exiting.")
            return 0

        # ---- Phase 2: download images ----
        print(f"\nDownloading {len(all_pairs)} images...")
        tasks = [
            download_image(client, p["image_url"], image_filename_from_url(p["image_url"]))
            for p in all_pairs
        ]
        results = await asyncio.gather(*tasks)
        downloaded = sum(1 for r in results if r is not None)
        print(f"Downloaded: {downloaded}/{len(all_pairs)}")

        # ---- Phase 3: match and update DB ----
        print("\nMatching questions to database...")
        if not DB_PATH.exists():
            print(f"Database not found: {DB_PATH}")
            return downloaded

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row

        db_rows = conn.execute(
            "SELECT id, prompt_en FROM questions WHERE source_url LIKE ?",
            ("%leasejapan%",),
        ).fetchall()
        print(f"  DB has {len(db_rows)} leasejapan questions")

        updated = 0
        for pair in all_pairs:
            src_prompt = pair["prompt_en"]
            img_fname = image_filename_from_url(pair["image_url"])
            local_url = f"/static/images/questions/{img_fname}"

            # Fuzzy-match against DB questions
            best = None
            best_score = 0
            for row in db_rows:
                score = int(
                    difflib.SequenceMatcher(
                        None, src_prompt.lower(), row["prompt_en"].lower()
                    ).ratio()
                    * 100
                )
                if score > best_score:
                    best_score = score
                    best = row

            if best and best_score >= 60:
                conn.execute(
                    "UPDATE questions SET image_url = ? WHERE id = ?",
                    (local_url, best["id"]),
                )
                conn.commit()
                updated += 1
                print(f"  #{best['id']} ({best_score}%): {local_url}")
            else:
                print(f"  NO MATCH ({best_score}%): '{src_prompt[:70]}...'")

        conn.close()
        print(f"\nSummary: {downloaded} images downloaded, {updated} DB rows updated")
        return updated


def main() -> int:
    result = asyncio.run(scrape_leasejapan())
    return 0 if result > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
