# Knowledge Persistence Qualification Report (Workspace)

**Document ID:** `COSMOS-KW-PERSIST-QUAL-001`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-WORKSPACE-BRAIN-2026-08-24`

```text
PRODUCTION-READY = NO
SQLite is not a production multi-node database.
```

## Layers

1. **Original artifacts** — `DurableArtifactVault` (`originals/` + manifests). Directory layout is not authoritative; manifests/records are.
2. **Workspace KV** — `PersistenceBackend` (`InMemoryPersistenceBackend` or `SQLitePersistenceBackend` at `{root}/workspace.sqlite`).
3. **Jobs / conversations** — JSON files under `{root}/jobs` and `{root}/conversations`.
4. **Knowledge Foundation** — existing `KnowledgeDatabase` + JSON snapshots remain available via `KnowledgeFoundationService`; not replaced.

The protocol exists so a future PostgreSQL backend can be added without a second canonical model. That backend is **not implemented** and **not qualified**.

## What is qualified

- Local SQLite KV migrate/put/get for source and dataset records.
- Thread-safe-enough local HTTP use (`check_same_thread=False` + write lock).
- JSON snapshot compatibility of the foundation path is unchanged.

## Residual

- Single-writer local files.
- No replication, no HA, no operational backup SLA.
- Foundation in-memory seed/indexes are not inside the workspace zip except where recovered_text in manifests allows document-index rebuild.
