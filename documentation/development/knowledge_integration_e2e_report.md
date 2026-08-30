# Knowledge Integration — E2E Report

**Workflow:** API-EQUIVALENT (desktop shell proxy)  
**Test:** `tests/integration_tests/knowledge/test_gui_backend_integration_qualification.py`

## Journey executed

```text
LOGIN (cosmos-admin, ADMIN profile)
  → POST /api/ingest (cooling.md)
  → GET /api/sources, /api/jobs, /api/graph
  → GET /api/sources/{id} (text_content present)
  → POST /api/chat (factual query)
  → POST /api/chat (semantic paraphrase)
  → KnowledgeWorkspace reload (persistence)
  → DELETE /api/sources/{id}
  → POST /api/ingest (re-ingest)
  → POST /api/chat (post-restore)
```

## Results

| Step | Result | Evidence |
|------|--------|----------|
| Authentication | PASS | Session cookie set; API 200 |
| Upload/ingest | PASS | source_id + job AVAILABLE/REVIEW_REQUIRED |
| Graph state | PASS | source_id in graph nodes |
| Factual chat | PASS | evidence + document_ids + conclusion |
| Semantic chat | PASS | evidence on paraphrase |
| Persistence | PASS | KI-T03 vault.verify after reload |
| Delete | PASS | node removed; document_ids exclude deleted |
| Re-ingest | PASS | new source_id in graph + chat evidence |

## GUI verification status

**NOT VERIFIED** — maharshi.js browser automation not run. API paths and payloads match `maharshi.js` contract (KI-T06).
