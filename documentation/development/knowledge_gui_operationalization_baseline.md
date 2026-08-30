# Knowledge GUI Operationalization — Baseline

**Recorded:** 2026-08-30  
**Repository:** `COSMOS_0.1`  
**Baseline SHA:** `0295e022381b7482e6a5ad6c9e0807ee305b8e1d`

## Test baseline (pre-implementation)

| Metric | Value |
|--------|-------|
| pytest passed | 1519 |
| pytest skipped | 5 |
| pytest failed | 0 |

## Test baseline (post-implementation)

| Metric | Value |
|--------|-------|
| pytest passed | 1536 |
| pytest skipped | 5 |
| pytest failed | 0 |
| New tests | 17 (4 unit + 13 integration GUI-KI) |

## Qualification envelope (unchanged)

| Field | Value |
|-------|-------|
| Knowledge qualification | YES — CONDITIONAL / ENVELOPE B |
| Production-ready | NO |
| provider_invoked | FALSE |
| Neural backend | cosmos-local-neural-mini-v1 |
| Frozen KG-BLOCK-001→013 | unchanged |

## Architecture snapshot

- GUI: `gui/static/workbench/knowledge.html`, `maharshi.js`, `maharshi.css`
- Proxy: `gui/knowledge_proxy.py` → `knowledge/workspace/server.py`
- Health: `knowledge/brain/health.py` (frozen) consumed via `workspace.health()`; GUI enrichment in `knowledge/workspace/operational.py`
- Chat: `knowledge/brain/chat.py` via `/api/chat`
- Search gap (pre-phase): no `/api/search` HTTP route — **addressed in this phase**

## Static analysis

- Ruff/Mypy: not re-run as gate; no new linter regressions observed in changed Python modules.

## Playwright / browser automation

- **Not present** in repository (`playwright` dependency absent).
- GUI-KI-001→014 implemented as **API-EQUIVALENT** integration tests through desktop-shell proxy.
