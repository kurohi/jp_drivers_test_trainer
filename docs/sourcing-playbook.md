# Content Sourcing Playbook — JP Driver's Test Trainer

> **Executor's manual** for gathering free/open Japanese driver's test content for EN + PT.
> This playbook is the single source of truth for T14 (scraper implementation) and all downstream content ingestion.

---

## 1. Goal

- **≥660 native questions** across all 22 official themes (≥30 per theme minimum)
- **≥40% flagged `tricky=true`** by the 7-pattern detector (manual-review queue for ambiguous)
- **Bilingual EN/PT** — every question has both language variants; `translations_status` tracks verification
- **Every persisted question carries**: `source_url` (string), `license` (string), `attribution` (string)
- **No paid content** — JAF "Rules of the Road", Amitie, Yumi books are EXCLUDED from direct ingestion (see §5)

---

## 2. 22 Official Themes (slug + EN + PT)

These slugs are the authoritative identifiers from `backend/scripts/seed_themes.py`. Every scraped question MUST be mapped to one of these slugs.

| # | Slug | Name (EN) | Name (PT) |
|---|------|-----------|-----------|
| 1 | `driver-mindset` | Driver Mindset | Mentalidade do Motorista |
| 2 | `signals` | Signals | Sinalização de Trânsito |
| 3 | `signs-and-markings` | Signs & Markings | Placas e Marcações |
| 4 | `prohibited-actions` | Prohibited Actions | Ações Proibidas |
| 5 | `emergency-vehicle-priority` | Emergency Vehicle Priority | Prioridade de Veículos de Emergência |
| 6 | `intersections-and-railroad-crossings` | Intersections & Railroad Crossings | Interseções e Passagens de Nível |
| 7 | `pedestrian-protection` | Pedestrian Protection | Proteção de Pedestres |
| 8 | `safety-checks` | Safety Checks | Verificações de Segurança |
| 9 | `overtaking-and-passing` | Overtaking & Passing | Ultrapassagem e Passagem |
| 10 | `license-system` | License System | Sistema de Pontos da CNH |
| 11 | `blind-spots` | Blind Spots | Pontos Cegos |
| 12 | `human-factors` | Human Factors | Fatores Humanos |
| 13 | `natural-forces` | Natural Forces | Forças Naturais |
| 14 | `adverse-conditions` | Adverse Conditions | Condições Adversas |
| 15 | `typical-accidents` | Typical Accidents | Acidentes Típicos |
| 16 | `vehicle-maintenance` | Vehicle Maintenance | Manutenção do Veículo |
| 17 | `parking-and-stopping` | Parking & Stopping | Estacionamento e Parada |
| 18 | `loading-and-passengers` | Loading & Passengers | Carga e Passageiros |
| 19 | `accident-response` | Accident Response | Resposta a Acidentes |
| 20 | `highway-driving` | Highway Driving | Direção em Rodovias |
| 21 | `route-planning` | Route Planning | Planejamento de Rota |
| 22 | `speed-and-following-distance` | Speed & Following Distance | Velocidade e Distância |

---

## 3. 7 Trap-Question Patterns

Every question is evaluated against these patterns. A match on ≥1 sets `tricky=true` and `tricky_pattern` to the matching slug(s).

| # | Pattern Slug | Description | Regex Heuristic |
|---|-------------|-------------|-----------------|
| 1 | `assertive-language` | Uses absolute words (always, never, must, only, all, none) to make a statement sound definitive when exceptions exist | `\b(always|never|must|only|all|none|every|no one|under all circumstances)\b` |
| 2 | `permission-vs-obligation` | Confuses "may" (permission) with "must" (obligation) — e.g., "drivers may stop" vs "drivers must stop" | `\b(may|might|allowed to|permitted to|can)\b.*\b(stop|yield|proceed|pass)\b` vs `\b(must|shall|required to|obligated to)\b` |
| 3 | `double-negatives` | Two negatives in the prompt create confusion — e.g., "not prohibited" = allowed | `\bnot\b.*\b(prohibited|forbidden|illegal|restricted|banned|allowed|permitted)\b` |
| 4 | `scope-substitution` | Swaps the scope of a rule — e.g., "within 5m" becomes "within 10m", or "expressway" becomes "regular road" | Numeric distance swaps: `\b(5|10|15|20|30)\s*(meters?|m)\b` in context of stopping/parking rules |
| 5 | `term-substitution` | Replaces a key term with a similar but different one — e.g., "novice driver sign" → "experienced driver sign" | Look for antonym pairs in reason vs prompt |
| 6 | `ignored-exceptions` | States a general rule but omits a critical exception — e.g., "overtaking is prohibited" without mentioning the visibility exception | `\b(prohibited|not allowed|forbidden)\b` without `\b(except|unless|however|but|unless)\b` nearby |
| 7 | `number-confusion` | Swaps numbers in the answer — e.g., "45/50 to pass" becomes "40/50", or "30 meters" becomes "50 meters" | `\b(\d+)\b` compared against known reference values |

