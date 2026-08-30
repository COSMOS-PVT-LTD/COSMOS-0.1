# Knowledge Integration — GUI/Backend Contract Report

## maharshi.js → API mapping

| GUI control | JS function | API | Backend handler |
|-------------|-------------|-----|-----------------|
| Upload button | `addDocument()` | `POST /api/ingest` | `_ingest` |
| Refresh | `refreshAll()` | `GET /api/health,sources,jobs,review,graph` | respective handlers |
| Approve | `approveSource()` | `POST /api/sources/{id}/approve` | approve route |
| Reprocess | `reprocessSource()` | `POST /api/reprocess` | reprocess |
| Delete | `deleteSource()` | `DELETE /api/sources/{id}` | delete |
| Chat send | `sendChat()` | `POST /api/chat` | `_chat` |
| Backup | backup action | `POST /api/backup` | backup |

## Proxy path

```text
maharshi.js fetch("/api/...")
  → gui/server.py (session check)
  → gui/knowledge_proxy.py dispatch_knowledge_request
  → knowledge/workspace/server.py WorkspaceRequestHandler
  → KnowledgeWorkspace
```

## Contract verification (KI-T06)

All poll endpoints return HTTP 200 when authenticated.

## Issues

| ID | Issue | Class |
|----|-------|-------|
| C-001 | Job polling interval 12s in engineering-ux.js — acceptable for background jobs | D5 |
| C-002 | Upload shows success only after JSON response — not optimistic | PASS (correct) |

## Defects

None in contract wiring.
