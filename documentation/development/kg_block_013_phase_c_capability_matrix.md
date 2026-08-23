# KG-BLOCK-013 Phase C — Capability Matrix

**Document ID:** COSMOS-KG-B013-PHASE-C-MATRIX-001  
**Date:** 2026-08-23

| ID | Capability | Frozen Requirement | Implementation | Tests | Integration | Status |
|----|------------|-------------------|----------------|-------|-------------|--------|
| GAP-C-001 | Citation integrity validation | `citation_validator.py` (KG-041) | `knowledge/validation/citation_validator.py` | `test_phase_c_validation.py` | `validate_context_extended()` + `ValidationContext.parsed_document` | **PASS** |
| GAP-C-002 | Ambiguity detection | `ambiguity_detector.py` (KG-044) | `knowledge/validation/ambiguity_detector.py` | `test_phase_c_validation.py` | `validate_context_extended()` | **PASS** |
| GAP-C-003 | PDF normalizer coverage | DEV-010 test gap | Existing `pdf_normalizer.py` | `test_pdf_normalizer_phase_c.py` | Parser contract path | **PASS** |

## Gap Justification Summary

### GAP-C-001 — Citation Validator

- **Genuine:** W3 produces citations/references; no validator checked unresolved keys or orphan bibliography entries.
- **Consolidation insufficient:** `provenance.py` validates anchor chains, not citation graph integrity.
- **Compatibility insufficient:** Phase-B facades do not cover validation.
- **Owner:** `knowledge/validation/citation_validator.py`
- **Consumer:** W9 extended validation → W10/W11 controlled RAG gate

### GAP-C-002 — Ambiguity Detector

- **Genuine:** `conflicts.py` handles numeric/claim conflicts, not hedging language or conflicting sections.
- **Owner:** `knowledge/validation/ambiguity_detector.py`
- **Consumer:** W9 extended validation → reasoning classification

### GAP-C-003 — PDF Normalizer Tests

- **Genuine:** DEV-010 documented missing coverage; module existed without sufficient edge-case tests.
- **Owner:** `knowledge/parsers/pdf_normalizer.py` (unchanged)
- **Consumer:** Frozen parser contract tests

## Deferred Items

DG-154 (`text_utils.py`), DG-033, DG-067, exporters, persistence, embeddings, glossary parsers, batch_loader.
