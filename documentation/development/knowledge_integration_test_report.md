# Knowledge Integration — Test Report

**Executed:** 2026-08-30

## Commands

```bash
python -m pytest tests/integration_tests/knowledge/test_gui_backend_integration_qualification.py -v
python -m pytest tests/unit_tests/knowledge/ -q
python -m pytest -q
python -m ruff check tests/integration_tests/knowledge/test_gui_backend_integration_qualification.py
```

## Results

| Suite | Passed | Skipped | Failed |
|-------|--------|---------|--------|
| New integration (7) | 7 | 0 | 0 |
| Knowledge unit | 1054 | 5 | 0 |
| Full regression | **1519** | **5** | **0** |
| ruff | All checks passed | — | — |

## New tests

7 in `test_gui_backend_integration_qualification.py`

## Regressions

None.

## Import smoke

Implicit via pytest collection (1519 tests).

## mypy

Not configured as gate in this repository.
