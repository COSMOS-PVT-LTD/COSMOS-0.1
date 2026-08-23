# KG-BLOCK-005 ENGINEERING REVIEW & HARDENING REPORT

**Document ID:** COSMOS-KG-REV-B005  
**Date:** 2026-08-23  
**Block:** KG-BLOCK-005  
**Scope:** KG-006 → KG-013 (W1 Source System + W2 Ingestion)  
**Review Type:** Engineering Review + Verification + Targeted Hardening

---

## 28.1 Executive Status

```text
BLOCK:      KG-BLOCK-005
STATUS:     PASS WITH MINOR HARDENING
BATCHES:    KG-006, KG-007, KG-008, KG-009, KG-010, KG-011, KG-012, KG-013
BASELINE:   977 passed, 5 skipped
FINAL:      987 passed, 5 skipped
REGRESSION: +10 tests, 0 regressions
```

---

## 28.2 Scope Reviewed

| Batch | Capability | Module(s) | Review Result |
|-------|------------|-----------|---------------|
| **KG-006** | Source hashing / integrity | `knowledge/source/integrity.py` | PASS WITH HARDENING |
| **KG-007** | License & IP metadata | `knowledge/source/license.py` | PASS |
| **KG-008** | Source vault interface | `knowledge/source/vault.py` | PASS WITH HARDENING |
| **KG-009** | PDF ingestion | `knowledge/ingestion_adapters/pdf.py` | PASS |
| **KG-010** | DOCX ingestion | `knowledge/ingestion_adapters/docx.py` | PASS |
| **KG-011** | PPTX / XLSX ingestion | `knowledge/ingestion_adapters/pptx.py`, `xlsx.py` | PASS |
| **KG-012** | HTML / Markdown ingestion | `knowledge/ingestion_adapters/html.py` | PASS |
| **KG-013** | Repository ingestion | `knowledge/ingestion_adapters/repository.py` | PASS WITH HARDENING |
| **Cross** | Adapter registry / orchestration | `knowledge/ingestion_adapters/registry.py`, `base.py`, `normalize.py` | PASS |

**Authoritative references reviewed:**

- `coursor prompts /COSMOS_KG-BLOCK-005_MASTER_CURSOR_PROMPT.md`
- `coursor prompts /COSMOS_KG_001-051_ARCHITECTURE_RECONCILIATION_MASTER_DEVELOPMENT_MATRIX.md`
- `documentation/development/kg_block_005_handoff_report.md`
- `documentation/development/kg_architecture_reconciliation.md`
- `documentation/development/kg_001_051_traceability_matrix.md`
- `documentation/development/kg_001_051_architecture_reconciliation_master_matrix.md`
- `documentation/development/kg_001_051_matrix_approval_record.md`
- `documentation/development/knowledge_folder_development_status.md`
- `documentation/development/kg_block_freeze_ledger.md`
- `documentation/development/batch_status.json`
- `documentation/development/kg_block_004_engineering_review.md`

**Absent authoritative document (recorded, not invented):**

- `COSMOS_0.1_KNOWLEDGE_FOLDER_DEVELOPMENT_STATUS.md` — not at repository root; equivalent content located at `documentation/development/knowledge_folder_development_status.md`

---

## 28.3 Findings

### CRITICAL — 0

None.

### HIGH — 0 (resolved by hardening)

| ID | File | Observation | Engineering Impact | Action | Verification |
|----|------|-------------|-------------------|--------|--------------|
| H-001 (resolved) | `knowledge/ingestion_adapters/repository.py` | Root-boundary check used `str(path).startswith(str(root))`, allowing prefix-collision bypass (e.g. `/tmp/repo` vs `/tmp/repo_ext`) when symlinks resolve outside the configured root | Untrusted repository content could escape ingestion boundary and be stored in the vault | Replaced with `_is_within_root()` using `Path.relative_to()` | `test_repository_rejects_path_prefix_collision`, `test_repository_rejects_symlink_escape` |

