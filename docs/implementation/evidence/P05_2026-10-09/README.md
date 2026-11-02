# P05 evidence and reproduction

Start with `P05_IMPLEMENTATION_REPORT.md`, `G4_GATE.json`, `physics_parity.json` and `source_integrity.json`. `artifact_hashes.json` seals code, contracts, tests, screenshots, logs and this report. `--verify` rechecks evidence, not test execution.

From `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`:

```sh
.venv-remediation/bin/python docs/implementation/evidence/P05_2026-10-09/finalize_evidence.py --verify
.venv-remediation/bin/python docs/implementation/evidence/P05_2026-10-09/physics_parity.py
.venv-remediation/bin/python -m pytest -q
node --test tests/js/*.test.cjs
.venv-remediation/bin/python -m ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools
.venv-remediation/bin/python -m mypy core physics numerics systems api
```

Browser tools reuse P03's isolated `/tmp/cosmos-p03.pfPm6s/node_modules`: Playwright 1.64.0, axe-core 4.14.0, TypeScript 6.0.3 and installed Chrome 154.0.8037.98. No new production npm dependency. Temporary path may disappear; do not silently upgrade evidence tools. Final logs are retained here and require no temporary directory to inspect.

Browser execution uses `tests/ui/rocket-workbench/playwright.config.cjs` (P05 suite) and `p04-compatibility.config.cjs` (mechanically copied P04 scenarios, new ports/output paths only). Start `tests/ui/app-shell/serve_fixture.py` with fresh temporary storage on 8797 modern/8798 `--legacy`, and 8799 modern/8800 `--legacy` for the independent predecessor suite. Do not point fixture servers at user project storage. Set `NODE_PATH` to the isolated modules and `COSMOS_P05_OUTPUT` to a new temporary output directory before running the Playwright CLI. Browser specs deliberately produce **new P05** artifacts, never rewrite P04's evidence.

The full suite refreshes only `cache/cea/test_key.json`'s known test-created timestamp. Its generated copy is retained here; the original fixture bytes were restored and checked against the pre-P05 SHA256, without overwriting unrelated work. Rechecks may recreate that side effect.

Run `capture_before.cjs` only before production changes in a fresh baseline checkout; it is not an after-the-fact source for baseline images. Scientific `capture` similarly refuses to overwrite a captured baseline. Full report explains random identity metadata exclusions. Source checkpoint and predecessor seals ensure that dirty user work and earlier phase evidence were preserved.
