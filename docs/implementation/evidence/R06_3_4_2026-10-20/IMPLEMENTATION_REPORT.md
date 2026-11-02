# R06.3 / R06.4 — selected-cycle implementation and qualification

2026-10-20. Parent approval: steady pressure-fed first, then open gas-generator. Entry HEAD `293223ebef190eaa647e67dc581eb186b2b5d987`; inherited dirty checkout retained. This report covers the selected **prescribed-component, steady design-point assessment**, not a full engine/network operating-point, hardware or release qualification. Final machine results are in `STATUS.json`, `test-summary.json`, `preservation.json` and `source-final.json`.

## Delivered implementation

| Boundary | Implementation and status |
|---|---|
| Physics | `physics/feed/gas_generator.py`: dimensional immutable pump/turbine contracts, source-backed work relations, explicit component efficiencies/total states, separate GG O/F, analytic GG mass/pump feedback, shaft loss/auxiliary power and independently evaluated turbine/shaft residuals. Infeasible feedback and explicit GG flow-limit violations refuse; no clipping or guessed component maps. |
| Systems | `systems/cycle/coupled.py`: strict versioned SI specification and exact baseline snapshot; actual retained injector, optional full-core-fuel series regenerative cooling and additional fuel-film routing; two liquid branch budgets, external withdrawals, separate core/GG/film/external mass ledger, cooling energy/pressure checks, GG hot-gas energy and power closure. |
| Core performance adapter | Retains actual assumed-state **or CEA** core nozzle outputs. Checks cycle/Pc/O/F/propellant and exact injector/performance/CEA source identities. CEA is neither rerun with perfect-gas assumptions nor substituted on failure. The new adapter does not retroactively change R06.2a's narrower old adapter. |
| Persistence | `systems/projects/cycle_assessment.py` reuses the existing downstream R05 capture protocol. Minimal configuration hooks in `systems/projects/pressure_fed.py` preserve its old defaults. Separate domains `coupled-cycle-inputs` and `coupled-cycle-assessment`; no new SQL schema, root migration or dependency. Input-first capture, CAS, actor-scoped idempotency, interruption recovery, failures without calculated answers and baseline/method currentness remain explicit. |
| API | `api/cycle_assessment.py`, `api/cycle_projects.py`, composition in `api/project_authority.py` and `api/context_projects.py`. Authenticated `/api/projects/{project}/cycle-assessments`: capabilities, paginated records/captures, explicit create/retry, exact committed inspection, original input/result JSON, signed raw residual CSV and source-bound plot data. Membership, reader, foreign-project, extra-field/query and flag-off restrictions are retained. |
| GUI | `gui/static/managed-cycle.js` / `.css`, composed in Projects and `gui/server.py`. Explicit no-numerical-default SI inputs, density/loss/efficiency/energy sources, cycle/cooling/film choices, draft and uncertain-command guards, paginated exact baselines/history/captures, retry, failure/UNBALANCED/BALANCED labels, current/historical identities, original source and residual downloads. No cycle equations in GUI. |
| Plots | Reuses local ECharts and `ScientificChart` / `CosmosPlotExports`. Additive managed-cycle source domain in `gui/static/visualization/chart.js` and chooser identity in `exports.js`. Signed normalized residual versus discrete ledger index, explicit ±1 algebraic bounds, exact raw values/units/tolerances, source identity, full CSV and SVG/provenance/source exports. Not a convergence plot or physical trajectory; no interpolation or uncertainty claim. |

## Model contract and finite scope

`EXECUTION_PLAN.md` pins primary sources, equations, station/enthalpy conventions, independent numerical constants and refusal/termination criteria before implementation. GG total inlet state and constant cp/gamma/net reaction energy are **user-supplied**, not predicted GG chemistry. Pump efficiencies/pressure rises are design-point assumptions, not hardware maps. The GG solution includes the pump power required for both GG propellants themselves. It is direct affine algebra with independently tested residuals, not an iterative solver; iterations0 and `DIRECT_AFFINE` are intentional.

Branch `core_loss` / `gg_loss` / external / film losses are explicitly supplied total-head-equivalent losses at applicable flows, including kinetic/elevation effects. No extra station velocity or implicit throttle coefficient is invented. Declared controls must consume pressure surplus; positive surplus is not automatically called closure. Pump-free feed explicitly requires null efficiency, identical source/discharge pressure and zero GG losses; shaft power is NOT_APPLICABLE, not an invented zero-power pump.

Series regenerative cooling consumes its actual pressure loss/heat pickup/outlet state and returns the **same full core fuel flow** to the injector. Coolant flow is not added to tank demand twice. Flow, density, inlet pressure, retained nozzle/thermal IDs, pressure drop and energy residuals must agree. Arbitrary partial-flow manifolds/recirculation and mixed coolant species are unsupported.

The actual retained gaseous-slot film mass estimate is an **additional fuel withdrawal** through the fuel pump/feed boundary. Film conditioning is an explicit externally imposed boundary; a phase-change heater/gas feed model is not claimed. Film-disabled cannot silently discard a retained nonzero film stream. Other withdrawals are explicit and separately budgeted.

The original core thrust/nozzle/CEA solution is preserved. Reported effective Isp is explicitly **core thrust divided by total propellant withdrawal**; no GG, film or external-stream exhaust thrust is guessed. Retained thermal/film outputs affect the coupled heat/pressure/mass ledger, but the frozen core combustion/nozzle is not recomputed with cooling heat loss. This one-way component-boundary model is not a bidirectional thermal/combustion fixed point.