### MEDIUM — 0 (resolved by hardening)

| ID | File | Observation | Engineering Impact | Action | Verification |
|----|------|-------------|-------------------|--------|--------------|
| M-001 (resolved) | `knowledge/source/vault.py` | `verify_integrity()` caught broad `except Exception` | Unrelated engineering failures could be masked as integrity mismatch | Narrowed to `IntegrityMismatchError`, `IntegrityValidationError` | `test_vault_verify_integrity_returns_false_on_mismatch` |

### LOW — 2 (accepted)

| ID | File | Observation | Engineering Impact | Action |
|----|------|-------------|-------------------|--------|
| L-001 | `knowledge/ingestion_adapters/pdf.py` | Binary PDF ingestion produces a structured envelope, not extracted text | Downstream W3 parsing required for full PDF text extraction | **ACCEPT** — documented limitation |
| L-002 | `knowledge/ingestion_adapters/docx.py`, `pptx.py`, `xlsx.py` | Office adapters use stdlib ZIP/XML extraction | Sufficient for BLOCK-005; production corpus may need richer Office XML handling | **ACCEPT** — defer to W3+ |

### INFORMATIONAL — 4

| ID | Observation | Action |
|----|-------------|--------|
| I-001 | New packages `knowledge/source/` and `knowledge/ingestion_adapters/` extend frozen `knowledge/ingestion/` contracts without modifying them | No change — compliant |
| I-002 | Repository ingestion stores per-file vault artifacts; format dispatch uses frozen `SourceFormat` enum | No change |
| I-003 | XLSX adapter reads stored cell values only; does not evaluate formulas | No change — compliant with contract |
| I-004 | Per-batch spec files KG-006–013 not found as standalone documents | Implementation validated against master prompt, handoff report, and traceability matrix |

---

## 28.4 Hardening Applied

| File | Change | Reason | Requirement / Invariant | Test Added | Verification |
|------|--------|--------|-------------------------|------------|--------------|
| `knowledge/ingestion_adapters/repository.py` | Added `_is_within_root()`; replaced `startswith` boundary check | Prevent symlink / prefix-collision escape from repository root | H1 path traversal, H2 symlink boundary (Review Areas H) | `test_repository_rejects_symlink_escape`, `test_repository_rejects_path_prefix_collision` | PASS |
| `knowledge/source/vault.py` | Narrowed `verify_integrity` exception handling | Preserve failure taxonomy; do not mask unexpected errors | Review Area K — error taxonomy | `test_vault_verify_integrity_returns_false_on_mismatch` | PASS |
| `tests/unit_tests/knowledge/test_block005_hardening.py` | **NEW** — 10 targeted hardening tests | Close review gaps in integrity, vault, dispatch, provenance, security, frozen API | Review Area N — test quality | All 10 tests | PASS |
| `tests/unit_tests/knowledge/source/test_source.py` | Duplicate-vault test now expects `VaultValidationError` | Strengthen negative-path assertion specificity | Vault immutability (C4) | Existing test tightened | PASS |

**Frozen modules modified:** 0

---

## 28.5 Test Results

```text
Targeted (BLOCK-005 W1+W2):   16 passed
Hardening (BLOCK-005):        10 passed
Knowledge suite:              601 passed, 5 skipped
Full repository suite:        987 passed, 5 skipped
Ruff (BLOCK-005 scope):       PASS
Mypy (source + adapters):     PASS (16 source files)
Import smoke:                 PASS
```

### New hardening tests

```text
test_verify_digest_accepts_uppercase_hex
test_sha256_empty_content_is_deterministic
test_vault_verify_integrity_returns_false_on_mismatch
test_vault_rejects_duplicate_with_validation_error
test_orchestrator_rejects_unsupported_format
test_docx_adapter_rejects_malformed_zip
test_ingestion_preserves_document_id_provenance
test_repository_rejects_symlink_escape
test_repository_rejects_path_prefix_collision
test_frozen_ingestion_contract_import_smoke
```

