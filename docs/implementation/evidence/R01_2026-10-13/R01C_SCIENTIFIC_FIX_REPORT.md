# R01C — scientific correctness fixes

Date: 2026-10-13, Asia/Kolkata. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

**Status: focused correctness fixes PASS.** This work closes the three concrete scientific defects SCI-01/02/03 in `docs/implementation/COMPLETION_BACKLOG_2026-10-13.md`. It does not complete the broader scientific/platform backlog or authorize production/physical acceptance.

## Changes

1. **Assumed-state validation:** Operating Point and Thermochemistry validate explicit/effective chamber temperature and molar mass as finite positive real scalars, and gamma against the existing Physics envelope `1 < gamma <= 3`. Booleans are not direct scalar assumptions. Existing Core/Physics validation owns these rules; no equations or new empirical bounds were added. Both stages use a local candidate and commit only checked data while preserving the live OperatingPoint object identity. Invalid inputs produce the existing typed FAILED result and downstream invalidation, without partially applying earlier valid overrides. CEA failure continues to clear previously derived thermochemical/performance state rather than silently reuse it; actual valid CEA execution remains supported.
2. **Defensive canonical projections:** outbound and inbound `CalculationResult`, `PropulsionDesign` and nested `DesignChangeEvent` canonical dictionaries are detached deep copies. Editing nested result inputs/outputs, subsystem slots/configuration, history or event values cannot mutate authoritative live state through these serialization boundaries. Schema fields/order/result IDs and valid canonical values are unchanged. This does **not** freeze every live Python object or add signed publication/durable engineering acceptance; those are separate backlog items.
3. **MOC relation finite-angle check:** existing `validate_flow_angle` is invoked before calculating characteristic invariants. NaN/Inf yield `InvalidInputError`; finite invariant relations are unchanged. MOC contour generation is still explicitly unsupported.

Production files changed:

- `systems/stages/operating_point.py`
- `systems/stages/thermochemistry.py`
- `systems/contracts/results.py`
- `systems/projects/models.py`
- `physics/compressible_flow/moc_nozzle.py`

Tests added/extended:

- `tests/unit_tests/systems_layer/test_r01_scientific_hardening.py`
- `tests/integration_tests/gui/test_r01_assumed_thermo_http.py`
- `tests/unit_tests/physics/test_compressible_flow.py`

No production GUI/API, scientific equations/defaults, optional cycle/MOC solver, dependencies, Git history, remote or prior phase evidence was changed by this workstream. Existing user source changes were preserved.

## Verification

Commands use `.venv-release-p12/bin/python`; Python test runs set `PYTHONDONTWRITEBYTECODE=1`. New test fixtures are in memory or pytest private temporary directories, not user engineering storage. HTTP tests bind their own ephemeral localhost ports and stop their own servers.

| Evidence | Executed result | Scope |
| --- | --- | --- |
| `R01C-baseline.xml` / `.log` | **44 passed** | Existing result/domain/compressible/phase3/CEA workflow fixtures before production changes. |
| `R01C-red.xml` / `.log` | **64 failed, 8 passed, 22 deselected** | Deliberately executed new negatives/projection tests plus MOC selection before the fix; retained proof of regression sensitivity, not a final failure. |
| `R01C-focused.xml` / `.log` | **121 passed** | Previous 44 fixtures plus 77 new tests, including six actual HTTP persistence/export negatives. |
| `R01C-regression.xml` / `.log` | **549 passed** | Physics + Systems unit tests, propulsion/CEA/subsystem API, NASA CEA adapter, Systems integration and new isolated HTTP tests. Includes focused tests; do not add counts as unique coverage. |
| `R01C-ruff.log` | **PASS** | Five owned production files and three test files. |
| `R01C-mypy.log` | **PASS, five source files** | Scoped typing, not full repository/GUI qualification. |

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv-release-p12/bin/python -m pytest -q tests/unit_tests/systems_layer/test_r01_scientific_hardening.py tests/unit_tests/systems_layer/test_contracts.py tests/unit_tests/systems_layer/test_domain_models.py tests/unit_tests/physics/test_compressible_flow.py tests/integration_tests/systems_layer/test_phase3_chain.py tests/unit_tests/api/test_cea_workflow.py tests/integration_tests/gui/test_r01_assumed_thermo_http.py
```

Broader command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv-release-p12/bin/python -m pytest -q tests/unit_tests/physics tests/unit_tests/systems_layer tests/unit_tests/api/test_propulsion_workflow.py tests/unit_tests/api/test_cea_workflow.py tests/unit_tests/api/test_subsystem_workflow.py tests/unit_tests/plugins/test_nasa_cea_engine.py tests/integration_tests/systems_layer tests/integration_tests/gui/test_r01_assumed_thermo_http.py
```

New regressions cover zero/negative/nonfinite/Boolean assumptions, valid gamma upper boundary, invalid restored values, no external-engine dispatch for invalid manual overrides, no partial accepted-state mutation, downstream current-answer refusal, nested export/restore aliases and MOC finite-angle rejection. Existing successful assumed chains and real NASA CEA regression fixtures passed (including methane/LOX chamber temperature approximately 3093.338 K, ideal c-star/thrust scaling, native failure clearing and persistence/invalidation). These analytical/reference fixtures are numerical/software evidence, not experimental/hot-fire proof or a universal zero-error guarantee.

## Remaining scope

Full-suite/native/UI/release integration checks and preservation of the overall multi-agent R01 candidate are coordinator-owned. Production/G9, durable signed engineering publication, complete cycle/engine CAD/CAE/report integration and physical readiness remain separately gated. No commit or push was performed.
