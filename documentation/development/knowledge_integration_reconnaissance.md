# COSMOS Knowledge Integration — Reconnaissance

**Date:** 2026-08-30  
**HEAD SHA:** `0295e022381b7482e6a5ad6c9e0807ee305b8e1d`  
**Qualification prompt:** `COSMOS_END_TO_END_KNOWLEDGE_INFRASTRUCTURE_INTEGRATION_QUALIFICATION_MASTER_CURSOR_PROMPT.md`

## Git state

| Item | Value |
|------|-------|
| HEAD | `0295e022381b7482e6a5ad6c9e0807ee305b8e1d` |
| Uncommitted | UI/UX shell work, login profiles, design tokens, knowledge RBAC (`knowledge/workspace/access.py`), integration tests |
| Frozen blocks | KG-BLOCK-001→013 per `documentation/development/kg_block_freeze_ledger.md` |

## Operational chain (as implemented)

```text
gui/static/workbench/knowledge.html + maharshi.js
   ↓ fetch /api/*
gui/server.py → gui/knowledge_proxy.py
   ↓ dispatch_knowledge_request
knowledge/workspace/server.py (WorkspaceRequestHandler)
   ↓
knowledge/workspace/session.py (KnowledgeWorkspace)
   ↓ ingest → extract → vault → jobs → graph → search → chat
knowledge/brain/chat.py + hybrid.py + planner.py
   ↓
knowledge/foundation/* (controlled RAG, provider_invoked=False)
```

## GUI entry points

| Surface | Path | Route |
|---------|------|-------|
| Desktop workbench | `gui/static/workbench/knowledge.html` | `/app/workbench/knowledge` |
| Maharshi JS client | `gui/static/maharshi.js` | Calls proxied `/api/*` |
| Popup embed | `gui/static/maharshi-popup.js` | iframe `?view=compact&embed=1` |
| Standalone workspace | `knowledge/workspace/static/index.html` | `/knowledge` |

## Authentication / session

| Layer | Module |
|-------|--------|
| Desktop login | `api/authentication.py`, `gui/server.py` `/api/auth/login` |
| Session cookie | `cosmos_session` in `gui/server.py` |
| Role → workspace | `api/authorization.py` `map_user_role_to_workspace()` |
| Knowledge RBAC | `knowledge/workspace/access.py` `WorkspaceAuthorization` |
| Proxy role header | `gui/server.py` `bind_session_to_workspace()` → `X-COSMOS-ROLE` |

**Note:** Mutating workspace actions (`INGEST`, `APPROVE`, `DESTROY`, etc.) require `WorkspaceRole.ADMIN` in `access.py`. Desktop maps COSMOS `ADMIN` login profile to workspace ADMIN.

## API surface (proxied)

Prefixes in `gui/knowledge_proxy.py`:

`/api/health`, `/api/sources`, `/api/jobs`, `/api/review`, `/api/ingest`, `/api/chat`, `/api/backup`, `/api/restore`, `/api/reprocess`, `/api/conversations`, `/api/graph`

## Ingestion path

1. `POST /api/ingest` → `WorkspaceRequestHandler._ingest`
2. `KnowledgeWorkspace.ingest()` — `knowledge/workspace/session.py`
3. `validate_upload` — `knowledge/workspace/security.py`
4. `classify_upload` — `knowledge/workspace/classify.py`
5. `vault.store_original` — `knowledge/workspace/vault.py`
6. `extract_upload` — `knowledge/workspace/extract.py`
7. Job lifecycle — `knowledge/workspace/jobs.py`

## Parsing / extraction / validation

- Parsers: `knowledge/parsers/` (+ frozen `w3/`)
- Extraction: `knowledge/extraction/`, `knowledge/workspace/extract.py`
- Validation: `knowledge/validation/` (KG-BLOCK-009 frozen)
- Workspace quality: `knowledge/workspace/quality.py`

## Graph

- Construction: `knowledge/graph/construction.py`
- Workspace view: `knowledge/workspace/graph_view.py` → `GET /api/graph`
- Session API: `KnowledgeWorkspace.knowledge_graph()`

