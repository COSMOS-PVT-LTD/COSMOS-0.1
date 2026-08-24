# Knowledge Workspace Gap Matrix

**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-WORKSPACE-BRAIN-2026-08-24`  
**Baseline:** `KG-KF-FOUNDATION-COMPLETION-2026-08-24`

Disposition is relative to `COSMOS_KNOWLEDGE_WORKSPACE_AND_BRAIN_COMPLETION.md`.

| Requirement | Previous | Now | Tests | Qualification | Residual |
|---|---|---|---|---|---|
| Universal intake gateway | Missing | `knowledge.ingest` + `KnowledgeWorkspace.ingest` | Required | Development | Local-sync worker only |
| File capability registry | Partial SourceFormat | `WorkspaceFormat` registry | Required | Development | CAD/mesh/sim future |
| Durable artifact vault | In-memory frozen vault | `DurableArtifactVault` disk/memory | Required | Development | Layout ≠ source of truth (manifests/DB are) |
| SHA-256 identity | Existing | Reused | Required | Development | — |
| Duplicate/version | PDF registry only | Filename/hash/parent/edition | Required | Development | Edition needs explicit kwarg |
| Rights | PDF/reference | All intake formats | Required | Development | Legal corpus still COSMOS-authored |
| Job orchestration | OCR jobs / incremental ingest | Full status enum + JSON jobs | Required | Development | Not a distributed queue |
| Checkpoint/resume | Missing | Stage/row/page fields + reprocess | Required | Partial | Native PDF page-cursor not exposed |
| Idempotency | Partial | `(hash, pipeline, config)` fingerprint | Required | Development | — |
| Unified extraction | Per-adapter | Capability router | Required | Development | Office images/math-OCR unavailable |
| Dataset ingestion | Missing | CSV/JSON/XLSX cells; units only if declared | Required | Development | No ontology Experiment auto-bind |
| Persistence abstraction | SQLite store | `PersistenceBackend` protocol | Required | Development | SQLite ≠ multi-node |
| Backup/restore | JSON snapshot / Step-7 recovery | Workspace zip + vault | Required | Development | In-memory KF seed is recreated, not snapshotted in the zip |
| Query planner | `classify_query` | `QueryPlanner` | Required | Development | Heuristic, not a learned planner |
| Knowledge chat | Missing | Persistent conversations | Required | Development | No LLM; retrieval + governed answer |
| Project scope | Hardcoded COSMOS | `project_id` on sources + filter | Required | Development | No separate physical partition |
| Physics aliases | `get_approved_*` | `get_physical_law` / `get_correlation` | Required | Development | Still approved-only |
| Workspace UI | Missing | stdlib HTTP + HTML | Required | Development | Local only |
| Access control | KnowledgeRole | WorkspaceRole mapping | Required | Development | Header-based local auth |
| Monitoring | Partial KF metrics | `WorkspaceMetrics` + health | Required | Development | Not production ops monitoring |
| Reprocess | Missing | New `pipeline_version` job | Required | Development | — |
| Index rebuild | W7 manager | Workspace document index rebuild | Required | Partial | W7 bundle not auto-rebuilt from workspace docs |
| Production-ready | NO | NO | Required | **NO** | See readiness report |

**PRODUCTION-READY = NO.** **KG-BLOCK-014 = NOT AUTHORIZED.**