---

## 4. Top 10 Practical Failure Points

These are the most common reasons candidates fail the closed-course skill test. They inform the "tricky" weighting for related themes.

| # | Failure Point | Related Theme(s) |
|---|--------------|------------------|
| 1 | Incomplete stops at stop lines / intersections | `intersections-and-railroad-crossings`, `signals` |
| 2 | Missing head/shoulder turns (not checking blind spots) | `blind-spots`, `safety-checks` |
| 3 | Wheel over curb during parallel parking + forcing forward | `parking-and-stopping` |
| 4 | Not yielding to pedestrians at crosswalks | `pedestrian-protection` |
| 5 | Signal timing too early or too late (must be ≥30m before turn) | `signals`, `route-planning` |
| 6 | Wrong turn positioning (cutting corners on right turns) | `intersections-and-railroad-crossings` |
| 7 | Hill-start rollback (>30cm = fail) | `adverse-conditions`, `safety-checks` |
| 8 | Stopping ON railroad tracks instead of BEFORE | `intersections-and-railroad-crossings` |
| 9 | No post-reverse visual check before moving forward | `safety-checks`, `parking-and-stopping` |
| 10 | Signal cancellation failure (forgetting to cancel after turn) | `signals` |

---

## 5. Free Source Inventory (≥10 Sources)

| # | Source | URL | License Assessment | Est. Questions | Scraping Difficulty |
|---|--------|-----|-------------------|----------------|---------------------|
| 1 | **JapanDL.com** | https://japandl.com/en | Community-free; practice questions openly available. No explicit license — treat as "rewrite-required" for safety. | 1,545+ (Gaimen Kirikae), 496 (Learner's), 1,041 (Full License), 626 (Class 2) | Medium — SPA with JS rendering; use Apify or Playwright |
| 2 | **Lease Japan — Test 1** | https://leasejapan.com/en/license-conversion/written-test-guide/test-1/ | Free blog content; 50 T/F questions with reasons. No explicit license — treat as "rewrite-required". | 50 | Low — static HTML, clean structure |
| 3 | **Lease Japan — Test 2** | https://leasejapan.com/en/license-conversion/written-test-guide/test-2/ | Same as Test 1. | 50 | Low |
| 4 | **Lease Japan — Test 3** | https://leasejapan.com/en/license-conversion/written-test-guide/test-3/ | Same as Test 1. | 50 | Low |
| 5 | **MenkyoHub Community** | https://menkyohub.com | Community-contributed Q&A; check individual post licenses. Treat as "community-free". | ~200-300 | Medium — forum structure |
| 6 | **BR no Japão Blog** (PT) | https://brnojapao.com.br | Brazilian expat blog with PT driving guides. Blog content — "rewrite-required". | ~30-50 PT questions | Low — WordPress blog |
| 7 | **DIA A DIA News Blog** (PT) | https://diaadia.news | PT-language news/blog with driving-related content. "rewrite-required". | ~20-30 PT questions | Low |
| 8 | **Lo-PAL Practical Guide** | https://lo-pal.com | Practical driving guide for foreigners in Japan. "rewrite-required". | ~40-60 | Low-Medium |
| 9 | **Menkyo Tottaru Academy EN Guide** | https://menkyo-tottaru.com/en | English guide for Japanese license conversion. "rewrite-required". | ~50-80 | Low |
| 10 | **online-ds.jp** | https://online-ds.jp | Japanese driving school articles. JP-language source — useful for rule verification, not direct EN questions. "rewrite-required". | ~100+ articles | Medium — Japanese content |
| 11 | **Reddit r/japanresidents** | https://reddit.com/r/japanresidents | Community discussions about the test. "community-free" — extract Q&A from threads. | ~50-100 from threads | Medium — Reddit API or scraping |
| 12 | **NPA English-language PDFs** (Chiba/Osaka) | Varies by prefecture (search: `site:npa.go.jp "driver" "license" "english"`) | Government public documents — "public-domain". | ~20-40 | Medium — PDF parsing |
| 13 | **GitHub: kevincobain2000/japan-drivers-license-practice-test-questions-english** | https://github.com/kevincobain2000/japan-drivers-license-practice-test-questions-english | MIT-licensed (open-source repo with questions.tsv). "open-source" — best license in inventory. | ~100+ (TSV format) | Low — raw TSV file |

