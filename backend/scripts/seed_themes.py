#!/usr/bin/env python3
"""
Seed the 22 official driver-test theme domains into the themes table.

Slugs are the authoritative identifier; names are provided in both EN and PT.
Run after apply_migrations.py:
    uv run python scripts/seed_themes.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "jp_drivers.sqlite"

# The 22 official driver-test subject domains (exact slugs as specified).
ROOT_THEMES = [
    {
        "slug": "driver-mindset",
        "name_en": "Driver Mindset",
        "name_pt": "Mentalidade do Motorista",
    },
    {
        "slug": "signals",
        "name_en": "Signals",
        "name_pt": "Sinalização de Trânsito",
    },
    {
        "slug": "signs-and-markings",
        "name_en": "Signs & Markings",
        "name_pt": "Placas e Marcações",
    },
    {
        "slug": "prohibited-actions",
        "name_en": "Prohibited Actions",
        "name_pt": "Ações Proibidas",
    },
    {
        "slug": "emergency-vehicle-priority",
        "name_en": "Emergency Vehicle Priority",
        "name_pt": "Prioridade de Veículos de Emergência",
    },
    {
        "slug": "intersections-and-railroad-crossings",
        "name_en": "Intersections & Railroad Crossings",
        "name_pt": "Interseções e Passagens de Nível",
    },
    {
        "slug": "pedestrian-protection",
        "name_en": "Pedestrian Protection",
        "name_pt": "Proteção de Pedestres",
    },
    {
        "slug": "safety-checks",
        "name_en": "Safety Checks",
        "name_pt": "Verificações de Segurança",
    },
    {
        "slug": "overtaking-and-passing",
        "name_en": "Overtaking & Passing",
        "name_pt": "Ultrapassagem e Passagem",
    },
    {
        "slug": "license-system",
        "name_en": "License System",
        "name_pt": "Sistema de Pontos da CNH",
    },
    {
        "slug": "blind-spots",
        "name_en": "Blind Spots",
        "name_pt": "Pontos Cegos",
    },
    {
        "slug": "human-factors",
        "name_en": "Human Factors",
        "name_pt": "Fatores Humanos",
    },
    {
        "slug": "natural-forces",
        "name_en": "Natural Forces",
        "name_pt": "Forças Naturais",
    },
    {
        "slug": "adverse-conditions",
        "name_en": "Adverse Conditions",
        "name_pt": "Condições Adversas",
    },
    {
        "slug": "typical-accidents",
        "name_en": "Typical Accidents",
        "name_pt": "Acidentes Típicos",
    },
    {
        "slug": "vehicle-maintenance",
        "name_en": "Vehicle Maintenance",
        "name_pt": "Manutenção do Veículo",
    },
    {
        "slug": "parking-and-stopping",
        "name_en": "Parking & Stopping",
        "name_pt": "Estacionamento e Parada",
    },
    {
        "slug": "loading-and-passengers",
        "name_en": "Loading & Passengers",
        "name_pt": "Carga e Passageiros",
    },
    {
        "slug": "accident-response",
        "name_en": "Accident Response",
        "name_pt": "Resposta a Acidentes",
    },
    {
        "slug": "highway-driving",
        "name_en": "Highway Driving",
        "name_pt": "Direção em Rodovias",
    },
    {
        "slug": "route-planning",
        "name_en": "Route Planning",
        "name_pt": "Planejamento de Rota",
    },
    {
        "slug": "speed-and-following-distance",
        "name_en": "Speed & Following Distance",
        "name_pt": "Velocidade e Distância",
    },
]


def main() -> int:
    if not DB_PATH.exists():
        print("Database not found. Run apply_migrations.py first.")
        return 1

    import sqlite_vec

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())

    for idx, theme in enumerate(ROOT_THEMES, start=1):
        conn.execute(
            """
            INSERT OR IGNORE INTO themes (slug, name_en, name_pt, sort_order)
            VALUES (?, ?, ?, ?)
            """,
            (theme["slug"], theme["name_en"], theme["name_pt"], idx),
        )

    conn.commit()

    # Verify
    cur = conn.execute(
        "SELECT COUNT(*) FROM themes WHERE parent_id IS NULL"
    )
    count = cur.fetchone()[0]
    print(f"Root themes in DB: {count}")

    conn.close()
    print("Seed completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
