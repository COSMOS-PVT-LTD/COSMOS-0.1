# Knowledge Recovery Qualification Report (Workspace)

**Document ID:** `COSMOS-KW-RECOVERY-QUAL-001`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-WORKSPACE-BRAIN-2026-08-24`

```text
PRODUCTION-READY = NO
```

## Procedure

`KnowledgeWorkspace.backup(path)` writes a zip:

- `backup_manifest.json` (`cosmos-workspace-backup-v1`)
- `knowledge_vault/` originals, derivatives, manifests
- `jobs/`, `conversations/`
- `workspace.sqlite` when present

`KnowledgeWorkspace.restore(archive)` closes the local SQLite handle, replaces the root, reloads the vault/jobs, and rebuilds the document evidence index.

## Tests

- `test_backup_and_restore_roundtrip`
- `test_destroy_restore_recovers_document_evidence`

After destroy/restore, `search_documents("regenerative cooling")` hits and `vault.verify` passes.

## Residual

- Does not restore in-memory approved equation objects unless they were persisted through the foundation SQLite/snapshot path separately.
- Not a point-in-time clustered recovery system.
- Step-7 `RecoveryProcedure` for the JSON local RAG store remains a separate envelope.
