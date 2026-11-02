# P08 evidence and reproduction

Read `P08_IMPLEMENTATION_REPORT.md`, `G6_GATE.json`, `source_integrity.json`, `physics_parity.json`, `candidate-reaudit.json`, and the predecessor G5 closure report/decision. `artifact_hashes.json` seals this final repository state; verification does not re-run tests.

From the repository root, using its existing `.venv-remediation`:

```sh
.venv-remediation/bin/python docs/implementation/evidence/P08_2026-10-09/finalize_evidence.py --verify
.venv-remediation/bin/python -m pytest -q
node --test tests/js/*.test.cjs
.venv-remediation/bin/python -m ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools
.venv-remediation/bin/python -m mypy core physics numerics systems api
```

Optional native checks require explicit qualified runtime hashes, never auto-detection. `P07_NATIVE_CONFIG` must point to a **fresh** evidence-directory config for the original retain-fixture tests; do not reuse an existing directory or rewrite the immutable acceptance artifacts. `P08_NATIVE_CONFIG` names the qualified P08 runtime. Run `tests/integration_tests/geometry/` with both variables to execute all 58 native cases. Temp installation paths may disappear; resolve the pinned native prerequisites deliberately before attempting reproduction. No production native dependency was installed by P08.

Browser tools reuse isolated `/tmp/cosmos-p03.pfPm6s/node_modules` (Playwright 1.64.0, axe-core 4.14.0, TypeScript 6.0.3) and the installed Chrome. No production npm dependency. Start `tests/ui/app-shell/serve_fixture.py` with a new isolated state directory on 8811 (flag off for NGG), and `tests/ui/ngg/serve_fixture.py` with another new state directory, explicit `--runtime` config and `--port 8812`. Never use user application storage. Set `NODE_PATH` to the isolated modules and `COSMOS_P08_OUTPUT` to fresh temporary output before calling the Playwright CLI with `tests/ui/ngg/playwright.config.cjs`. That config writes to P08 evidence, so archive the existing final register first or create a separate reproduction overlay; do not mutate retained acceptance.

Strict display-interface contract check: TypeScript `--strict --noEmit --target ES2022 --module node16 --moduleResolution node16 --lib ES2022,DOM tests/ui/ngg/type_contracts.ts`. Runtime geometry/measurement remains server-side, not this declaration file.

Full tests have a known `cache/cea/test_key.json` timestamp side effect. Preserve/inspect that exact fixture and restore only the verified test-generated timestamp change. This run restored original bytes and retained the generated copy in `logs/`. `source_integrity.json` records preservation of unrelated dirty user work and unchanged historical P07 evidence.

Native bounds, fidelity and metrology remain sampled software checks. G6's verdict is local software qualification, not human UX/CAD acceptance, published engineering exports, native redistribution or physical validation.
