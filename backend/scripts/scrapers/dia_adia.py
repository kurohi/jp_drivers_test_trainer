#!/usr/bin/env python3
"""
Scraper for DIA A DIA news blog (PT-language driving content).

URL: https://diaadia.news
WordPress-style blog.
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
RAW_DIR = PROJECT_ROOT / "data" / "raw_scrapes" / "dia_adia"

THEME_KEYWORDS = {
    "signals": ["sinal", "sinaleiro", "seta"],
    "intersections-and-railroad-crossings": ["cruzamento", "interseção"],
    "pedestrian-protection": ["pedestre", "faixa"],
    "blind-spots": ["ponto cego"],
    "safety-checks": ["verificação", "segurança"],
    "parking-and-stopping": ["estacionar", "parada"],
    "overtaking-and-passing": ["ultrapassar"],
    "highway-driving": ["rodovia", "autoestrada"],
    "adverse-conditions": ["chuva", "noite"],
    "driver-mindset": ["atenção", "cuidado"],
    "prohibited-actions": ["proibido"],
    "emergency-vehicle-priority": ["emergência"],
    "speed-and-following-distance": ["velocidade", "distância"],
    "vehicle-maintenance": ["pneu", "óleo"],
    "signs-and-markings": ["placa"],
    "human-factors": ["fadiga"],
    "natural-forces": ["inércia"],
    "typical-accidents": ["acidente"],
    "loading-and-passengers": ["carga", "passageiro"],
    "accident-response": ["pane"],
    "route-planning": ["rota"],
    "license-system": ["habilitação"],
}


def _classify_theme_pt(prompt: str) -> str:
    prompt_lower = prompt.lower()
    best_slug = "driver-mindset"
    best_score = 0
    for slug, keywords in THEME_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > best_score:
            best_score = score
            best_slug = slug
    return best_slug


async def scrape_dia_adia(
    urls: list[str] | None = None,
    *,
    rate_limit: float = 1.0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Scrape DIA A DIA blog for PT driving content."""
    if urls is None:
        urls = ["https://diaadia.news"]

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
            questions = _parse_dia_adia_page(soup, source_url=url, limit=limit)
            all_questions.extend(questions)

            raw_file = RAW_DIR / "diaadia_main.json"
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(questions)} questions to {raw_file}")

            await asyncio.sleep(rate_limit)

    return all_questions


def _parse_dia_adia_page(
    soup: BeautifulSoup, *, source_url: str, limit: int | None = None
) -> list[dict[str, Any]]:
    """Parse DIA A DIA page into question dicts."""
    questions: list[dict[str, Any]] = []

    for article in soup.find_all(["article", "div"], class_=re.compile(r"entry|content|post", re.I)):
        text = article.get_text(strip=True)
        if len(text) < 50:
            continue

        lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 20]
        for line in lines:
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)
            if len(cleaned) < 20:
                continue

            theme_slug = _classify_theme_pt(cleaned)
            questions.append({
                "prompt_en": cleaned,
                "answer_en": "false",
                "explanation_en": "",
                "theme_slug": theme_slug,
                "source_url": source_url,
                "license": "rewrite-required",
                "attribution": "DIA A DIA",
                "raw_text": cleaned,
            })

            if limit and len(questions) >= limit:
                break

    return questions


if __name__ == "__main__":
    import sys
    result = asyncio.run(scrape_dia_adia())
    print(f"Total questions scraped: {len(result)}")
    sys.exit(0)
