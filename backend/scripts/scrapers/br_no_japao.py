#!/usr/bin/env python3
"""
Scraper for BR no Japao blog (PT-language driving guides).

URL: https://brnojapao.com.br
WordPress blog — PT content.
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
RAW_DIR = PROJECT_ROOT / "data" / "raw_scrapes" / "br_no_japao"

THEME_KEYWORDS = {
    "signals": ["sinal", "sinaleiro", "seta", "indicador"],
    "intersections-and-railroad-crossings": ["cruzamento", "interseção", "ferrovia"],
    "pedestrian-protection": ["pedestre", "faixa de pedestre"],
    "blind-spots": ["ponto cego", "retrovisor"],
    "safety-checks": ["verificação", "inspeção", "segurança"],
    "parking-and-stopping": ["estacionar", "parada", "estacionamento"],
    "overtaking-and-passing": ["ultrapassar", "ultrapassagem"],
    "highway-driving": ["rodovia", "expressway", "autoestrada"],
    "adverse-conditions": ["chuva", "noite", "molhado"],
    "driver-mindset": ["confiança", "atenção", "cuidado"],
    "prohibited-actions": ["proibido", "não deve"],
    "emergency-vehicle-priority": ["emergência", "ambulância"],
    "speed-and-following-distance": ["velocidade", "distância"],
    "vehicle-maintenance": ["pneu", "óleo", "motor"],
    "signs-and-markings": ["placa", "marcação"],
    "human-factors": ["fadiga", "sono"],
    "natural-forces": ["inércia", "gravidade"],
    "typical-accidents": ["acidente", "colisão"],
    "loading-and-passengers": ["carga", "passageiro"],
    "accident-response": ["pane", "acidente"],
    "route-planning": ["rota", "garagem"],
    "license-system": ["licença", "habilitação", "cnh"],
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


async def scrape_br_no_japao(
    urls: list[str] | None = None,
    *,
    rate_limit: float = 1.0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Scrape BR no Japao blog for PT driving questions."""
    if urls is None:
        urls = [
            "https://brnojapao.com.br",
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
            questions = _parse_br_no_japao_page(soup, source_url=url, limit=limit)
            all_questions.extend(questions)

            raw_file = RAW_DIR / "brnojapao_main.json"
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(questions)} questions to {raw_file}")

            await asyncio.sleep(rate_limit)

    return all_questions


def _parse_br_no_japao_page(
    soup: BeautifulSoup, *, source_url: str, limit: int | None = None
) -> list[dict[str, Any]]:
    """Parse BR no Japao WordPress page into question dicts."""
    questions: list[dict[str, Any]] = []

    # WordPress: look for article or entry-content
    for article in soup.find_all(["article", "div"], class_=re.compile(r"entry-content|post-content", re.I)):
        text = article.get_text(strip=True)
        if len(text) < 50:
            continue

        # Look for numbered questions (1., 2., etc.) or Q&A patterns
        lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 20]

        for line in lines:
            # Remove numbering
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)
            if len(cleaned) < 20:
                continue

            theme_slug = _classify_theme_pt(cleaned)
            questions.append({
                "prompt_en": cleaned,  # Will be translated later
                "answer_en": "false",
                "explanation_en": "",
                "theme_slug": theme_slug,
                "source_url": source_url,
                "license": "rewrite-required",
                "attribution": "BR no Japão",
                "raw_text": cleaned,
            })

            if limit and len(questions) >= limit:
                break

    return questions


if __name__ == "__main__":
    import sys
    result = asyncio.run(scrape_br_no_japao())
    print(f"Total questions scraped: {len(result)}")
    sys.exit(0)
