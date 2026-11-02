# P04 evidence and reproduction

Start with `P04_IMPLEMENTATION_REPORT.md`, `G3_GATE.json`, `source_integrity.json` and `artifact_hashes.json`. Rollout/rollback: `gui/static/app-shell/README.md`.

## Final verification summary

| Check | Result | Retained artifact |
| --- | --- | --- |
| Full Python suite | 2,265 passed; 5 skipped | `logs/pytest-final.log`, `logs/pytest-final.xml` |
| P04 Python flags/HTTP/roles | 31 passed | `logs/python-focused-final.log` |
| Existing propulsion workflow, flag on | 3 passed | `logs/scientific-flag-on.log` |
| All JS tests | 84 passed | `logs/js-full-final.log` |
| P04 browser scenarios | 26 passed | `browser-tests.json`, `logs/browser-final.log` |
| P03 legacy screenshot regression | 12 passed | `logs/legacy-visual-regression.log` |
| P03 component screenshots | 19 passed | `logs/component-visual-regression.log` |
| Ruff / Mypy / strict TS contracts | PASS / 318 files / PASS | Corresponding final logs |
| New-shell dark/high-contrast axe scope | 0 violations; flagged table cells reviewed separately | `accessibility-*.json`, `accessibility-contrast-review.json` |
| Source/old-evidence/diff checks | PASS | `source_integrity.json`, retained verification logs |

## Commands

Run from the repository root with the existing `.venv-remediation`. The Node browser dependencies were isolated under a temporary directory using the already-retained P03 lockfile; no repository runtime dependency was added. Replace `P04_OUTPUT` with a fresh temporary directory and `P03_TOOLS` with an isolated installed tool directory. These are placeholders, not shell variables already set on the user's machine.

```sh
.venv-remediation/bin/python -m pytest -q --disable-warnings --junitxml=P04_OUTPUT/pytest.xml
.venv-remediation/bin/python -m pytest tests/unit_tests/gui/test_app_shell.py tests/integration_tests/gui/test_app_shell_http.py -q
COSMOS_NEW_SHELL=1 .venv-remediation/bin/python -m pytest tests/integration_tests/gui/test_propulsion_e2e_http.py -q
node --test tests/js/*.test.cjs
.venv-remediation/bin/python -m ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools
.venv-remediation/bin/python -m mypy core physics numerics systems api
node P03_TOOLS/node_modules/typescript/bin/tsc --strict --noEmit --target ES2022 --module node16 --moduleResolution node16 --lib ES2022,DOM tests/ui/app-shell/type_contracts.ts
.venv-remediation/bin/python docs/implementation/evidence/P04_2026-10-09/check_scope.py
.venv-remediation/bin/python docs/implementation/evidence/P03_2026-10-08/finalize_evidence.py --verify
git diff --check
```

For the browser suite, run fixture servers in separate terminals, with temporary state directories only:

```sh
.venv-remediation/bin/python tests/ui/app-shell/serve_fixture.py P04_OUTPUT/modern-state --port 8795
.venv-remediation/bin/python tests/ui/app-shell/serve_fixture.py P04_OUTPUT/legacy-state --port 8796 --legacy
NODE_PATH=P03_TOOLS/node_modules COSMOS_P04_OUTPUT=P04_OUTPUT node P03_TOOLS/node_modules/@playwright/test/cli.js test --config tests/ui/app-shell/playwright.config.cjs
```

The fixture uses real application/auth/design APIs and seeds two clearly named temporary designs. Mock transport/job/save failures are restricted to individual browser tests. Nothing in those fixtures is physical validation. The config records its latest result into this phase's evidence folder; retain the original immutable register before reproducing a release.

To recheck the retained P03 screenshot baselines without rewriting P03 reports/metrics:

```sh
.venv-remediation/bin/python tests/ui/design-system/serve_legacy.py P04_OUTPUT/p03-legacy-state
.venv-remediation/bin/python tests/ui/app-shell/serve_components.py
NODE_PATH=P03_TOOLS/node_modules COSMOS_P03_TOOLS=P03_TOOLS node P03_TOOLS/node_modules/@playwright/test/cli.js test --config tests/ui/design-system/playwright.config.cjs --reporter=list --output=P04_OUTPUT/legacy-output --grep 'actual legacy workbench baseline'
NODE_PATH=P03_TOOLS/node_modules COSMOS_P03_TOOLS=P03_TOOLS node P03_TOOLS/node_modules/@playwright/test/cli.js test --config tests/ui/design-system/playwright.config.cjs --reporter=list --output=P04_OUTPUT/component-output --grep 'visual baseline'
```

Do not use snapshot-update mode. The prior component baseline retains zero pixel allowance/threshold; the legacy threshold remains its already-calibrated P03 value of 0.0425 with zero pixel-count allowance. This is a display-regression setting, not a scientific tolerance.

The full Python suite has a known tracked cache timestamp side effect. Before a rerun, preserve that exact fixture, inspect the resulting diff, and recover only a verified test-generated timestamp change. Do not overwrite unrelated local edits. `check_scope.py` detects unapproved changes.

Final evidence build/verify:

```sh
.venv-remediation/bin/python docs/implementation/evidence/P04_2026-10-09/finalize_evidence.py --output P04_OUTPUT
.venv-remediation/bin/python docs/implementation/evidence/P04_2026-10-09/finalize_evidence.py --verify
```

All detailed results are scoped to the local Mac/browser environment recorded in `G3_GATE.json`. No GitHub CI execution, packaged native build, publishing or engineering/hardware certification is claimed.
