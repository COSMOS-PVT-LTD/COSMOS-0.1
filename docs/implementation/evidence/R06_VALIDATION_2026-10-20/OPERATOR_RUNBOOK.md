# Prepare a propulsion validation record

Use the existing configured app-data root and normal Mac launcher. Restart normally to load updated sources; do not kill an unidentified port listener, enable a different live root or migrate owner data just to see this feature. The panel belongs to the existing managed Projects workflow; flag-off mode is read-only. Existing source fixtures are not automatically migrated.

1. Open **Projects & Mission**, select your managed project, and expand **Propulsion experimental-validation preparation — measurements required**.
2. Select an exact saved current propulsion baseline and supported target. The target's producing stages must be current and applicable; no out-of-range source is accepted. Cooling targets are limited to the actual existing divergent-nozzle model.
3. Click **Preview exact prediction and build empty criteria fields**. This displays model output/context, not measurements, and creates blank criteria fields. A preview is not a saved plan.
4. With the responsible qualified reviewer, document intended use/applicability, explicit SI discrepancy and uncertainty limits, coverage factor/correlation and numeric context/property tolerances. Supply sourced prediction standard uncertainty and basis, or explicitly UNKNOWN. UNKNOWN blocks a passing software comparison; do not enter zero merely to remove a blocker. No QA fixture values are recommended for an engine.
5. Save the predeclared plan **before** importing/evaluating measurements. Inspect exact commit/hash and upstream baseline. Download **EMPTY measurement CSV template** and **empty provenance checklist JSON**. With no real data available, stop here: AWAITING_MEASUREMENTS is the correct state.
6. Later, preserve authentic raw originals and have the measurement provider/reviewer populate the exact SI rows and positive standard uncertainties; identity rows use exact identity and blank uncertainty. Supply all provenance fields: kind, source, author, version, license, instrumentation, calibration record, uncertainty basis, offset-aware acquisition timestamp, calibration usage and criteria-predefinition basis. Source assertions/checksums alone do not prove authenticity or held-out independence. This software is not a hazardous-test procedure.
7. Open the saved plan and **Import actual measurements later — no data is generated**. Paste the CSV and provenance JSON explicitly. The parser refuses empty templates, missing/duplicate/extra rows, nonfinite values, wrong units and absent uncertainties. Use the retained exact command identity for uncertain network retries; do not invent new inputs or duplicate operations.
8. Create a software comparison from the exact retained plan and measurement commits. Inspect every mismatch, signed error, uncertainty and blocker. A numeric pass does not complete independent review, the uncertainty budget, physical validation, production/hardware/flight acceptance or R06.
9. For a changed candidate/criteria, save a new explicit plan. Historical originals remain readable; CURRENT is source/method freshness, not validation. Do not tune criteria after seeing results and represent that as predeclared independent validation.

## Supported data envelope

- Exact CSV header: `kind,name,value,unit,standard_uncertainty`. Explicit SI units exactly as emitted; no conversion, interpolation or resampling. Maximum 1 MiB, 128 complete rows.
- Targets: thrust [N], core mass flow [kg/s], core specific impulse [s], coolant outlet temperature [K], coolant pressure loss [Pa], coolant heat pickup [W], divergent-nozzle peak hot-wall temperature [K]. UI selects one per plan; API supports a bounded multiple-target plan.
- Numeric context/property rows require reported positive standard uncertainty. These contributions are retained but **not** propagated into a complete model-output uncertainty budget by this increment.
- `experimental`/`published-experimental`/`synthetic` and `held-out`/`calibration`/`not-applicable` are explicit provenance declarations. Authenticity/applicability/qualified acceptance remain external review tasks, never POSTed success flags.

## Reproduce software checks

From `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`:

```sh
.venv-release-p12/bin/python -m pytest -q tests/unit_tests/validation/test_propulsion.py tests/unit_tests/infrastructure/test_propulsion_validation.py tests/integration_tests/gui/test_propulsion_validation_http.py tests/integration_tests/gui/test_coupled_cycle_http.py
node --test tests/js/propulsion_validation.test.cjs
```

Full checks: `.venv-release-p12/bin/python -m pytest -q`, `node --test tests/js/*.test.cjs`, Ruff over CI targets and `scripts/collect_r06_validation_evidence.py`, Mypy over existing CI targets (397 files). Full Python tests intentionally mutate `cache/cea/test_key.json`; first copy to a fresh `mktemp` path, use an EXIT trap to restore the original bytes, and verify with `cmp`. Never discard owner cache content or replace it with a generated empty fixture.

Existing TypeScript5.9.3 executable: `/Users/vaibhavkumarn/.npm/_npx/69f9afb961c37556/node_modules/typescript/bin/tsc`; `--noEmit --strict --target ES2022 --module commonjs --moduleResolution node --lib ES2022,DOM`, all seven existing `tests/ui/` consumers. No new dependency installation needed.

Real browser qualification reused `tests/ui/r06_3_4/preview.py` with fresh guarded root `/private/tmp/cosmos-r06_3_4-qa.validation.mSMXgA`, port8871; `--resume` for restart. `tests/ui/r06_validation/check_plan.py` verifies GUI downloads and absence of data/assessment records against that isolated authority. This root/downloads are retained, preview server/tab are closed. Do not use this test account/root as owner or hardware evidence. The new collector writes only `R06_VALIDATION_2026-10-20/` receipts and compares the preceding R06.3/4 source/test manifests; it does not rewrite earlier receipts.
