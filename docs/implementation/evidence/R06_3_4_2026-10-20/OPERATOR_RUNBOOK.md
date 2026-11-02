# Selected-cycle assessment operation and local verification

## Use in COSMOS on the Mac

Use the existing application's configured data root and managed-project setting; do not switch roots or migrate data just to view this feature. Restart the existing app through its normal launcher after source updates. Do not kill an unidentified process using its port.

1. Open **Projects & Mission** and select your managed project.
2. Save a baseline with the explicitly selected **PRESSURE_FED** or **GAS_GENERATOR** cycle. Run the existing core calculation and injector stage. For included cooling/film, also run the actual nozzle/thermal/cooling stages.
3. Expand **Coupled pressure-fed / gas-generator design-point assessment**.
4. Select the exact saved baseline, cycle, cooling routing and film boundary. Enter all explicit SI inputs, source/assumption annotations and algebraic tolerances. No numerical defaults or automatic property maps are supplied. The form's branch losses use the total-head-equivalent convention described beside the controls.
5. For pressure-fed, source/discharge pressures are identical, pump efficiency is not applicable and GG losses are explicitly zero. For GG, supply pump efficiencies and gas total states/common-reference energy assumptions. The GG temperature/cp/energy source must describe a consistent state; the software does not infer combustion properties.
6. Series cooling is full core fuel returned to the injector. Match its retained inlet pressure to fuel discharge, density to the same fuel assumption and coolant flow to core fuel. Film requires the retained gaseous-slot model and an explicit externally conditioned fuel boundary; it is not a phase-change calculator.
7. Run and inspect the receipt. COMPLETED is execution, BALANCED/UNBALANCED is the declared algebraic check, CURRENT/HISTORICAL is source freshness, and physical validation is NOT_PERFORMED. None means hardware or workflow-stage acceptance.
8. Inspect exact source/upstream IDs and download original input/result JSON, raw residual CSV and optional source-bound SVG/plot CSV with provenance. The plot is a discrete normalized ledger, not convergence history.

If an operation's network response is uncertain, keep its original identity. Use the retained input capture to retry the exact original command; do not post guessed new defaults. Explicitly discard/abandon local drafts before changing context. Corrected engineering inputs require a new explicit command. Failed calculations retain their input originals but have no numerical export.

## Reproduce focused checks

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
.venv-remediation/bin/python -m pytest -q tests/unit_tests/physics/test_gas_generator.py tests/unit_tests/systems_layer/test_coupled_cycle.py tests/unit_tests/infrastructure/test_managed_cycle.py tests/integration_tests/gui/test_coupled_cycle_http.py tests/unit_tests/infrastructure/test_managed_pressure_fed.py tests/integration_tests/gui/test_pressure_fed_projects_http.py
node --test tests/js/managed_cycle.test.cjs tests/js/cycle_plot.test.cjs tests/js/scientific_chart.test.cjs tests/js/visualization_exports.test.cjs
```

Full qualification uses `.venv-release-p12/bin/python -m pytest -q`, which includes the already-installed independent `jsonschema` fixtures. Protect `cache/cea/test_key.json` with an exact temporary copy, EXIT-trap restore and byte comparison; tests intentionally mutate that cache. `.venv-remediation` full tests also passed, but its optional geometry-schema dependency was absent and its skip count is different. No dependency installation was needed.

Static commands: Ruff across the existing CI production/test targets plus the new evidence collector; Mypy over the existing CI target set (394 files); existing TypeScript5.9.3 at `/Users/vaibhavkumarn/.npm/_npx/69f9afb961c37556/node_modules/typescript/bin/tsc`, `--noEmit --strict --target ES2022 --module commonjs --moduleResolution node --lib ES2022,DOM`, all seven `tests/ui/` consumer files. No type-error suppression or tolerance relaxation.

Actual browser QA used `tests/ui/r06_3_4/preview.py --root /private/tmp/cosmos-r06_3_4-qa.yqztVH --port 8869`, with explicit `--resume` for restart. Only a fresh task-owned root is admitted. It contains synthetic QA accounts, subsystem baselines and explicit fixture assumptions, not owner project data. Preview does not seed successful cycle results. `tests/ui/r06_3_4/check_exports.py` checks downloaded originals/CSV/plot against retained authority; `scripts/collect_r06_cycle_evidence.py` binds final sources, preservation and test XML. Preserve prior receipts; do not reuse an old proof as a fresh run.