## Frozen architecture and readiness

The assessment consumes saved performance/cooling **downstream** of the frozen stage graph. It does not introduce a back-edge into the upstream cycle stage, change existing equations, mutate any original source result, or promote its `NOT_IMPLEMENTED` flag. `workflow_cycle_complete=false` remains truthful. The new separate result explicitly reports `BALANCED_DECLARED_DESIGN_POINT` versus `UNBALANCED`; `usable_current_balanced_assessment` additionally requires current source/method identities and a completed receipt. A completed but unbalanced calculation is not a passing balance.

R06.3 is complete for the declared selected GG model; R06.4 passes its component-boundary software qualification. **Whole R06 / full engine-product closure is not implied.** Remaining broader items include RKT-01's wider sensitivity scope, pressurant sizing, component maps/speed, full network operating-point solution, phase-change conditioner and bidirectional core thermal/combustion feedback. Staged-combustion, expander and electric-pump were not selected and remain unsupported. Human/native-window accessibility, qualified hardware properties/maps, experiments and clean release/CI are separate gates, not fabricated evidence or excuses for missing software.

## Verification evidence

- Entry baseline:139 pressure-fed Physics/Systems/authority/HTTP tests passed before changes (`baseline.log`).
- Focused final:72 passed (`focused-final.log`, `focused.xml`), including49 new Physics/coupling/authority/HTTP cases and23 preceding authority/HTTP regressions. Independent predeclared GG fixture, feedback infeasibility, mass cap, efficiencies, thermal/branch mismatch, stale sources, source bytes, CEA, restart, input-first interruption, history, permissions and flag-off routes are covered.
- Initial full default environment `.venv-remediation`:3442 passed/95 skipped in188.80s. Comparing XML against the preceding campaign revealed that this environment lacks optional `jsonschema`; its module-level skips replace21 prior geometry-schema cases. No test source was removed. Final full run in the existing `.venv-release-p12` qualification environment: **3464 passed/93 skipped in186.01s** (`full-python-qualified.*`, `test-summary.json`). All3508 preceding test identities are retained, with49 new cases. Neither run's receipt is overwritten.
- JavaScript:413 passed, including form no-default/strict-unit/routing checks and a real Python managed-cycle payload accepted by the shared chart's provenance/budget checks. No fake simulation IDs.
- Ruff, Mypy394 production files and seven strict TypeScript consumer checks. Commands/profile versions are in `OPERATOR_RUNBOOK.md`; final receipts retained. Python full runs use exact copy/restore/byte-compare around the test-mutated CEA cache; no cache deletion or silent post-test source mutation.
- `preservation.json` compares the preceding source manifest; eight declared integration/generalization edits, with no changes to pre-existing Core/Physics/Numerics equations or prior scientific stage sources. Original evidence is not resealed.

## Actual GUI → API → retained data → exports

Verification skill story: choose an exact saved baseline and explicit synthetic component data in Projects → authenticated create → input-first durable capture → real Physics evaluation → immutable result/currentness → UI ledger/plot → exact original/CSV/SVG downloads → task-server restart and reinspection. QA root `/private/tmp/cosmos-r06_3_4-qa.yqztVH`, port8869. Only the actual existing subsystem baseline was seeded; no successful assessment was seeded. No live owner-data root or port8787 was changed.

Final balanced source:

- Project `9d0b0ca1-a723-40ff-944a-1bfcd18febbb`.
- Baseline `529a9bd8-9c5e-4933-879f-36af2953ce3b`.
- Object `29304057-f35a-512b-9104-061749e817f5`.
- Input capture `e2d37b82-7c18-4794-af23-5b2181c60a0d`.
- Assessment commit `b8c3197f-1803-4c11-82c4-4f69eff5daa0`.
- SHA256 `1613b2e71c09fb3709003d49c5b53fe8a834795990aaba8d30fcb55cc3bdc32c`.

`ui-export-proof.json` compares actual downloaded input/result bytes with retained authority,19 raw signed residuals,57 plotted points, every raw/normalized quantity and original baseline bytes. UI retains floating-point residuals instead of rounding them to fake zeros. `ui-final-balanced.png`, `ui-final-plot.png`, `ui-final.txt` and `ui-unbalanced.txt` record the actual narrow IAB presentation. The y-axis's long shared-chart label is clipped at this narrow size; its complete quantity/unit and definition remain in accessible text, table and exports. This is not full application/native accessibility acceptance.

Actual empty-baseline run refused. A deliberate +100J/kg GG reaction-energy mismatch produced a completed **UNBALANCED** record and `GG.energy · FAIL`, not a successful balance. Earlier pre-final-method assessment remains byte-retained and explicitly HISTORICAL (`ui-historical.txt`); it was not resealed. The final balanced original remains independent of this negative fixture. Separate SVG and CSV export controls were corrected after the actual first browser check found an imprecise combined label.

After a second full task-server process restart, the GUI reopened the same balanced commit/hash as CURRENT (`ui-restart.txt`), and its newly downloaded record is byte-identical to the final original. Actual exact-source navigation preserves project/commit/domain and shows both upstream baseline/captured-input dependencies (`ui-lineage.txt`). Captured browser console errors:0. Task-only server/tab were closed after recording; no material data was deleted.

No commit, push, GitHub CI/release, owner migration, credential/trust change, native Cocoa/human observation or hardware test is claimed. Synthetic numbers are software fixtures, not an engine design recommendation.
