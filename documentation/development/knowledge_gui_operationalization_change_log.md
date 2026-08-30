# Knowledge GUI Operationalization — Change Log

## 2026-08-30 — Phase completion

### Added

- `knowledge/workspace/operational.py` — enriched health, search, validation helpers
- `POST /api/search`, `GET /api/validation`
- Chat response fields: `grounding_state`, `trace`, `provider_invoked`
- Knowledge Workspace UI zones: overview, embedding strip, search, validation, trace, evidence modal, document inspector sections
- 17 automated tests (GUI-KI API-EQUIVALENT + unit operational API)
- 10 documentation artifacts under `documentation/development/knowledge_gui_operationalization_*`

### Modified

- `knowledge/workspace/server.py`
- `gui/knowledge_proxy.py`
- `gui/static/workbench/knowledge.html`
- `gui/static/maharshi.js`
- `gui/static/maharshi.css`

### Not modified

- KG-BLOCK-001→013 frozen canonical modules
- `knowledge/brain/health.py`
- `knowledge/validation/models.py`

### Regression

- 1519 → **1536** passed (+17), 5 skipped, 0 failed