### Regression record

```text
Baseline:  977 passed, 5 skipped
Final:     987 passed, 5 skipped
Delta:     +10 tests, 0 regressions
```

---

## 28.6 Frozen Interface Verification

```text
KG-BLOCK-001:  UNCHANGED
KG-BLOCK-002:  UNCHANGED
KG-BLOCK-003:  UNCHANGED
KG-BLOCK-004:  UNCHANGED

knowledge/models/quantity.py:   UNCHANGED
knowledge/models/unit.py:       UNCHANGED
knowledge/models/dimension.py:  UNCHANGED
```

Verified via `git diff` against frozen module paths — no modifications detected.

---

## 28.7 Security / IP Verification

| Check | Result | Evidence |
|-------|--------|----------|
| Local-only processing | PASS | No network imports or calls in BLOCK-005 modules |
| No code / macro execution | PASS | HTML uses `HTMLParser` only; no script execution |
| Repository boundary enforcement | PASS (after hardening) | Symlink escape and prefix-collision tests |
| Credential / secret exclusion | PASS | `.env`, `*credentials*`, `*secret*`, `*.pem`, `*.key` excluded by default |
| No source-text exfiltration in errors | PASS | Domain exceptions carry operational messages only |
| Untrusted content treated as data | PASS | Ingestion adapters do not dereference external links or execute embedded content |
| License metadata records only | PASS | `LicenseMetadata` preserves declared fields; no legal inference |

---

## Review Area Summary

| Area | Topic | Result |
|------|-------|--------|
| A | Source integrity (SHA-256, determinism, mutation detection) | PASS |
| B | License / IP metadata | PASS |
| C | Source vault (abstraction, identity, integrity, immutability, ordering) | PASS WITH HARDENING |
| D | Adapter architecture / registry | PASS |
| E | PDF adapter | PASS |
| F | DOCX / PPTX / XLSX adapters | PASS |
| G | HTML / Markdown | PASS |
| H | Repository ingestion security | PASS WITH HARDENING |
| I | Provenance | PASS |
| J | Determinism | PASS |
| K | Error taxonomy | PASS WITH HARDENING |
| L | Security / IP boundary | PASS |
| M | API / interface stability | PASS |
| N | Test quality | PASS WITH HARDENING |

---

## 28.8 Deferred Work

**Required before freeze:** None — all HIGH/MEDIUM findings resolved.

**Future enhancement (not blocking):**

- W3 production parsing (tables, figures, citations)
- Binary PDF text extraction / production PDF library
- OCR
- Git revision provenance automation
- Persistent vault backend
- End-to-end ingestion → parsing integration tests
- Richer Office XML handling for production corpora

---

## 28.9 Acceptance Gates

```text
[x] All authorized KG-006 → KG-013 scope reviewed
[x] No CRITICAL findings
[x] No HIGH findings
[x] MEDIUM findings resolved
[x] Determinism verified
[x] Provenance verified
[x] Source integrity verified
[x] License/IP metadata verified
[x] Source vault verified
[x] Adapter registry verified
[x] Ingestion failure paths verified
[x] Repository security boundaries verified
[x] Frozen BLOCK-001 → BLOCK-004 interfaces preserved
[x] Protected quantity/unit/dimension models preserved
[x] Targeted tests pass
[x] Knowledge test suite passes
[x] Full regression passes
[x] Ruff passes for affected scope
[x] Mypy passes for affected scope
[x] Import/API smoke tests pass
[x] No unauthorized KG-014+ work exists
```

---

## 28.10 Final Recommendation

```text
PASS WITH MINOR HARDENING
```

KG-BLOCK-005 is recommended for **human freeze approval**. Engineering review and targeted hardening are complete. The block is **not frozen** by this report.

---

**END OF KG-BLOCK-005 ENGINEERING REVIEW REPORT**
