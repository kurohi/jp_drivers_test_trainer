# JP Drivers Test Trainer · 外免切替 学習アプリ

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![Ollama](https://img.shields.io/badge/Ollama-Local_AI-6B46C1?logo=ollama&logoColor=white)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![sqlite-vec](https://img.shields.io/badge/sqlite--vec-0.1.9-003B57?logo=sqlite&logoColor=white)](https://github.com/asg017/sqlite-vec)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **外免切替 (gaimen kirikae)** — Prepare for the Japanese driver's license written exam (Gaimen Kirikae) and closed-course practical skill test. Bilingual English & Portuguese. 100% offline, local AI, no paid subscriptions.

A bilingual (EN/PT) study and practice tool for anyone converting a foreign driver's license to a Japanese one. Covers the **50-question written test** (true/false, 30-minute limit, 90% pass threshold) and the **closed-course skill test** (S-curve, crank, parallel parking, hill start, and more). Uses [Ollama](https://ollama.com) for zero-cost local AI — no API keys, no subscriptions, no data leaves your machine.

### Keywords

`外免切替` `gaimen kirikae` `Japanese driver's license` `運転免許` `Japanese driving test` `written exam practice` `driving school` `免許取得` `study app` `RAG` `Ollama` `FastAPI` `React` `SQLite` `sqlite-vec` `local AI` `LLM` `offline-first`

## Features

- **Study by theme** -- Browse 1081+ true/false questions across all 22 official exam themes with bilingual EN/PT prompts
- **Mock test (50Q / 30 min / 90% pass)** -- Timed full-length exam simulation matching the real 外免 written test format
- **RAG teacher** -- Ask AI-powered questions about any Japanese traffic rule or scenario; answers grounded in the local question database via sqlite-vec semantic search + Ollama
- **Skill walkthrough** -- Closed-course maneuver diagrams (S-curve, crank, parallel parking, hill start, railroad crossing, sudden stop, pedestrian crossing, general driving) with trajectory paths, checklist, and common mistakes
- **Study plan** -- Track progress per theme, identify weak areas, and get recommended next-study suggestions
- **EN / PT toggle** -- Switch between English and Portuguese at any point; translation status is tracked per question

## Architecture

```mermaid
flowchart LR
  Browser["Browser<br/>localhost:5173"]
  Vite["Vite Dev Server<br/>React 19 + TanStack Router<br/>Zustand + i18next"]
  FastAPI["FastAPI Backend<br/>localhost:8000"]
  SQLite[("SQLite<br/>jp_drivers.sqlite<br/>+ sqlite-vec")]
  Ollama[("Ollama<br/>localhost:11434<br/>gemma4-256k<br/>nomic-embed-text")]

  Browser -->|"/api/*"| Vite
  Vite -->|proxy /api| FastAPI
  FastAPI --> SQLite
  FastAPI -->|embeddings & chat| Ollama
```

## Quick Start

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.13+ | Required for backend |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | latest | Python package manager — `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 18+ | Required for frontend |
| npm | bundled with Node | Frontend dependency manager |
| [Ollama](https://ollama.com/download) | latest | Local LLM runtime — `curl -fsSL https://ollama.com/install.sh \| sh` |
| Git LFS | optional | If the repo contains large skill-module SVGs |

### One-shot Setup

Run these from the **project root** (`jp_drivers_test_trainer/`):

```bash
# 1. Backend dependencies
cd backend && uv sync && cd ..

# 2. Frontend dependencies
cd frontend && npm install && cd ..

# 3. Pull Ollama models
ollama pull gemma4-256k
ollama pull nomic-embed-text

# 4. Create database and seed all content
cd backend
uv run python scripts/apply_migrations.py   # creates tables
uv run python scripts/seed_themes.py         # 22 exam themes
# Normalize & translate questions (requires Ollama):
uv run python scripts/normalize.py
# Build RAG embeddings (requires Ollama):
uv run python scripts/ingest.py
uv run python scripts/seed_skill_modules.py   # 8 skill modules
cd ..
```

> **Note:** Steps marked "requires Ollama" can be skipped if Ollama isn't available yet — the app will still start, but RAG teacher and translations will be limited.

### Running

Open **two terminals**:

#### Terminal 1 — Backend
```bash
cd backend
uv run uvicorn src.main:app --reload
```
Starts on `http://localhost:8000`. If port 8000 is occupied, use `--port 8001` and update the frontend proxy (see Troubleshooting).

#### Terminal 2 — Frontend
```bash
cd frontend
npm run dev
```
Opens at `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend.

### Verify It Works

```bash
curl -s http://localhost:8000/api/themes/ | python3 -m json.tool | head -5
# Should show array of themes
```

## Tests

```bash
# Backend unit + integration tests
cd backend && uv run pytest

# Frontend type-check
cd frontend && npx tsc --noEmit

# End-to-end (Playwright) — standalone mock mode (no backend needed)
cd frontend && VITE_API_MOCK=true npx playwright test

# E2E against live backend
cd frontend && LIVE_E2E=true npx playwright test
```

## Development Modes

| Mode | Command | Backend Required? |
|------|---------|-------------------|
| Full stack | `npm run dev` (frontend) + `uvicorn` (backend) | Yes |
| Frontend-only (mock API) | `VITE_API_MOCK=true npm run dev` | No |
| E2E tests (mock) | `VITE_API_MOCK=true npx playwright test` | No |
| E2E tests (live) | `LIVE_E2E=true npx playwright test` | Yes |
| Production build | `npm run build` then serve `dist/` | No |

## Troubleshooting

### Port Conflicts

| Problem | Likely Cause | Fix |
|---------|-------|-------------|
| `Port 8000 already in use` | Another service on 8000 | `lsof -i :8000` to find it, then either kill it or start backend on 8001: `uv run uvicorn src.main:app --reload --port 8001` |
| Frontend can't reach backend | Vite proxy port mismatch | Set `VITE_API_BASE_URL` to match: `VITE_API_BASE_URL=http://localhost:8001 npm run dev` |

### Database

| Problem | Likely Cause | Fix |
|---------|-------|-------------|
| `no such table` on startup | DB not created | Run `uv run python scripts/apply_migrations.py` from `backend/` |
| `AttributeError: enable_load_extension` in logs | sqlite-vec extension loading | The aiosqlite driver needs the `run_async` path — already handled in `src/db.py`. Ensure `aiosqlite >= 0.20`. |
| `No module named 'models'` on startup | PYTHONPATH missing | All imports now use `from src.` prefix — no PYTHONPATH needed. If you see this, run `uv sync` to update dependencies. |
| DB inconsistency (scripts write to wrong file) | Two DB copies | `scripts/*.py` write to `backend/data/` but the backend reads from `data/` (project root). Copy the file: `cp backend/data/jp_drivers.sqlite data/jp_drivers.sqlite` |

### Ollama

| Problem | Likely Cause | Fix |
|---------|-------|-------------|
| `Connection refused` | Ollama not running | `ollama serve`. Verify: `curl http://localhost:11434/api/tags` |
| Slow responses | Large model on CPU | Switch to a smaller model by editing `ollama_chat_model` in `backend/config.yaml` |
| Parsing errors | Model returns unexpected format | The Ollama client has a NDJSON fallback parser (see `src/llm/provider.py`). If it still fails, check Ollama logs. |

### Frontend

| Problem | Likely Cause | Fix |
|---------|-------|-------------|
| Blank page | Dependencies missing | `cd frontend && npm install && npm run dev` |
| "VITE_API_MOCK" not working | Env var not set | Use `VITE_API_MOCK=true npm run dev` (must be set on same line, not exported separately) |
| Port 5173 in use | Another Vite dev server | Kill it or change port in `frontend/vite.config.ts` |

### Data

| Problem | Likely Cause | Fix |
|---------|-------|-------------|
| Questions missing | Scraped data not loaded | Run `normalize.py` from `backend/` |
| Skill modules empty | Not seeded | `cd backend && uv run python scripts/seed_skill_modules.py` |
| RAG teacher says "cannot answer" | Embeddings not built | Run `cd backend && uv run python scripts/ingest.py` |
| Translation drift | Machine translation | Check `translations_status` in DB; `"machine"` values need manual review |

## Content Sourcing

All question content is gathered following the [Content Sourcing Playbook](docs/sourcing-playbook.md). Read it before adding new scrapers or questions.

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for adding themes, questions, and skill modules.

## License

MIT. See [LICENSE](LICENSE).

## Project Structure

```
jp_drivers_test_trainer/
├── backend/
│   ├── scripts/              # Setup, seed, ingest, normalize
│   ├── src/
│   │   ├── api/              # FastAPI route handlers + repositories
│   │   ├── llm/              # Ollama client, prompts, answer parsers
│   │   ├── migrations/       # SQL migration files (numbered)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── rag/              # Embedding, chunking, vector store
│   │   ├── repositories/     # Data access layer (lower-level)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic layer
│   │   ├── config.py         # pydantic-settings (yaml + env override)
│   │   ├── db.py             # Engine, session factory, sqlite-vec init
│   │   └── main.py           # FastAPI app entry point
│   ├── tests/
│   ├── config.yaml           # Runtime config overrides
│   ├── pyproject.toml
│   └── uv.lock
├── data/
│   ├── skill_modules/        # JSON maneuver walkthroughs
│   ├── raw_scrapes/          # Scraped question source files
│   ├── rag_source_documents/ # Documents for RAG embedding
│   ├── jp_drivers.sqlite     # Database (not tracked in git)
│   └── manual_review_queue.jsonl
├── docs/
│   ├── CONTRIBUTING.md
│   ├── sourcing-playbook.md
│   └── skill_module.schema.json
├── frontend/
│   ├── public/assets/skill/  # SVG maneuver diagrams
│   ├── src/
│   │   ├── components/       # React components (shadcn + Radix)
│   │   ├── hooks/            # Custom React hooks
│   │   ├── i18n/             # EN/PT translation resources
│   │   ├── lib/api/          # API client (mock + live providers)
│   │   ├── routes/           # TanStack Router route definitions
│   │   └── store/            # Zustand state stores
│   ├── tests/                # Playwright E2E tests
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── playwright.config.ts
├── scripts/                  # Dev utility scripts
├── .gitignore
├── LICENSE
└── README.md
```