## Indexing / embeddings

- Lexical/semantic: `knowledge/indexing/`, `knowledge/search/`
- W7 bundle: `knowledge/indexing/w7/`
- Deterministic backend: `knowledge/embeddings/local_backend.py` (`cosmos-local-deterministic-v1`)
- Neural backend: `knowledge/embeddings/neural_backend.py` (`cosmos-local-neural-mini-v1`, 64-dim)
- Production RAG: `knowledge/production/local_rag_pipeline.py` (`provider_invoked=False`)

## Chat / evidence

- Planner: `knowledge/brain/planner.py`
- Hybrid retrieval: `knowledge/brain/hybrid.py`
- Chat service: `knowledge/brain/chat.py`
- Answer assembly: `knowledge/foundation/reasoning_answer.py`
- API response: `evidence`, `document_ids`, `validation_state`, `plan`, `routed_to_solver`

## Lifecycle

- Approve document: `POST /api/sources/{id}/approve`, `POST /api/review` (`APPROVE_DOCUMENT`)
- Delete: `DELETE /api/sources/{id}` → `KnowledgeWorkspace.delete_source()`
- States: `knowledge/workspace/models.py` `JobStatus`, graph lifecycle in `knowledge/graph/lifecycle.py`

## Persistence (source of truth)

Runtime root: `{CosmosApplication.root}/workspace_data/`

| Store | Path |
|-------|------|
| Source manifests | `knowledge_vault/manifests/{source_id}.json` |
| Originals | `knowledge_vault/originals/{source_id}/{sha256}` |
| Derivatives | `knowledge_vault/derivatives/{source_id}/` |
| Jobs | `jobs/{job_id}.json` |
| Conversations | `conversations/{conversation_id}.json` |
| SQLite KV | `workspace.sqlite` via `knowledge/persistence/backend.py` |

## Existing tests (representative)

| Area | Path |
|------|------|
| Workspace E2E | `tests/unit_tests/knowledge/workspace/test_e2e_workspace.py` |
| Graph/delete | `tests/unit_tests/knowledge/workspace/test_graph_and_delete.py` |
| Approve | `tests/unit_tests/knowledge/workspace/test_approve_source.py` |
| Desktop proxy | `tests/unit_tests/gui/test_knowledge_proxy.py` |
| Neural embeddings | `tests/unit_tests/knowledge/embeddings/test_step7_neural_embeddings.py` |
| Production RAG | `tests/unit_tests/knowledge/production/test_step7_production_pipeline.py` |
| **New integration** | `tests/integration_tests/knowledge/test_gui_backend_integration_qualification.py` |

## GUI ↔ backend contract (maharshi.js)

| GUI action | API |
|------------|-----|
| Upload | `POST /api/ingest` (FormData) |
| Health poll | `GET /api/health`, `/api/sources`, `/api/jobs`, `/api/review`, `/api/graph` |
| Approve | `POST /api/sources/{id}/approve` |
| Reprocess | `POST /api/reprocess` |
| Delete | `DELETE /api/sources/{id}` |
| Chat | `POST /api/chat` |
| Backup | `POST /api/backup` |
| Session | `GET /api/auth/session` |

## Qualification envelope (unchanged)

- ≤25 documents; 1–4 concurrent queries; offline; `cosmos-local-neural-mini-v1`; `provider_invoked=False`
- `PRODUCTION-READY: NO` per Gate-6 Option B closure

## Reconnaissance gaps identified

| ID | Gap | Class |
|----|-----|-------|
| R-001 | Browser GUI not automated in CI — API-EQUIVALENT qualification only | D5 limitation |
| R-002 | Bootstrap admin `cosmos-admin` / `COSMOS-Dev-2026!` active on normal login path | D3 security finding |
| R-003 | Foundation corpus can answer generic engineering queries without user upload | D5 expected behavior |
| R-004 | Full solver telemetry not exposed in engineering console | D5 missing backend |
