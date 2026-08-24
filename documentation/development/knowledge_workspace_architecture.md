# Knowledge Workspace Architecture

**Document ID:** `COSMOS-KW-ARCH-001`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-WORKSPACE-BRAIN-2026-08-24`  
**Baseline:** `KG-KF-FOUNDATION-COMPLETION-2026-08-24`

```text
PRODUCTION-READY = NO
KG-BLOCK-014 = NOT AUTHORIZED
Qualification state: QUALIFIED FOR DEVELOPMENT
```

## Purpose

Additive Knowledge Workspace and Engineering Knowledge Brain on top of the development-qualified Knowledge Foundation. An engineer can drop a permitted file, retain the original, extract candidates without fabrication, review/approve through existing governance, and chat against accumulated evidence.

This is not a disconnected RAG prototype. The UI calls the same `KnowledgeWorkspace` contracts as tests.

## Package map

```text
knowledge/ingest.py                 knowledge.ingest(file) facade
knowledge/workspace/                intake, vault, jobs, datasets, UI
knowledge/brain/                    planner, hybrid search, chat, health
knowledge/persistence/backend.py    PersistenceBackend protocol (SQLite local)
```

Frozen KG-BLOCK-001→013 packages were not modified. `knowledge/ingestion_adapters/pdf.py` was not modified.

## Runtime flow

```text
ENGINEER
  → Knowledge Workspace UI (stdlib HTTP + static HTML)
  → KnowledgeWorkspace.ingest / conversations.ask / review_equation
  → DurableArtifactVault + JobStore + PersistenceBackend
  → extract_upload → existing PDF/OCR/markdown pipelines where applicable
  → candidate indexes (workspace documents) + KnowledgeFoundationService
  → QueryPlanner + hybrid retrieval + EngineeringAnswer
  → PhysicsKnowledgeGateway (approved-only aliases)
```

## Local-first rules

- No mandatory cloud OCR, embeddings, or object storage.
- SQLite is a **local/development** persistence boundary, not a production multi-node database.
- Tesseract equation-span is **not** a dedicated math-OCR engine.
- Conversation memory is stored separately from canonical knowledge and is never auto-promoted.
- UNKNOWN and RESTRICTED rights register the original and block extraction.

## Entry points

- Programmatic: `from knowledge.ingest import ingest` or `KnowledgeWorkspace(root).ingest(...)`
- UI: `python -m knowledge.workspace.server --root workspace_data`
- Default local UI role is `ENGINEER`; approval requires `APPROVER` / `ADMIN` (`X-COSMOS-ROLE`).
