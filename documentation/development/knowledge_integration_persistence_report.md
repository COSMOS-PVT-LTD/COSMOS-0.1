# Knowledge Integration — Persistence Report

## Source of truth

`{CosmosApplication.root}/workspace_data/` — single-writer JSON + SQLite KV.

## Restart test (KI-T03)

1. Ingest via API
2. Chat with evidence
3. Instantiate new `KnowledgeWorkspace(app.root / "workspace_data")`
4. `search_documents("regenerative cooling")` — PASS
5. `vault.verify(source_id)` — PASS
6. Subsequent API chat — evidence preserved

## Backup/restore

Covered by `test_destroy_restore_recovers_document_evidence` in `test_e2e_workspace.py`.

## Defects

None.
