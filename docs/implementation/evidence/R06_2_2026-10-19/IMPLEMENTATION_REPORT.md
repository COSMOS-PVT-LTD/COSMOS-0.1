# R06.2a - pressure-fed computational foundation

Date2026-10-19; parent authority is the recorded pressure-fed-first, then gas-generator approval. **This is a bounded calculation foundation, not complete R06.2/R06 or a GUI feature release.** Detailed preimplementation scientific contract: [MODEL_CONTRACT.md](MODEL_CONTRACT.md). Machine-readable final results: `STATUS.json` and `source-final.json` once final qualification succeeds.

## Implemented

- `physics/feed/pressure_fed.py`: typed Core Quantity pressure budget for a specified steady incompressible liquid flow, source/sink static pressure, kinetic/elevation changes and explicit irreversible losses; signed continuity residual; traceable ModelIdentity, admissibility and overflow/underflow refusal. No parallel unit system or new numerical solver. Sources mapped to exact DOE equations/pages; NASA feed-system topology checked using the PDF skill before implementation.
- `systems/cycle/pressure_fed.py`: strict explicit-SI/source/phase/operating-condition specification; captures the existing canonical baseline and consumes only its CURRENT operating-point, propellant, assumed-thermochemistry and performance results. Checks source/result/graph/Pc/O/F/identity consistency; reuses existing Physics bipropellant split. Independent tank withdrawals are tested against each core stream and total. Static injector delta-p defines the required manifold pressure and is not counted again as an upstream irreversible loss. Explicit diversion zeros required; nonzero diversion, unknown phase/regime, CEA and unsupported cycle architectures refused.
- `api/pressure_fed.py`: read-only in-process facade `assess_pressure_fed(design, specification)`. Detached CalculationResult plus conservative method-source hashes; after-load/during-call source drift refuses return. No HTTP route, permissions bypass, save, stage activation, owner inference or project migration. This API is developer-callable; there is **no new pressure-fed GUI control yet**.
- `tests/unit_tests/physics/test_pressure_fed.py` and `tests/unit_tests/systems_layer/test_pressure_fed_assessment.py`: independent constant fixtures, actual unchanged existing-model baseline, negative/domain/unit/source checks, immutable canonical-source/method lineage and nonmutation tests. Synthetic feed properties/pressures are labelled software fixtures, not measurements.

The existing canonical serializer uses16 significant decimal digits. Assessment deliberately consumes a detached reconstruction of the exact captured canonical text, not a higher-precision live object hidden behind a different hash. `source_results` are exact extractions from that consumed canonical baseline; original source IDs and complete canonical bytes/hash are retained. The serializer itself was not changed.

An actual fresh-process API example is retained in `example-baseline.json`, `example-input.json`, `example-result.json` and `example.log` (builder `example.py`). It runs the existing ideal model rather than seeding successful feed outputs, then uses explicitly synthetic feed assumptions. Core flow3.045330832294221kg/s; each supplied tank pressure5182000Pa balances the specified manifold/loss/head budget. Source design unchanged; still no cycle completion or physical validation. Final recorder verifies exact original baseline bytes, input equality and current method hashes. **These example pressures/properties are not defaults or hardware design recommendations.**

## Why not promote the cycle stage?

`systems/workflow/graph.py` places cycle **before** operating point/performance. This budget needs the latter's mass flow. Feeding it back into the upstream cycle would create a dependency cycle or silently alter the frozen workflow. The result is deliberately unattached (`stage_id=null`), with `workflow_cycle_complete=false`, while the graph and all old cycle implementation flags remain unchanged. A positive surplus at imposed flow is `SURPLUS_REQUIRES_CONTROL`, not a solved operating point or closed network.

Balance tolerances are caller-declared algebraic comparison thresholds, not uncertainty or hardware acceptance. Even a balanced assessment has scientific applicability UNKNOWN, physical validation NOT_PERFORMED, pressurant boundary only, shaft power NOT_APPLICABLE/null, and existing injector/cooling coupling NOT_ASSESSED. Current cooling/injector results remain unchanged and are not silently consumed. No full engine, cooling/film/GG stream, regulator, pressurant consumption/work, local cavitation, transient/two-phase or structural claim.

## Verification record

Baseline existing propulsion-subsystem tests27 passed. Physics-only independent reference52 passed before Systems integration. Final focused new+existing workflow121 passed (116 new cases). Import-isolation/API-catalog/new-assessment76 passed. Full default Python3392 passed/93 skipped in169.56s. JavaScript402 passed with no JS/GUI changes. Ruff and Mypy387 production files pass. Final whole-Python result is recorded in `full-qualified.xml`, `full-qualified.log`, `STATUS.json`; do not infer a pass from an earlier/interrupted run. Exact CEA cache restore/byte comparison completed successfully after the final process exited.

Earlier diagnostics are retained, not relabelled green:

- `physics-reference.log`: one test incorrectly expected a very small but still finite density to overflow; changed the synthetic extreme to an actually overflowing case without adding arbitrary physical density limits.
- `focused.log`: source exactness assertion initially compared a higher-precision live DTO with the canonical16-digit snapshot. Corrected the assertion to require exact consumed canonical-source equality; no serializer or equation change.
- `mypy-final.log`: static narrowing needed an explicit validated dictionary return; fixed and rechecked in `mypy-qualified.log`.
- `full-python.log/xml`: intentionally interrupted the first full run to finish that static correction before freezing the final candidate; not acceptance evidence. Final full suite uses separate `full-qualified.*`. Both use copy/restore/byte-compare EXIT traps for the test-mutated CEA cache. The interrupted pytest stash diagnostic is retained, not attributed to a production calculation.

Source-preservation gate: entry matches all906 preceding R06 sources. This slice adds six production/test source files and changes **none** of those906. Original inventory remains4888 unchanged/54 already-declared edits/0 unexpected/0 missing. `source-final.json` binds the final qualified source set, not a release or physical seal. No native-runtime/hardware campaign, browser/UI journey, remote CI, packaging, signing or clean-commit qualification was run for this API-only slice.

## Remaining / next

1. R06.2b: managed pressure-fed assessment input capture and original result retention under accepted R05 authority; exact same-project baseline commits, method-currentness, CAS/idempotency/restart/failure handling and retained comparison criteria. Do not publish this in-process API via an unauthenticated ad-hoc route.
2. Authenticated scoped HTTP and explicit draft-safe GUI inputs/results/source inspection, pressure/mass residual presentation and source-consistent exports; actual browser/native observation. No hidden loss/property/default values.
3. Resolve post-performance assessment versus upstream cycle dependency explicitly before any stage integration/promotion. Preserve the existing preliminary workflow; do not add a graph loop or claim complete cycle balance from imposed-flow algebra.
4. Couple actual injector/cooling/film/other diverted or recirculated streams with compatible source conditions; no unknown-to-zero substitution. Separately qualify CEA baselines. Regulator/pressurant modelling requires its own explicit scientific boundary.
5. Then selected R06.3 gas-generator pump/turbine/diversion/power closure and independent reference fixtures. Staged-combustion, expander and electric-pump remain unsupported. Remaining R06.1 CEA/global/long-job/native scope is separately open.

No live owner-data migration/root switch, dependency installation, credentials/trust change, old evidence reseal, memory write, commit/push/release or physical action. Usage remained allowed when checked; no reached-limit pause claimed. All inherited dirty work is preserved.
