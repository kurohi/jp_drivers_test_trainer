# Contributing Guide -- JP Drivers Test Trainer

This document covers extending the project with new themes, questions, and skill-test modules. Read the [sourcing playbook](sourcing-playbook.md) first for content-gathering rules and license requirements.

## Adding a New Theme

The 22 official exam themes are fixed by the Japanese licensing authority. Do not add root themes unless the syllabus changes. What you may need is a **sub-theme** for finer question organization.

### Steps

1. **Add i18n entries.** Open `backend/scripts/seed_themes.py` and add the new theme to the seed data array:

   ```python
   {
       "slug": "night-driving",
       "name_en": "Night Driving",
       "name_pt": "Direcao Noturna",
       "parent_slug": "adverse-conditions",  # or None for root
       "sort_order": 1,
   }
   ```

2. **Add frontend i18n strings.** If the theme name appears in UI labels, add translations in the frontend i18n resource files:

   ```json
   {
       "themes.night-driving": "Night Driving",
       "themes.night-driving_pt": "Direcao Noturna"
   }
   ```

3. **Re-seed the themes table:**

   ```bash
   cd backend
   uv run python scripts/seed_themes.py
   ```

4. **Update the sourcing playbook.** Add the new theme to the 22 Themes table in `docs/sourcing-playbook.md` so scrapers can map questions to it.

## Adding Questions

Do not hand-write questions directly into the database. Use the ingestion pipeline.

### Steps

1. **Scrape or author raw content.** Place raw JSON in `data/raw_scrapes/<source_name>/` as an array of objects:

   ```json
   {
       "prompt_en": "Drivers must yield to emergency vehicles at all times.",
       "answer_en": "true",
       "explanation_en": "Emergency vehicles have absolute priority under Japanese traffic law.",
       "theme_slug": "emergency-vehicle-priority",
       "source_url": "https://example.com/question/42",
       "license": "rewrite-required",
       "attribution": "Example Source"
   }
   ```

2. **Run the normalization pipeline:**

   ```bash
   cd backend
   uv run python scripts/normalize.py --source <source_name>
   ```

   This normalizes text, deduplicates (exact + fuzzy 85%), tags tricky patterns, translates to PT, and persists to SQLite.

3. **Review `data/manual_review_queue.jsonl`.** Near-duplicates and ambiguous questions land here. Review and keep, modify, or discard.

4. **Verify coverage:**

   ```bash
   cd backend
   uv run python scripts/normalize.py --source all
   ```

   The script prints totals: question count (target 660+), tricky ratio (target 40%+), theme coverage (target 22).

### Alternative: edit the question seed directly

For small fixes (typos, answer corrections), edit the source JSON files in `data/raw_scrapes/` and re-run `normalize.py`. The pipeline is idempotent -- it skips exact duplicates, so re-running is safe.

## Adding Skill Modules

Skill modules model closed-course maneuvers with trajectory data and SVG diagrams.

### Schema

Each module is a JSON file in `data/skill_modules/` conforming to `docs/skill_module.schema.json`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique numeric ID |
| `slug` | string | URL-safe identifier (e.g. `s-curve`) |
| `name_en` | string | English display name |
| `name_pt` | string | Portuguese display name |
| `sort_order` | integer | Display order in UI |
| `overview` | object | `{ "en": "...", "pt": "..." }` -- 200-300 word description |
| `svg_path` | string | Path to SVG diagram, e.g. `assets/skill/s-curve-diagram.svg` |
| `correct_trajectory` | object | Ideal vehicle path (keypoints + coordinate array) |
| `wrong_trajectory` | object | Common failure path with `failure_reason` (EN/PT) |
| `common_mistakes` | object | `{ "en": [...], "pt": [...] }` -- 3-5 items each |
| `checklist` | array | Sequential steps with `text` and `pass_criteria` (EN/PT) |
| `pro_tip` | object | `{ "en": "...", "pt": "..." }` -- one-sentence tip |

### Steps

1. **Create the JSON file** in `data/skill_modules/<slug>.json`.

2. **Validate against the schema:**

   ```bash
   cd backend
   uv run python scripts/validate_skill_modules.py
   ```

3. **Add the SVG diagram** to `frontend/public/assets/skill/`. Include course boundaries, correct trajectory (solid line), wrong trajectory (dashed line), and labeled keypoints matching the trajectory arrays.

4. **Seed the module:**

   ```bash
   cd backend
   uv run python scripts/seed_skill_modules.py
   ```

   Idempotent -- deletes existing records by slug and re-inserts.

5. **Verify in the UI.** Start frontend, navigate to Skill Test. New module should appear in sort order.

## Code Style

- **Backend (Python):** pytest for TDD (`uv run pytest`). Use pytest-asyncio for async tests. Follow existing repository pattern (Pydantic schemas -> services -> repositories). Format with ruff (`uv run ruff check .`).
- **Frontend (TypeScript):** TypeScript strict mode. Playwright for E2E tests (`npx playwright test`). Components use Radix UI primitives + Tailwind CSS. State via Zustand. Routing via TanStack Router.
- **Python tooling:** Use `uv` exclusively -- `uv sync` for installs, `uv run` for execution, `uv add` for dependencies. Never `pip` or `venv`.
- **JavaScript tooling:** Use `npm` -- `npm install`, `npm run dev`, `npm run build`.

## Pull Request Checklist

- [ ] New themes have both EN and PT names
- [ ] Questions include `source_url`, `license`, and `attribution`
- [ ] Skill modules validate against `docs/skill_module.schema.json`
- [ ] Backend tests pass: `cd backend && uv run pytest`
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] TypeScript clean: `cd frontend && tsc --noEmit`
- [ ] No hardcoded secrets or API keys in commits
