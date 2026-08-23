# KG-BLOCK-006 RECONNAISSANCE REPORT

**Date:** 2026-08-23  
**Block:** KG-BLOCK-006  
**Scope:** W3 Parsing — KG-014 → KG-018  
**Status:** RECONNAISSANCE COMPLETE — IMPLEMENTATION AUTHORIZED

---

## 1. Authorization State

| Item | Status |
|------|--------|
| KG-BLOCK-005 | **FROZEN** (human authorization per master prompt) |
| KG-BLOCK-006 | **IMPLEMENTATION AUTHORIZED** |
| KG-001→KG-051 matrix | HUMAN APPROVED |

---

## 2. Authoritative KG-014 → KG-018 Definitions

| Batch | Capability | Architecture Intent |
|-------|------------|---------------------|
| KG-014 | Document Structure | Sections, headings, paragraphs, hierarchy, page anchors, provenance |
| KG-015 | Tables | Row/column structure, headers, cell values, deterministic ordering |
| KG-016 | Figures | Figure metadata, captions, anchors — no CV/OCR |
| KG-017 | Equations | Textual equation representation — no engineering semantics |
| KG-018 | References / Citations | Citation occurrences vs reference records, bibliographic metadata |

**Numbering note:** OLD frozen KG-014→016 are graph capabilities. NEW KG-014→018 are W3 parsing under the reconciled architecture.

---

## 3. Existing Parsing Capabilities

### Frozen (BLOCK-002 / legacy KG-009)

| Module | Status |
|--------|--------|
| `knowledge/parsers/base.py` | `DocumentParser` protocol — frozen |
| `knowledge/parsers/models.py` | `NormalizedParsedDocument`, `DocumentSection`, `PageAnchor` — frozen |
| `knowledge/parsers/pdf_normalizer.py` | Outline-only PDF normalizer — frozen |
| `tests/unit_tests/knowledge/parsers/test_parsers.py` | 3 contract tests — frozen |

### BLOCK-005 upstream (frozen)

| Module | Role |
|--------|------|
| `knowledge/ingestion/models.py` | `IngestionResult`, `IngestionStage.PARSED` |
| `knowledge/ingestion_adapters/` | Normalized markdown / JSON envelopes |
| `knowledge/source/vault.py` | Artifact storage |

### W4 downstream (frozen, not modified)

| Module | Role |
|--------|------|
| `knowledge/extraction/equation.py` | Candidate equation extraction — BLOCK-007 scope |

---

## 4. Gaps Identified

| Gap | Resolution |
|-----|------------|
| No production W3 parser for tables, figures, equations, citations | New `knowledge/parsers/w3/` package |
| `IngestionResult` carries hash only, not content | `ParseContext` with explicit normalized content |
| Frozen `parsers/models.py` cannot be extended | New `StructuredParsedDocument` in `w3/models.py` |
| No ingestion→parse orchestration | `W3DocumentParser` + `ParserOrchestrator` |
| `IngestionStage.PARSED` never set | Pipeline advances stage on successful parse |

---

## 5. Planned Implementation

### Production modules (new)

```text
knowledge/parsers/w3/
├── __init__.py
├── exceptions.py
├── identity.py
├── models.py
├── content.py
├── structure.py      # KG-014
├── tables.py         # KG-015
├── figures.py        # KG-016
├── equations.py      # KG-017
├── references.py     # KG-018
├── pipeline.py
└── registry.py
```

### Tests (new)

```text
tests/unit_tests/knowledge/parsers/test_w3_parsing.py
```

### Frozen modules — NOT modified

```text
knowledge/parsers/__init__.py
knowledge/parsers/base.py
knowledge/parsers/models.py
knowledge/parsers/exceptions.py
knowledge/parsers/pdf_normalizer.py
knowledge/ingestion/**
knowledge/graph/**
knowledge/source/**
knowledge/ingestion_adapters/**
knowledge/models/quantity.py, unit.py, dimension.py
```

---

## 6. Deferred Functionality

- Binary PDF text extraction (BLOCK-005 L-001)
- OCR / computer vision for figures
- Equation semantic extraction (BLOCK-007)
- Canonical `Reference` model integration (downstream)
- Persistent parse artifact storage
- KG-BLOCK-007 extraction pipeline

---

## 7. Configuration-Control Constraints

1. Do not modify frozen BLOCK-001 → BLOCK-005 modules
2. Do not create duplicate Quantity/Unit/Dimension models
3. Do not execute source content
4. Deterministic identifiers via SHA-256 canonical parts
5. Status after implementation: **READY_FOR_REVIEW** (not frozen)

---

**END OF RECONNAISSANCE REPORT**
