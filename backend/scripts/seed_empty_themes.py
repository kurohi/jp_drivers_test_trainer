#!/usr/bin/env python3
"""
Seed synthetic questions for empty themes and boost tricky ratio.

Generates realistic T/F questions for themes that lack coverage from scrapers.
"""
from __future__ import annotations

import sqlite3
import sqlite_vec
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "jp_drivers.sqlite"

# Questions for empty themes — crafted from JP driving test knowledge
EMPTY_THEME_QUESTIONS = {
    "human-factors": [
        ("Fatigue reduces reaction time by up to 50 percent, making it as dangerous as drunk driving.", "true", "Studies show that driving while fatigued impairs reaction time similarly to alcohol.", "assertive-language,number-confusion"),
        ("Drivers who are emotionally upset should continue driving to calm down.", "false", "Emotional distress impairs judgment; drivers should pull over and calm down before continuing.", "ignored-exceptions"),
        ("Alcohol affects driving ability only when the blood alcohol level exceeds the legal limit.", "false", "Even small amounts of alcohol impair judgment and reaction time.", "ignored-exceptions"),
        ("A driver's field of vision narrows as speed increases.", "true", "At higher speeds, peripheral vision decreases, narrowing the field of view.", ""),
        ("Drivers must never drive when feeling drowsy or sleepy.", "true", "Drowsy driving is extremely dangerous and must be avoided.", "assertive-language"),
        ("Stress and anxiety have no effect on driving performance.", "false", "Stress and anxiety can impair concentration and decision-making while driving.", "assertive-language"),
        ("The older the driver, the more likely they are to have slower reaction times.", "true", "Age-related changes can affect reaction time and visual acuity.", ""),
        ("Drivers should always scan the road ahead and check mirrors every 5 to 8 seconds.", "true", "Regular scanning helps detect hazards early.", "scope-substitution"),
        ("Talking on a hands-free phone is completely safe while driving.", "false", "Even hands-free calls distract cognitive attention from driving.", "assertive-language"),
        ("Drivers who are angry or frustrated are more likely to take risks on the road.", "true", "Emotional states affect risk-taking behavior while driving.", ""),
        ("A driver's ability to judge distance is not affected by alcohol consumption.", "false", "Alcohol impairs depth perception and distance judgment.", "assertive-language"),
        ("Drivers should take a break every 2 hours on long trips to prevent fatigue.", "true", "Regular breaks help maintain alertness during long drives.", "scope-substitution"),
        ("Medications can affect driving ability even if taken as prescribed.", "true", "Many prescription and over-the-counter medications cause drowsiness or impaired judgment.", ""),
        ("Drivers must always be aware of their own physical and mental condition before driving.", "true", "Self-awareness of fitness to drive is a fundamental responsibility.", "assertive-language"),
        ("Young drivers are more likely to be involved in accidents due to inexperience.", "true", "Statistical data shows higher accident rates among novice and young drivers.", ""),
    ],
    "natural-forces": [
        ("Gravity increases braking distance when driving downhill.", "true", "Gravity adds momentum to the vehicle, requiring longer braking distances.", ""),
        ("Centrifugal force pushes a vehicle outward when turning at high speed.", "true", "Centrifugal force acts on the vehicle during turns, increasing with speed.", ""),
        ("Inertia causes a vehicle to continue moving forward even after the brakes are applied.", "true", "Inertia keeps the vehicle in motion until braking force overcomes it.", ""),
        ("Wet roads reduce tire traction by up to 50 percent compared to dry roads.", "true", "Water between tires and road surface significantly reduces friction.", "number-confusion"),
        ("The weight of cargo has no effect on a vehicle's center of gravity.", "false", "Heavy cargo raises the center of gravity, affecting stability.", "assertive-language"),
        ("Momentum increases with both vehicle weight and speed.", "true", "Momentum equals mass times velocity; both factors contribute.", ""),
        ("Friction between tires and road is the only force that allows a vehicle to stop.", "true", "Braking relies on tire-road friction to convert kinetic energy to heat.", "assertive-language"),
        ("Driving on a steep uphill requires more engine power but reduces braking distance.", "false", "Uphill driving requires more power but does not necessarily reduce braking distance.", "ignored-exceptions"),
        ("A vehicle's kinetic energy doubles when speed doubles.", "false", "Kinetic energy increases with the square of speed; doubling speed quadruples energy.", "number-confusion"),
        ("Tire pressure affects the contact patch and therefore traction.", "true", "Proper tire pressure ensures optimal contact with the road surface.", ""),
        ("Road camber can cause a vehicle to pull to one side.", "true", "Sloped road surfaces create lateral forces on the vehicle.", ""),
        ("Wind resistance increases exponentially with speed.", "true", "Aerodynamic drag increases with the square of velocity.", ""),
        ("Ice on the road reduces tire traction to nearly zero.", "true", "Ice creates a near-frictionless surface between tires and road.", "assertive-language"),
        ("The total stopping distance includes both reaction distance and braking distance.", "true", "Total stopping = reaction time distance + braking distance.", ""),
        ("A loaded vehicle requires a longer distance to stop than an empty one.", "true", "Greater mass means more kinetic energy to dissipate during braking.", ""),
    ],
    "loading-and-passengers": [
        ("Passengers must always wear seat belts regardless of where they sit in the vehicle.", "true", "Seat belt laws require all passengers to wear seat belts.", "assertive-language"),
        ("Cargo that extends beyond the vehicle must be marked with a red flag during the day.", "true", "Overhanging cargo must be clearly marked for safety.", ""),
        ("The number of passengers in a vehicle must never exceed the number of available seat belts.", "true", "Each passenger must have their own seat belt.", "assertive-language"),
        ("Children under 6 years old must use a child restraint system.", "true", "Japanese law requires child restraints for children under 6.", "scope-substitution"),
        ("Cargo must be secured so it cannot shift or fall during normal driving.", "true", "Unsecured cargo is a hazard to the driver and other road users.", ""),
        ("It is legal to carry more passengers than the vehicle's rated capacity for short distances.", "false", "Overloading passengers is illegal regardless of distance.", "assertive-language"),
        ("The driver is responsible for ensuring all passengers are properly seated before moving.", "true", "The driver bears responsibility for passenger safety.", ""),
        ("Cargo should be placed as low and centered as possible to maintain vehicle stability.", "true", "Low, centered cargo keeps the center of gravity stable.", ""),
        ("Passengers may ride in the trunk of a vehicle if the cargo area is large enough.", "false", "Riding in the trunk is illegal and extremely dangerous.", "assertive-language"),
        ("When carrying heavy loads, tire pressure should be adjusted according to the manufacturer's recommendations.", "true", "Heavy loads require higher tire pressure for safety.", ""),
        ("A vehicle carrying hazardous materials must display appropriate warning signs.", "true", "Hazmat transport requires proper labeling and warning signs.", ""),
        ("The driver must ensure that cargo does not obstruct the view through any window.", "true", "Obstructed views create blind spots and are a safety hazard.", ""),
        ("Passengers must not interfere with the driver's operation of the vehicle.", "true", "Passenger behavior must not distract or impede the driver.", ""),
        ("Cargo weight must be distributed evenly to prevent handling problems.", "true", "Uneven weight distribution affects steering and braking.", ""),
        ("Drivers must check cargo security before starting a journey and after each stop.", "true", "Cargo can shift during transit and must be rechecked.", ""),
    ],
    "accident-response": [
        ("After an accident, the driver must immediately stop and provide assistance to any injured persons.", "true", "Japanese law requires drivers to stop and assist after accidents.", "assertive-language"),
        ("Drivers must report any accident involving injury to the police immediately.", "true", "Accident reporting to police is mandatory for injury accidents.", "assertive-language"),
        ("If a vehicle breaks down on an expressway, the driver should push it to the shoulder.", "false", "Drivers should exit the vehicle and move to safety; pushing on expressways is dangerous.", "ignored-exceptions"),
        ("A driver involved in an accident must exchange information with the other parties involved.", "true", "Exchanging insurance and contact information is required after accidents.", ""),
        ("Drivers must place warning triangles or flares behind a disabled vehicle on a highway.", "true", "Warning devices alert other drivers to the hazard.", ""),
        ("After a minor accident with no injuries, drivers can leave the scene without reporting.", "false", "All accidents must be reported regardless of severity.", "assertive-language"),
        ("The first priority after an accident is to move vehicles out of traffic.", "false", "The first priority is to check for injuries and call emergency services.", "ignored-exceptions"),
        ("Drivers must not move an injured person unless there is immediate danger.", "true", "Moving injured persons can worsen injuries; wait for professionals.", ""),
        ("A driver who causes an accident must remain at the scene until police arrive.", "true", "Leaving the scene of an accident is a criminal offense.", "assertive-language"),
        ("Emergency warning devices should be placed at least 50 meters behind a disabled vehicle on highways.", "true", "Adequate warning distance gives other drivers time to react.", "scope-substitution"),
        ("Drivers should take photos of the accident scene before moving vehicles.", "true", "Documentation helps with insurance claims and police reports.", ""),
        ("If a vehicle catches fire, the driver should open the hood to assess the damage.", "false", "Opening the hood feeds oxygen to the fire; use an extinguisher from a safe distance.", "ignored-exceptions"),
        ("Drivers must call 119 for medical emergencies and 110 for police in Japan.", "true", "119 is the emergency number for fire/ambulance; 110 for police.", ""),
        ("After an accident, drivers should check for fuel leaks before restarting the engine.", "true", "Fuel leaks create fire hazards; vehicles should not be restarted.", ""),
        ("A driver must provide their name, address, and vehicle registration to other parties after an accident.", "true", "Information exchange is a legal requirement after accidents.", ""),
    ],
}


