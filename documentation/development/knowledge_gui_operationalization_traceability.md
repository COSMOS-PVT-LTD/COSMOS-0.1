# Knowledge GUI Operationalization — Traceability

## Document → Answer chain visibility

| Stage | GUI surface | Backend source |
|-------|-------------|----------------|
| DOCUMENT | Document Inspector, Sources table | `/api/sources/{id}` |
| INGESTION | Upload console, job status pills | `/api/ingest`, `/api/jobs` |
| NORMALIZATION | Inspector Lifecycle section | source detail + extraction summary |
| KNOWLEDGE EXTRACTION | Inspector Knowledge section | `extraction` fields |
| GRAPH | Graph explorer | `/api/graph` |
| INDEX | Overview indexed count | `enriched_health.indexed_document_count` |
| RETRIEVAL | Semantic search + diagnostics | `/api/search` |
| EVIDENCE | Evidence modal, chat evidence list | search/chat payloads |
| VALIDATION | Validation center | `/api/validation`, `/api/review` |
| ANSWER | Chat with grounding state | `/api/chat` |
| TRACEABILITY | Knowledge trace panel | `trace` on search/chat |

## Trace payload schema (deterministic)

```json
{
  "user_query": "...",
  "retrieval": { "mode": "...", "methods": ["..."] },
  "documents": ["source-id"],
  "evidence": ["snippet"],
  "graph_entities": ["entity-id"],
  "validation": "state",
  "answer": "conclusion or NOT AVAILABLE"
}
```

## Evidence integrity

- No truncation in evidence modal (chat list capped at 8 items for display density; full text in modal)
- Grounding states: GROUNDED, PARTIALLY_GROUNDED, INSUFFICIENT_EVIDENCE, ROUTED_TO_SOLVER
- Insufficient evidence not upgraded to confident answers in chat backend (preserved brain/chat behavior)

## Graph integrity

- `graph_integrity` from health + validation findings
- GUI-KI-010 verifies integrity after reprocess
