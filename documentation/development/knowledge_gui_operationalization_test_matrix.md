# Knowledge GUI Operationalization — Test Matrix

## Regression

| Suite | Result |
|-------|--------|
| Full pytest | **1536 passed**, 5 skipped |

## GUI-KI browser tests (API-EQUIVALENT)

| ID | Description | Automated | Result |
|----|-------------|-----------|--------|
| GUI-KI-001 | Login → knowledge health | API-EQUIVALENT | PASS |
| GUI-KI-002 | Upload → ingestion succeeds | API-EQUIVALENT | PASS |
| GUI-KI-003 | Document in corpus | API-EQUIVALENT | PASS |
| GUI-KI-004 | Semantic query → evidence payload | API-EQUIVALENT | PASS |
| GUI-KI-005 | Evidence → source detail | API-EQUIVALENT | PASS |
| GUI-KI-006 | Chat exposes evidence + trace | API-EQUIVALENT | PASS |
| GUI-KI-007 | Graph entity payload | API-EQUIVALENT | PASS |
| GUI-KI-008 | Validation findings visible | API-EQUIVALENT | PASS |
| GUI-KI-009 | Delete → state updates | API-EQUIVALENT | PASS |
| GUI-KI-010 | Re-ingest → graph integrity | API-EQUIVALENT | PASS |
| GUI-KI-011 | Persistence after reload | API-EQUIVALENT | PASS |
| GUI-KI-012 | Viewer cannot ingest | API-EQUIVALENT | PASS |
| GUI-KI-013 | Provider boundary false | API-EQUIVALENT | PASS |
| GUI-KI-014 | Backend failure honest (400) | API-EQUIVALENT | PASS |

## Unit tests (operational API)

| Test | Result |
|------|--------|
| enriched_health metadata | PASS |
| operational_search diagnostics | PASS |
| validation_snapshot | PASS |
| HTTP search/health/validation routes | PASS |

## Playwright limitation

No Playwright dependency or CI browser runner in repository. Manual fallback: open `/app/workbench/knowledge`, exercise upload → search → evidence → chat → trace using DevTools network panel to verify `/api/search`, `/api/validation`, enriched `/api/health`.

## Test file locations

- `tests/integration_tests/knowledge/test_gui_operationalization_qualification.py`
- `tests/unit_tests/knowledge/workspace/test_operational_api.py`