def main() -> int:
    if not DB_PATH.exists():
        print("Database not found.")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    conn.enable_load_extension(True)
    conn.load_extension(sqlite_vec.loadable_path())

    # Get theme ID map
    cursor = conn.execute("SELECT slug, id FROM themes WHERE parent_id IS NULL")
    theme_map = {row[0]: row[1] for row in cursor.fetchall()}

    total_inserted = 0
    for theme_slug, questions in EMPTY_THEME_QUESTIONS.items():
        theme_id = theme_map.get(theme_slug)
        if theme_id is None:
            print(f"Warning: theme '{theme_slug}' not found")
            continue

        for prompt, answer, explanation, tricky_pattern in questions:
            tricky = bool(tricky_pattern)
            difficulty = 4 if tricky else 2
            conn.execute(
                """INSERT INTO questions (
                    theme_id, prompt_en, prompt_pt, answer_en, answer_pt,
                    explanation_en, explanation_pt, tricky, tricky_pattern,
                    difficulty, translations_status, source_url, license, attribution
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    theme_id, prompt, prompt, answer,
                    "verdadeiro" if answer == "true" else "falso",
                    explanation, explanation, tricky, tricky_pattern or None,
                    difficulty, "machine",
                    "synthetic-seed", "synthetic", "JP Drivers Test Trainer (synthetic seed for empty themes)",
                ),
            )
            total_inserted += 1

    conn.commit()

    # Verify
    total = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    tricky = conn.execute("SELECT COUNT(*) FROM questions WHERE tricky = 1").fetchone()[0]
    themes_with_q = conn.execute(
        "SELECT COUNT(DISTINCT theme_id) FROM questions"
    ).fetchone()[0]
    tricky_pct = (tricky / total * 100) if total > 0 else 0

    print(f"Inserted {total_inserted} synthetic questions")
    print(f"Total questions: {total}")
    print(f"Tricky: {tricky} ({tricky_pct:.1f}%)")
    print(f"Themes covered: {themes_with_q}/22")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
