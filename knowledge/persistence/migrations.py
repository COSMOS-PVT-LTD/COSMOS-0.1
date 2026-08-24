"""SQLite schema and migrations for the production persistence boundary."""

from __future__ import annotations

SCHEMA_VERSION = 1

MIGRATION_001 = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    file_hash TEXT NOT NULL,
    rights_status TEXT NOT NULL,
    license TEXT,
    document_class TEXT,
    edition TEXT,
    revision TEXT,
    publisher TEXT,
    author TEXT,
    organization TEXT,
    publication_year INTEGER,
    usage_constraints TEXT,
    ingested_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    document_class TEXT,
    content_hash TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS pages (
    page_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    classification TEXT,
    char_count INTEGER NOT NULL,
    image_hash TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    UNIQUE (document_id, page_number)
);

CREATE TABLE IF NOT EXISTS regions (
    region_id TEXT PRIMARY KEY,
    page_id TEXT NOT NULL,
    region_type TEXT NOT NULL,
    text TEXT,
    confidence REAL,
    FOREIGN KEY (page_id) REFERENCES pages(page_id)
);

CREATE TABLE IF NOT EXISTS ocr_results (
    ocr_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    image_hash TEXT NOT NULL,
    backend TEXT NOT NULL,
    backend_version TEXT,
    text TEXT,
    confidence REAL,
    failure TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS math_ocr_results (
    math_ocr_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    region_id TEXT NOT NULL,
    image_hash TEXT,
    source_representation TEXT,
    latex TEXT,
    backend TEXT NOT NULL,
    failure TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS equation_candidates (
    candidate_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    page_number INTEGER,
    region_id TEXT,
    raw_text TEXT NOT NULL,
    normalized_text TEXT,
    latex TEXT,
    image_hash TEXT,
    extraction_method TEXT,
    backend TEXT,
    backend_version TEXT,
    version TEXT NOT NULL DEFAULT '1.0.0',
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS variable_candidates (
    variable_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES equation_candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS entity_candidates (
    entity_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_results (
    validation_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    state TEXT NOT NULL,
    dimension_state TEXT,
    semantic_state TEXT,
    unit_state TEXT,
    reasons TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES equation_candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    validation_state TEXT NOT NULL,
    page_image_hash TEXT,
    ocr_text TEXT,
    warnings TEXT,
    FOREIGN KEY (candidate_id) REFERENCES equation_candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES equation_candidates(candidate_id)
);

CREATE TABLE IF NOT EXISTS contradictions (
    contradiction_id TEXT PRIMARY KEY,
    left_entity_id TEXT NOT NULL,
    right_entity_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    relation TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_versions (
    version_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    supersedes_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    payload_json TEXT
);
"""

MIGRATIONS: tuple[tuple[int, str], ...] = ((1, MIGRATION_001),)
