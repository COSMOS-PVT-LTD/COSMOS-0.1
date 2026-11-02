# P03 reproduction and test isolation

Production runtime dependencies: none added. Browser test tools are isolated from COSMOS's root dependency environment. `tooling/package.json` and `tooling/package-lock.json` pin the actual installed development tools and transitive integrity records: Playwright 1.64.0, axe-core 4.14.0, TypeScript 6.0.3 and PNGJS 7.0.0. PNGJS is used only to read calibration PNGs, not alter application imagery. Tool licenses remain in the isolated packages; this is not a production asset bundle.

Current scratch tool root: `/tmp/cosmos-p03.pfPm6s`. Recreate it in a fresh temporary directory with `npm ci --ignore-scripts --no-audit --no-fund` after copying the two lock files there. Do not install these into the COSMOS repository or global Node environment. Set `COSMOS_P03_TOOLS` to that directory when running the browser tools. Chromium was not downloaded; the config uses the existing `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.

In separate terminals from the repository root:

```sh
python3 -m http.server 8793 --bind 127.0.0.1 --directory .
.venv-remediation/bin/python tests/ui/design-system/serve_legacy.py /tmp/cosmos-p03-fresh-legacy-state
```

The second command serves the **actual** legacy application on localhost 8794 with disposable state, not user designs or the live localhost 8787 app. Its authentication fixture comes from the existing GUI test convention. Do not expose either server beyond localhost. The fixture performs login/context reads and opens the Requirements module; it does not create designs, run calculations or publish artifacts. New library tests do not use the legacy server.

```sh
node --test tests/js/*.test.cjs
.venv-remediation/bin/python gui/static/design-system/build_tokens.py --check
COSMOS_P03_TOOLS=/tmp/cosmos-p03.pfPm6s node /tmp/cosmos-p03.pfPm6s/node_modules/@playwright/test/cli.js test -c tests/ui/design-system/playwright.config.cjs
COSMOS_P03_TOOLS=/tmp/cosmos-p03.pfPm6s node tests/ui/design-system/calibrate_visual.cjs
node /tmp/cosmos-p03.pfPm6s/node_modules/typescript/bin/tsc --noEmit --strict --lib es2022,dom gui/static/design-system/components.d.ts tests/ui/design-system/type_contracts.ts
PYTHONPATH=. .venv-remediation/bin/python -m pytest --import-mode=importlib -q
.venv-remediation/bin/python -m ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools
.venv-remediation/bin/python -m mypy core physics numerics systems api
.venv-remediation/bin/python docs/implementation/evidence/P03_2026-10-08/check_scope.py
.venv-remediation/bin/python docs/implementation/evidence/P03_2026-10-08/finalize_evidence.py --verify
git diff --check
```

Do not pass `--update-snapshots` for regression acceptance. Creating goldens is a separately reviewed baseline operation. Other OS/browser versions require their own reviewed baselines rather than silently accepting new images. The legacy YIQ calibration applies only to this target-device baseline and does not relax scientific tolerances. Stop the isolated legacy server after testing. The standalone library preview can remain open for review.

The source checkpoint and prior phase records are historical evidence; never rerun a capture or old phase finalizer to erase failures or acceptance history. `finalize_evidence.py --verify` validates retained evidence hashes without claiming to rerun a browser or the Python test suite.
