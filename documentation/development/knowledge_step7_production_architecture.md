# Step 7 — Production Local RAG Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  ProductionLocalRAGPipeline                       │
│  ingest → persist → index lifecycle → query                     │
└──────────┬──────────────┬─────────────────┬────────────────────┘
           │              │                 │
    ┌──────▼──────┐ ┌─────▼─────┐   ┌──────▼──────────┐
    │ LocalKnowledge│ │ IndexLifecycle│ │ ProductionRetrieval│
    │ Store         │ │ Manager       │ │ Service            │
    └──────┬──────┘ └─────┬─────┘   └──────┬──────────┘
           │              │                 │
    ┌──────▼──────┐ ┌─────▼─────┐   ┌──────▼──────────┐
    │ JSON files  │ │ W7 bundles │   │ W7 search +     │
    │ graph/docs  │ │ on disk    │   │ diagnostics     │
    └─────────────┘ └────────────┘   └─────────────────┘

Supporting:
  DeterministicLocalEmbeddingBackend  →  offline vectors
  IncrementalIngestionCoordinator     →  change detection
  ObservabilityRecorder               →  structured events
  OfflineExecutionGuard               →  provider_invoked=False
  RecoveryProcedure                   →  corruption / stale recovery
  PerformanceBenchmark                →  ingest/query timing
```

## Data Flow — Ingest

1. **Input:** `IngestRequest` (document_id, source_id, artifact_id, content)
2. **Pipeline:** `run_knowledge_pipeline_extended()` produces graph + evidence
3. **Persist:** `LocalKnowledgeStore` writes graph JSON, document registry, manifest
4. **Index:** `IndexLifecycleManager.build()` creates W7 bundle with embeddings
5. **Record:** `ObservabilityRecorder` logs ingest/index events

## Data Flow — Query

1. **Input:** `QueryRequest` (query text, allowed_document_ids, top_k)
2. **Load:** `IndexLifecycleManager.load()` validates bundle integrity
3. **Retrieve:** `ProductionRetrievalService` runs lexical + semantic + graph paths
4. **Output:** `QueryResponse` with ranked hits and diagnostics

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| Offline-first | `OfflineExecutionGuard`, deterministic embeddings |
| Fail-closed integrity | `CorruptionError`, `SchemaMismatchError`, digest checks |
| Observable | `ObservabilityRecorder` with typed event names |
| Recoverable | `RecoveryProcedure` for invalidate/rebuild paths |
| Non-invasive | New packages only; frozen orchestrator untouched |

## Integration with Existing W1–W7 Stack

- Ingestion uses **W4** extended pipeline (`parsed_document` path)
- Index bundles wrap **W7** lexical/semantic/graph adjacency structures
- Retrieval delegates to existing **W7** search primitives
- Validation uses **W6** extended context validation where applicable
