-- 0001_initial.sql
-- Raw SQL migration mirroring the SQLAlchemy ORM models.
-- No Alembic — run via scripts/apply_migrations.py

PRAGMA foreign_keys = ON;

-- ===========================================================================
-- themes
-- ===========================================================================
CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name_en VARCHAR(200) NOT NULL,
    name_pt VARCHAR(200) NOT NULL,
    parent_id INTEGER REFERENCES themes(id),
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_themes_parent_id ON themes(parent_id);
CREATE INDEX IF NOT EXISTS idx_themes_slug ON themes(slug);

-- ===========================================================================
-- questions
-- ===========================================================================
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    theme_id INTEGER NOT NULL REFERENCES themes(id),
    prompt_en TEXT NOT NULL,
    prompt_pt TEXT NOT NULL,
    answer_en TEXT NOT NULL,
    answer_pt TEXT NOT NULL,
    explanation_en TEXT NOT NULL,
    explanation_pt TEXT NOT NULL,
    tricky BOOLEAN NOT NULL DEFAULT 0,
    tricky_pattern VARCHAR(200),
    difficulty INTEGER NOT NULL DEFAULT 3,
    translations_status VARCHAR(20) NOT NULL DEFAULT 'missing',
    source_url VARCHAR(500),
    license VARCHAR(100),
    attribution VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_theme_id ON questions(theme_id);

-- ===========================================================================
-- attempts
-- ===========================================================================
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    score INTEGER NOT NULL DEFAULT 0,
    max_score INTEGER NOT NULL DEFAULT 0,
    passed BOOLEAN NOT NULL DEFAULT 0,
    language VARCHAR(5) NOT NULL DEFAULT 'en',
    difficulty_tricky REAL NOT NULL DEFAULT 0.0,
    time_limit_seconds INTEGER NOT NULL DEFAULT 0
);

-- ===========================================================================
-- attempt_answers
-- ===========================================================================
CREATE TABLE IF NOT EXISTS attempt_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    user_answer TEXT,
    is_correct BOOLEAN NOT NULL DEFAULT 0,
    time_spent_ms INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_attempt_answers_attempt_id ON attempt_answers(attempt_id);
CREATE INDEX IF NOT EXISTS idx_attempt_answers_question_id ON attempt_answers(question_id);

-- ===========================================================================
-- study_plans
-- ===========================================================================
CREATE TABLE IF NOT EXISTS study_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    days_json TEXT NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'default-beginner',
    weak_themes_json TEXT
);

-- ===========================================================================
-- rag_documents
-- ===========================================================================
CREATE TABLE IF NOT EXISTS rag_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url VARCHAR(500),
    title VARCHAR(300) NOT NULL,
    doc_type VARCHAR(20) NOT NULL,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rag_documents_doc_type ON rag_documents(doc_type);

-- ===========================================================================
-- rag_chunks
-- ===========================================================================
CREATE TABLE IF NOT EXISTS rag_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES rag_documents(id),
    chunk_text TEXT NOT NULL,
    chunk_idx INTEGER NOT NULL DEFAULT 0,
    embedding_id VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_document_id ON rag_chunks(document_id);

-- ===========================================================================
-- skill_modules
-- ===========================================================================
CREATE TABLE IF NOT EXISTS skill_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name_en VARCHAR(200) NOT NULL,
    name_pt VARCHAR(200) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    overview_en TEXT NOT NULL,
    overview_pt TEXT NOT NULL,
    svg_path VARCHAR(300),
    correct_trajectory_json TEXT NOT NULL,
    wrong_trajectory_json TEXT NOT NULL,
    common_mistakes_json TEXT NOT NULL,
    checklist_json TEXT NOT NULL,
    pro_tip_en TEXT NOT NULL,
    pro_tip_pt TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_skill_modules_slug ON skill_modules(slug);

-- ===========================================================================
-- sqlite-vec virtual table for RAG chunk embeddings
-- vec0 stores float[768] embeddings (e5-small / all-MiniLM default dimension)
-- ===========================================================================
CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
    embedding float[768]
);
