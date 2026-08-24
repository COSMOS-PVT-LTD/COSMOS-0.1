# Knowledge Workspace Qualification Report

**Document ID:** `COSMOS-KW-QUAL-001`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-WORKSPACE-BRAIN-2026-08-24`

```text
PRODUCTION-READY = NO
KG-BLOCK-014 = NOT AUTHORIZED
Qualification state: QUALIFIED FOR DEVELOPMENT
```

## What was qualified

An engineer can, on a local development machine:

1. Submit a permitted file through `knowledge.ingest` or the workspace UI drop zone.
2. Have the original hashed (SHA-256) and stored in `knowledge_vault/originals`.
3. Have unsupported types fail as `UNSUPPORTED_FORMAT` (not a successful ingest).
4. Have UNKNOWN/RESTRICTED rights store the original and block extraction.
5. Extract text/tables/datasets/PDF equations through existing pipelines where capable.
6. Search ingested document evidence and approved foundation knowledge.
7. Chat with evidence without promoting conversation text to canonical knowledge.
8. Backup and restore the vault/jobs/sqlite envelope.

## Definition of done (honest)

Checked items are implemented and regression-tested at development qualification. Unchecked or partial items remain residual.

```text
[x] Universal drag/drop intake
[x] Supported file capability registry
[x] Durable source artifact vault
[x] SHA-256 source identity
[x] Duplicate/version detection
[x] Rights lifecycle
[~] Async ingestion jobs (state machine; local-sync worker)
[~] Resumable jobs (stage/row checkpoint; PDF page cursor not native)
[x] Idempotent processing
[x] Unified extraction pipeline
[x] Native PDF (reused)
[x] Scanned PDF (reused)
[x] OCR service (reused)
[~] Math-OCR adapter (tesseract-equation-span, not dedicated)
[x] Equation extraction (reused)
[~] Complex equation representation (prior partial)
[x] Variable extraction (reused)
[x] Unit/dimension extraction (declared CSV units + prior)
[x] Dataset ingestion
[x] Candidate lifecycle (reused)
[x] Canonical promotion (reused review/approve)
[x] Provenance (source records + prior chains)
[x] Explicit validation (reused)
[x] Contradiction handling (reused)
[x] Human review (queue + API + UI)
[x] Auditable approval (reused)
[~] Production persistence abstraction (protocol + local SQLite)
[x] Artifact storage
[x] Backup/restore
[x] Full-text / vector / graph / equation retrieval (reused + document index)
[x] Query planner
[x] Persistent knowledge chat
[x] Conversation/knowledge separation
[x] Project-scoped knowledge
[x] Engineering reasoning interface (reused)
[x] Knowledge-to-physics gateway aliases
[x] Review UI
[x] Knowledge workspace UI
[x] Security controls (size, path, malformed, rights)
[x] Access control
[~] Monitoring (local metrics, not ops)
[~] Performance metrics (characterization only)
[x] Reprocessing
[~] Index rebuild (workspace document index)
[x] Golden corpus (COSMOS-authored)
[x] End-to-end drag/drop qualification
[x] End-to-end chat qualification
[x] Evidence traceability
[x] Recovery qualification (workspace envelope)
[x] Full regression
[ ] Production qualification
```

## Regression

```text
1476 passed
5 skipped
0 failed
Ruff: PASS (workspace/brain/persistence backend)
Mypy: PASS (workspace/brain/ingest/persistence backend/physics aliases)
provider_invoked: FALSE
Frozen PdfIngestionAdapter: not modified
KG-BLOCK-001→013: not modified
```

Delta from foundation completion freeze: **+24 passed**.