---

## 6. Excluded Sources (PAID — Do NOT Ingest)

| Source | Reason | Allowed Use |
|--------|--------|-------------|
| **JAF "Rules of the Road"** | Paid book; JAF explicitly disclaims it as NOT exam-prep material | Paraphrased rule-statement reference ONLY — never as "official exam questions" |
| **Amitie Driving School materials** | Paid prep kit | Paraphrased rule-statement reference ONLY |
| **Yumi Driving School materials** | Paid prep kit | Paraphrased rule-statement reference ONLY |

**Rule**: If a source requires payment, subscription, or physical book purchase to access, it is EXCLUDED from direct question ingestion. It may be consulted for rule verification and paraphrased into explanations, but the resulting question must cite a FREE source as its `source_url`.

---

## 7. Per-Source Scraping Strategy

### 7.1 JapanDL.com (https://japandl.com/en)

- **URL pattern**: `https://japandl.com/en/exam/paper-{paper_id}`
- **Sample paths**: `/en/exam/paper-1775192489399-6ljeo` (Gaimen Kirikae, 1545 Q), `/en/exam/paper-1775194229450-7704g` (Learner's, 496 Q)
- **Strategy**: SPA with JS rendering. Use Apify `apify/rag-web-browser` or Playwright to load each paper page. Questions are served dynamically — may need to click "Next" or scroll to load all.
- **CSS selectors**: Questions appear as T/F blocks. Look for `<div>` or `<section>` elements containing the question text and True/False buttons.
- **Expected count**: 1,545+ for Gaimen Kirikae paper
- **License**: rewrite-required (no explicit license)
- **Anti-scrape**: Moderate — rate-limit requests, add delays between page loads

### 7.2 Lease Japan (Tests 1-3)

- **URL pattern**: `https://leasejapan.com/en/license-conversion/written-test-guide/test-{N}/`
- **Strategy**: Static HTML. Each page has 50 T/F questions with question text, True/False options, and a "Reason" explanation.
- **CSS selectors**: Questions are in sequential page blocks. Each question has a statement paragraph followed by True/False radio buttons and a "Reason:" paragraph.
- **Expected count**: 50 per test × 3 tests = 150
- **License**: rewrite-required
- **Anti-scrape**: Low — straightforward HTML parsing with BeautifulSoup/lxml

### 7.3 GitHub kevincobain2000 Repo

- **URL**: `https://raw.githubusercontent.com/kevincobain2000/japan-drivers-license-practice-test-questions-english/master/questions.tsv`
- **Strategy**: Direct TSV download via httpx. Parse tab-separated columns.
- **Expected count**: ~100+ questions
- **License**: open-source (MIT)
- **Anti-scrape**: None — raw file

### 7.4 BR no Japão / DIA A DIA (PT Sources)

- **Strategy**: WordPress blog scraping. Use httpx + BeautifulSoup to extract article content.
- **CSS selectors**: Look for `<article>` or `.entry-content` divs containing numbered questions.
- **Expected count**: 30-50 PT questions combined
- **License**: rewrite-required

### 7.5 Reddit r/japanresidents

- **Strategy**: Use Reddit's JSON API (`https://www.reddit.com/r/japanresidents/.json`) or search for threads containing "driver's license test" / "外免切替".
- **Expected count**: 50-100 Q&A pairs from discussion threads
- **License**: community-free

### 7.6 NPA PDFs

- **Strategy**: Download PDFs from prefecture websites, parse with `pypdf` or `pdfplumber`.
- **Expected count**: 20-40 questions from English-language notices
- **License**: public-domain

---

## 8. Parser Schemas

### 8.1 Target Question Schema (maps to `questions` table)

```python
class ParsedQuestion(BaseModel):
    prompt_en: str           # The question statement in English
    answer_en: str           # "true" or "false" (normalized)
    explanation_en: str      # The reason/explanation in English
    theme_slug: str          # One of the 22 official slugs
    source_url: str          # URL where this question was found
    license: str             # "open-source" | "public-domain" | "community-free" | "rewrite-required"
    attribution: str         # Source name + author if available
    tricky: bool             # Auto-detected by pattern matcher
    tricky_pattern: str | None  # Matching pattern slug(s), comma-separated
    difficulty: int          # 1-5 (auto-assigned: tricky=4-5, non-tricky=1-3)
    raw_text: str            # Original text before normalization (for audit)
```

### 8.2 Parser Output Format

Each scraper yields a list of `ParsedQuestion` objects. The ingestion pipeline then:
1. Normalizes `answer_en` to `"true"` or `"false"`
2. Runs the tricky-pattern detector (§9)
3. Deduplicates against existing questions (§10)
4. Flags ambiguous items for manual review (§12)

---

## 9. Normalization Rules

### 9.1 Answer Normalization

| Raw Value | Normalized |
|-----------|-----------|
| "True", "TRUE", "true", "Yes", "YES", "Correct", "○" | `"true"` |
| "False", "FALSE", "false", "No", "NO", "Incorrect", "×", "X" | `"false"` |

### 9.2 Text Normalization

- Strip leading/trailing whitespace
- Normalize multiple spaces to single space
- Remove HTML tags (if present)
- Convert smart quotes to straight quotes: `'` `'` `"` `"` → `'` `"`
- Normalize em-dashes and en-dashes to hyphens: `—` `–` → `-`

### 9.3 Deduplication

- **Exact dedup**: Lowercase + strip punctuation → compare. If identical, skip.
- **Near-dup**: Use `rapidfuzz.fuzz.ratio()` on normalized prompts. If similarity > 85%, flag for manual review (do NOT auto-discard — may be a variant with different answer).
- **Cross-source dedup**: Same question from multiple sources → keep the one with the best license (open-source > public-domain > community-free > rewrite-required), merge explanations.

---

## 10. Tricky-Question Tagger (7-Pattern Regex)

The tagger applies these regex patterns to `prompt_en`. A question matching ≥1 pattern gets `tricky=true`.

```python
TRICKY_PATTERNS = {
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
    "term-substitution": None,  # Semantic check — compare prompt terms against known rule vocabulary
    "ignored-exceptions": re.compile(
        r"\b(prohibited|not allowed|forbidden|must not|shall not)\b(?!(.*\b(except|unless|however|but)\b))",
        re.IGNORECASE | re.DOTALL,
    ),
    "number-confusion": re.compile(
        r"\b(\d+)\s*/\s*(\d+)\b",  # Fraction patterns like "45/50", "90%"
        re.IGNORECASE,
    ),
}
```

**Note**: `term-substitution` requires semantic comparison against a known rule vocabulary dictionary. Implement as a separate pass that checks for antonym substitutions (e.g., "novice" vs "experienced", "uphill" vs "downhill").

---

## 11. Bilingual Parity Rules

- **EN-first pipeline**: All questions are ingested in English first. PT translation is a downstream step (T14 owns this).
- **Translation status tracking**:
  - `"missing"` — PT translation not yet generated
  - `"machine"` — PT translation generated by LLM (Ollama) but not manually verified
  - `"verified"` — PT translation manually reviewed and confirmed accurate
- **Parity check**: After translation, verify that `prompt_pt` length is within 30% of `prompt_en` length (catches truncation errors).
- **Missing translation guard**: If `translations_status != "verified"` and the user's active language is PT, the UI should show a warning banner (not silently suppress the question).

---

## 12. Manual-Review Queue Format

Ambiguous, near-duplicate, or low-confidence questions are written to `data/manual_review_queue.jsonl` (one JSON object per line):

```jsonl
{"raw_text": "Drivers must always display the novice sign regardless of confidence.", "source_url": "https://leasejapan.com/en/license-conversion/written-test-guide/test-1/", "reason": "assertive-language pattern match; verify if 'always' is accurate"}
{"raw_text": "Overtaking is prohibited on steep slopes.", "source_url": "https://japandl.com/en/exam/paper-1775192489399-6ljeo", "reason": "ignored-exceptions — no mention of visibility exception"}
{"raw_text": "The stopping distance is 10 meters.", "source_url": "https://brnojapao.com.br/artigo/cnh-japonesa", "reason": "number-confusion — verify against reference value (should be 30m for signals)"}
```

**Fields**:
- `raw_text` (string): The original question text before normalization
- `source_url` (string): Where the question was found
- `reason` (string): Why it was flagged (pattern name + brief explanation)

---

## 13. Execution Checklist for T14

- [ ] Implement scrapers for each source in `scripts/scrape_template.py`
- [ ] Run `scripts/dry_run_playbook.py` to validate parser compiles
- [ ] Ingest all free sources, producing `data/questions_raw.jsonl`
- [ ] Run normalization + dedup pipeline
- [ ] Run tricky-pattern tagger
- [ ] Write manual-review queue to `data/manual_review_queue.jsonl`
- [ ] Generate PT translations via Ollama (set `translations_status="machine"`)
- [ ] Load final questions into SQLite via seed script
- [ ] Verify ≥660 questions, ≥40% tricky, all 22 themes covered
