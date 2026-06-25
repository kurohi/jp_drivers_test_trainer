#!/usr/bin/env python3
"""
Assign downloaded leasejapan images to matching DB questions.

Manually curated mapping from scraped images to DB questions,
verified by keyword analysis of semantic overlap.

Usage:
    uv run python backend/scripts/assign_images.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "jp_drivers.sqlite"

# Manually curated mapping: (image_filename, db_question_id, confidence_note)
# Each links a leasejapan image to the best-matching existing DB question.
#
# Sources:
#   test-2: 10 image-based T/F questions about road situations
#   test-3: 10 image-based T/F questions about road situations
#   test-1: 1 image (Height-Limit) among 100 text questions
#
# Mapping verified by keyword overlap and semantic similarity analysis.
IMAGE_TO_DB: list[tuple[str, int, str]] = [
    # ---- Test 2 images ----
    ("2_1.gif", 183,
     "#183: 'parking and stopping are prohibited' — matches 'no parking or stopping' sign"),
    ("2_2.gif", 293,
     "#293: 'Drivers may change lane like this picture shown' — exact match for lane-change diagram"),
    ("2_3.gif", 500,
     "#500: 'When overtaking, if a car ahead has pulled over...' — matches 'not acceptable to pass'"),
    ("2_4.jpg", 656,
     "#656: 'When you park your car on road with a side strip...' — matches parking on roadside scenario"),
    ("2_5.jpg", 299,
     "#299: 'During a flashing amber light, vehicles may proceed...' — matches yellow blinking light"),
    ("2_6.jpg", 131,
     "#131: 'Even if the traffic signal ahead is red but the amber arrow light is shown...' — matches turn-right-on-red scenario"),
    ("2_7.jpg", 232,
     "#232: 'When there are two vehicle lanes in the same direction...' — matches 2-lane rule"),
    ("2_8.jpg", 548,
     "#548: 'Within 30 meters of pedestrian crossing...must not overtake' — matches pedestrian crossing + 30m rule"),
    ("2_9.gif", 539,
     "#539: about headlights — matches 'drive with lights on' (image shows headlight sign)"),
    ("2_10.gif", 293,
     "#293: lane change scenario — best match for 'position A to change lanes'"),

    # ---- Test 3 images ----
    ("3_1.gif", 376,
     "#376: 'This sign means you may proceed slowly after checking for safety' — matches 'proceed with caution'"),
    ("3_2.jpg", 187,
     "#187: 'On the road with this road marking, drivers must not change lanes' — matches solid white line rule"),
    ("3_3.jpg", 61,
     "#61: 'When your vehicle is in an intersection and you notice an emergency vehicle is approaching...' — proper ambulance/emergency vehicle match"),
    ("3_4.jpg", 162,
     "#162: 'When making a right turn from a one-way road...' — matches right turn at intersection"),
    ("3_5.jpg", 209,
     "#209: 'On the road with this road sign, the drivers may turn left even when the traffic signal is red' — matches turn-left-on-red"),
    ("3_6.jpg", 459,
     "#459: 'The driver must fasten the seat belt, and also passengers need to fasten their seat belts' — proper seatbelt match"),
    ("3_7.jpg", 582,
     "#582: about manual/automatic transmission — matches transmission type question"),
    ("3_8.gif", 303,
     "#303: 'The location with this sign...paying attention to pedestrians' — matches 'careful of pedestrians' sign"),
    ("3_9.jpg", 167,
     "#167: 'At an intersection where there is a Left-turn permitted sign...' — matches left-turn sound horn situation"),
    ("3_10.jpg", 972,
     "#972: about road sign — best available match for 'rules of the road' generic statement"),

    # ---- Test 1 image ----
    ("Height-Limit.jpg", 581,
     "#581: 'The height restriction of a load on a regular or large motorcycle is 2m...' — closest to height limit sign concept"),
]


def main() -> int:
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    updated = 0
    errors = 0
    for img_fname, qid, note in IMAGE_TO_DB:
        local_url = f"/static/images/questions/{img_fname}"
        row = conn.execute(
            "SELECT id, prompt_en, image_url FROM questions WHERE id = ?", (qid,)
        ).fetchone()
        if not row:
            print(f"  ERROR: Question #{qid} not found in DB")
            errors += 1
            continue

        if row[2] == local_url:
            print(f"  SKIP  #{qid} already has {local_url}")
            continue

        conn.execute(
            "UPDATE questions SET image_url = ? WHERE id = ?",
            (local_url, qid),
        )
        conn.commit()
        updated += 1
        print(f"  SET  #{qid}: {img_fname} -> \"{row[1][:60]}...\"")

    conn.close()
    print(f"\nResult: {updated} images assigned, {errors} errors")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
