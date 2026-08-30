# Knowledge GUI Operationalization — Architecture

## Control surface chain

```text
knowledge.html + maharshi.js
  → /api/* (gui/server.py)
  → gui/knowledge_proxy.py
  → knowledge/workspace/server.py
  → KnowledgeWorkspace (session.py)
  → brain/ (chat, hybrid) + foundation/ + vault/jobs
```

## New operational layer (additive, non-frozen)

| Component | Role |
|-----------|------|
| `knowledge/workspace/operational.py` | Enriched health, search+diagnostics, validation snapshot |
| `POST /api/search` | Hybrid/unified/document retrieval with trace payload |
| `GET /api/validation` | Review queue + job failures + graph integrity findings |
| `GET /api/health` | Extended in-handler via `enriched_health()` — preserves existing keys |

## Frozen boundaries respected

- `knowledge/brain/health.py` — **not modified**
- KG-BLOCK-001→013 canonical modules — **not modified**
- `knowledge/validation/models.py` — **not modified**

## Data honesty rules

- `provider_invoked: false` on all new API payloads
- Step-7 production semantic index: labeled **NOT AVAILABLE** when workspace session lacks ProductionLocalRAGPipeline binding
- Missing metrics render as **NOT AVAILABLE** in UI

## GUI zones

| Zone | Primary API |
|------|-------------|
| Knowledge Overview | `/api/health` |
| Ingestion Console | `/api/ingest`, `/api/reprocess`, `/api/sources` |
| Document Inspector | `/api/sources/{id}` |
| Semantic Search | `/api/search` |
| Retrieval Diagnostics | `/api/search` → `diagnostics` |
| Evidence Viewer | search/chat evidence + source detail |
| Chat (evidence-oriented) | `/api/chat` → `grounding_state`, `trace` |
| Graph Explorer | `/api/graph` |
| Validation Center | `/api/validation`, `/api/review` |
| Knowledge Trace | search/chat `trace` |
| Embedding Status | `/api/health` embedding fields |
