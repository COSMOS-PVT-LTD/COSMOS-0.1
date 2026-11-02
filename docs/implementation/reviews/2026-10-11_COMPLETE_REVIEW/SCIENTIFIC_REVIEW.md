# Scientific engineering implementation review — 2026-10-11

## Decision

**Not everything in the frozen architecture or complete modernization specification is implemented.** The repository contains a substantial preliminary propulsion/numerics/knowledge foundation and a genuine native-geometry-to-simulation-to-comparison-to-report software qualification journey. The modern geometry, simulation, comparison and report journey is nevertheless a deliberately constrained **synthetic-sphere research preview**, not an arbitrary rocket-engine CAD/CAE workflow.

This is a current-source review of `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`. Source paths and one-based line numbers below were inspected on 2026-10-11. Main-review evidence supplies the current Git SHA/dirty-tree identity and refreshed test results. No production code, models, defaults, dependencies, existing evidence, cached calculations or user engineering records were modified by this scientific reviewer. Only this report was added. Two small in-memory reproduction commands were executed with `PYTHONDONTWRITEBYTECODE=1`; no native fixtures, CEA execution/cache writes or engineering store writes were performed.

### Meaning of status

- **Implemented:** executable code exists for the stated limited operation; this does not mean independently qualified for an actual engine.
- **Partial:** an executable subset exists, but the broader capability/specification is not satisfied.
- **Deferred / not implemented:** explicit nonoperational slot or rejection exists.
- **Unverified in this review:** implementation/test evidence exists but the scientific reviewer did not execute that environment-dependent path anew.

The active P00–P12 prompts repeatedly call for the smallest independently testable vertical slice. Passing a slice gate must not be interpreted as completing every requirement in the broader workbench/specification documents.

## Findings requiring attention

### SCI-01 — Critical completeness gap: engineering design does not feed general NGG or CAE

**Priority: high next-development priority; not a newly discovered false-validation escalation.**

The native UI service explicitly does not read/write engineering `DesignStore` state (`systems/geometry/workbench.py:1-4`). It accepts only operation/backend/voxel settings and fixed 10 mm synthetic spheres/Boolean combinations (`systems/geometry/workbench.py:76-87`). `systems/geometry/software_fixtures.py:27-58` hard-codes the radius, fixed separation/placements and `p07-software-fixtures` project identity. Native adapters do support actual primitive/Boolean operations, but their qualified UI acceptance policy is not a general design policy (`plugins/geometry/adapters.py:52-68`; `systems/geometry/qa.py:56-63`).

Simulation attachment requires the OCCT `sphere` operation (`simulation/workbench.py:92-103`). The handoff requires a centered radius of exactly 0.01 m, world frame, analytic OCCT STEP and one exact outer-shell selection (`simulation/contracts.py:35-55`). The only study model is `steady-spherical-conduction-v1`; other models fail with `UNSUPPORTED_MODEL`, explicitly stating that CFD/FEA/engine thermal models are not qualified (`simulation/contracts.py:58-70`). The mesh is a 1D radial analytic symmetry reduction, not a volume mesh generated from an arbitrary engineering solid (`simulation/workbench.py:31-44`).

**Impact:** an engine designed in Rocket Engine cannot currently be turned into qualified chamber/nozzle/injector/cooling-channel solids and then run through engine CFD, structural FEA or coupled cooling analysis in these modern workbenches. A sphere benchmark proving process boundaries and numerical semantics is valuable, but it is not that product workflow.

**Requirement basis:** modernization NGG purpose and backend contract (`specs/03_NGG_SYSTEM_ARCHITECTURE.md`); NGG feature-tree/parametric-graph scope (`workbenches/02_NGG.md`); physical model/mesh/boundary/field scope (`workbenches/03_SIMULATION.md`); simulation handoff ladder (`specs/05_GEOMETRY_QA_AND_VV.md`).

**Follow-up:** preserve the qualified fixture journey. Add a separately reviewed engineering-snapshot adapter, engine feature templates, critical-feature-specific acceptance criteria, boundary/material mapping, general meshing and qualified model adapters. Do not silently enable arbitrary geometries under the sphere acceptance policy.

### SCI-02 — Cycle power balance and full subsystem coupling remain absent

All pressure-fed, gas-generator, staged-combustion, expander, electric-pump and unspecified cycle types map to `NOT_IMPLEMENTED` (`systems/cycle/models.py:27-34`). Operating-point construction explicitly bypasses cycle analysis only for preliminary calculations (`systems/workflow/graph.py:26-33,60`).

The implemented cooling model states that coolant/film flows are explicitly specified and are **not deducted from Performance**; cycle, mixture and heat-loss coupling remain open (`systems/stages/subsystems.py:281-290`). Regenerative pressure drop and heat pickup are explicitly not a closed cycle balance (`physics/heat_transfer/regenerative.py:68-72`). Injector mass splitting is core flow with no cycle/film diversion (`physics/injectors/orifice.py:60-69`).

**Impact:** current subsystem numbers cannot be taken as a mass-, energy- and power-balanced complete engine design. Turbopump/preburner/turbine/feed pressure budgets, diverted flows and coupled cycle closure are not present in the inspected cycle implementation. This is honestly surfaced by the workflow notes and design review.

### SCI-03 — P2 correctness defect: impossible assumed thermochemistry can be CURRENT

`systems/stages/operating_point.py:51-60` copies assumed Tc/gamma/MW without validating the thermodynamic envelope. It stores `CURRENT` at lines 71-95. `systems/stages/thermochemistry.py:54-61,170-198` similarly accepts an assumed state based on presence/assumption flags and records it as `CURRENT` without requiring `1 < gamma <= 3`, positive molar mass and physically valid temperature.

**In-memory reproduction (public API, no persisted design):** create a design; set Pc=3,000,000 Pa, thrust=1,000 N, ambient pressure=101,325 Pa, O/F=2.5, expansion ratio=10; select LOX/RP-1; invoke `api.propulsion_workflow.run_phase3` with Tc=3500 K, gamma=0.5, MW=0.025 kg/mol, throat area=0.001 m² and expansion ratio=10.

Observed:

```text
operating_point = CURRENT
thermochemistry = CURRENT
thermochemistry.outputs.gamma = {value: 0.5, unit: 1}
performance = FAILED
performance diagnostic = gamma must satisfy 1 < gamma <= 3. Received 0.5.
```

Performance's physics port correctly rejects the impossible gamma, so this does **not** produce a false completed engine. However, the independently displayable upstream current-answer contract accepts invalid scientific assumptions and can show them as a current thermochemistry result. The NASA CEA interface has stronger output range checks (`physics/thermochemistry/cea_interface.py:124-150`); the assumed-state path needs equivalent appropriate guards and negative tests.

**Recommended fix, not implemented:** reject invalid assumptions before changing the operating point or publishing an envelope. Test finite/nonfinite, nonpositive MW/Tc and gamma boundary violations through both direct stage/API and HTTP paths. Keep draft-input capture distinct from executable/current thermochemical state.

### SCI-04 — Full durable engineering history and signed review are not implemented for the modern journey

Geometry revisions/jobs (`systems/geometry/workbench.py:49-55,89-95`), simulation studies/runs (`simulation/workbench.py:61-81`), comparison datasets/policies/reports/reviews (`validation/workbench.py:27-55`) and modern reports (`validation/reporting.py:27-49`) reside in bounded process-memory sessions. Modern report context explicitly tells users to download before restart. These dictionaries are not a versioned engineering persistence service.

`GeometryBuildService.export` deliberately raises `NOT_PUBLISHED` because trusted engineering review/publication is not implemented (`systems/geometry/service.py:112-113`). Comparison/report reviews are notes of intent and cannot grant independent acceptance or production handoff (`validation/workbench.py:161-169`; `validation/reporting.py:126-134`).

The existing propulsion store does persist designs and their result history (`systems/persistence/design_store.py:33-50`; `systems/workflow/state.py:30-32,44-50,76-85`). This is useful reuse, not proof of restart-safe NGG/CAE history. A downloaded deterministic report is an immutable offline snapshot; it cannot restore an active study/worker/session on its own.

**Requirement basis:** GOV-003 immutable publication; data-contract invariants that old revisions/artifacts survive; report history/signoff scope. **Follow-up:** additive durable artifact/history storage plus authenticated reviewer authority/signatures and lifecycle rules, without conflating a review note with acceptance.

### SCI-05 — P10 external comparison is narrow; full validation budget is not implemented

Thermal datasets are only temperature in K/degC versus radius in m/mm for the fixed isotropic spherical-conduction model (`validation/contracts.py:38-70`). Comparisons require identical SI operating-condition dictionaries and already-matching coordinates; no explicit resampling/interpolation workflow is supplied (`validation/comparison.py:14-24`). STEP import accepts only a trusted centered analytic 10 mm sphere (`validation/workbench.py:222-245`). Cross-kernel comparison uses volume/centroid discrepancies and retained sampled distances to a common analytic reference, not general pairwise surfaces or a certified Hausdorff metric (`validation/workbench.py:194-217`).

The implemented uncertainty formula combines reported output standard uncertainties with an explicitly supplied correlation. It does not propagate uncertain inputs/material properties/geometry/model discrepancy/numerical contributions (`validation/comparison.py:28-55`). Independent reference identity is a declared source SHA, not cryptographic proof of independence/authorship. The software correctly flags this limitation and always leaves independent acceptance/production false.

**Impact:** full arbitrary CAD/CAE import, benchmark selection, mesh-refinement comparison workflows, generalized dataset alignment, complete uncertainty/sensitivity budgets and authenticated experimental evaluation remain partial. Import schemas and pending-review infrastructure are implemented; authentic engine measurements are not created by these schemas.

### SCI-06 — Modern engineering reports do not cover Rocket Engine calculations

`EngineeringReports.create` requires a current P09-backed P10 **thermal** receipt (`validation/reporting.py:55-58`) and fixes report project/scope to steady spherical research evidence (`validation/reporting.py:73-92`). It produces deterministic JSON/Markdown/escaped HTML/ZIP (`validation/reporting.py:136-176`); PDF is not among the supported new API formats (`api/knowledge_reports.py:57`).

A separate propulsion JSON package exists (`systems/export/design_package.py:16-50`), with complete design serialization and a current-only result view. It is not wired into the modern Reports UI's reproducible P09/P10 history/signoff journey.

**Impact:** the modern Reports workbench is not yet a general reproducible rocket-engine report generator covering requirements, CEA, injector, chamber, thermal, nozzle, structure and cycle. A lack of PDF alone is not a requirement violation because the specification conditions PDF support on what already existed; the substantive gap is general engineering evidence integration/history.

### SCI-07 — Explicit numerics deferrals are real, not implemented capabilities

Thirteen Python modules declare `CAPABILITY_STATE = "DEFERRED"` and export no operational API:

```text
numerics/automatic_differentiation/hessians.py
numerics/automatic_differentiation/reverse_mode.py
numerics/optimization/bayesian.py
numerics/optimization/genetic_algorithm.py
numerics/optimization/lbfgs.py
numerics/optimization/multi_objective.py
numerics/optimization/nelder_mead.py
numerics/optimization/particle_swarm.py
numerics/optimization/simulated_annealing.py
numerics/sensitivity/global.py
numerics/sensitivity/morris.py
numerics/sensitivity/sobol.py
numerics/uncertainty/polynomial_chaos.py
```

For most files the operative declaration is at line 16 (global sensitivity at line 17). These are honest reserved architecture slots, not silent callable stubs. Their presence means the broad architecture is not fully implemented, but they are not automatically blockers for a specifically scoped existing calculation that does not require them.

MOC contour marching is likewise absent: `physics/compressible_flow/moc_nozzle.py:106-113` raises `InsufficientDataError` and assigns the missing algorithm to Numerics. The actual implemented bell is tangent parabolic geometry, not an optimized Rao contour or a characteristic-network solution (`physics/compressible_flow/bell_nozzle.py:1,49-53`).

### SCI-08 — P2 defensive-copy gap in legacy calculation DTOs

`CalculationResult` remains mutable, and `to_canonical_dict()` only shallow-copies inputs/outputs (`systems/contracts/results.py:159-179,186-205`). A pure in-memory reproduction constructing `outputs={"nested":{"value":1}}`, serializing the result, then setting `serialized["outputs"]["nested"]["value"]=2` changes the live result's nested output to 2. `PropulsionDesign.to_canonical_dict()` also returns several live subsystem dictionaries directly (`systems/projects/models.py:198-225`).

**Scope:** a Python consumer of these application DTOs can accidentally mutate scientific state through an apparent serialization projection. Ordinary HTTP JSON decoding does not preserve this alias, so this is not evidence of an unauthenticated HTTP mutation exploit. Results are not generally published/accepted engineering artifacts in the current application. Nonetheless, it is a gap before adopting these legacy objects as immutable published contracts under GOV-003. New geometry/study/report canonical contracts use much stronger immutable/hash-based semantics.

**Recommended fix, not implemented:** define the publication boundary explicitly and return defensive deep copies/canonical immutable bytes at the service boundary; preserve workflow status invalidation as separate metadata. Add a nested mutation regression test.

### SCI-09 — P2 latent finite-angle defect in MOC physical relation

`physics.compressible_flow.moc_nozzle.invariants()` validates Mach/gamma but directly uses `flow_angle_rad` (`physics/compressible_flow/moc_nozzle.py:89-103`). Its dedicated `validate_flow_angle()` rejects nonfinite values at lines 116-121 but is never called there.

Pure in-memory reproduction `invariants(2.0, float("nan"), 1.4)` returns NaN C+ and C− rather than a typed invalid-input error. This does not affect the present tangent-bell or spherical simulation path, and there is no MOC contour solver to falsely accept a design. Fix the finite input check before this physical relation is consumed by a future MOC algorithm.

### SCI-10 — Capability documentation is stale

`README.md:59-64` still says CEA is unbound and injector/cooling are `NOT_IMPLEMENTED`, and only describes the legacy GUI. Actual executable CEA adapter/subsystem implementations and opt-in modern workbenches exist. `physics/thermochemistry/cea_interface.py:53` also retains the historical `interface_only: no built-in CEA execution in this batch` metadata, although the intentionally external adapter is integrated.

This is underclaiming/inconsistent as-built documentation, not proof that those integrations are absent. Update the capability matrix to describe **implemented within limited scope**, opt-in availability, scientific limitations and qualification evidence. Do not replace it with an unsupported universal complete/production-ready statement.

## As-built scientific capability matrix

| Capability | Current implementation | Limits / exact source evidence |
|---|---|---|
| Core unit/quantity/validation boundaries | Implemented infrastructure | `core/quantity.py`, `core/unit.py`, `core/validation.py`; explicit `physics.quantities.as_si` consumed by public physics functions. Numerical/physical correctness still depends on model envelopes. |
| Propulsion lifecycle and dependency freshness | Implemented preliminary workflow | `systems/workflow/graph.py:35-74,285-400`; `systems/projects/models.py:127-196`; result history `systems/workflow/state.py:44-50`. CURRENT is freshness, not experimental validation. |
| Propellant identity/property source registry | Implemented identity/data foundation | `systems/stages/propellants.py:35-47,73-119`; active candidate database is `physics/thermochemistry/database/propellants_master_candidate_v1.json`, not necessarily every placeholder in the separate master file. Properties/inlet state require validity/source review. |
| NASA CEA | Implemented optional external adapter | `plugins/nasa_cea/engine.py:62-238`, `systems/stages/thermochemistry.py:63-134`, `api/propulsion_workflow.py:365-393`. Equilibrium/infinite-area/ideal nozzle; explicit workbench inlet temperatures; no hardware/combustion-efficiency validation. |
| Assumed thermochemistry | Partial executable analysis mode | `systems/stages/thermochemistry.py:170-204`; clearly marked assumptions, but SCI-03 range validation missing. Not a substitute for CEA equilibrium. |
| Ideal performance/constant-gamma compressible flow | Implemented preliminary analytical models | `physics/compressible_flow/isentropic.py`, `choked_flow.py`, `area_mach.py`, `nozzle_1d.py`, `thrust_relations.py`; `systems/stages/performance.py`. No universal separated/viscous/combustion-loss engine model. |
| Injector | Partial, hydraulic liquid orifice | `physics/injectors/orifice.py:17-46,84-115`; two liquid registry propellants at `systems/stages/subsystems.py:69-78`. No layout/spray/atomization/mixing/cavitation/stability prediction. |
| Chamber | Partial L* preliminary geometry | `systems/stages/chamber.py`; explicit workflow limit `systems/workflow/graph.py:65`. Not detailed chamber/injector-volume/manufacturing CAD. |
| Gas-side thermal/Bartz | Partial correlation | `physics/heat_transfer/bartz.py`, `systems/stages/thermal.py`; applicability/source/input-property constraints matter. Not coupled CFD/radiation/combustion heat transfer. |
| Regenerative cooling | Partial prescribed-profile model | `physics/heat_transfer/regenerative.py:35-72,146-315`; single phase, constant properties, smooth fully developed rectangular-channel approximation with explicit Re/Pr/phase/temperature envelopes. Divergent nozzle only at `systems/stages/subsystems.py:269`. |
| Film cooling | Partial gaseous-slot estimate | `physics/heat_transfer/film_cooling.py:22-49`; liquid film evaporation, discrete holes and accelerating-nozzle applicability not established. `systems/stages/subsystems.py:237-264,281-290`. |
| Nozzle contour | Partial tangent parabolic divergent bell | `physics/compressible_flow/bell_nozzle.py:103-172`; `systems/stages/nozzle.py:125-194`. Not optimized Rao/MOC, convergent/chamber CAD, thickness/toleranced manufacturing definition or 2D flow solution. |
| Structure/materials | Partial textbook/handbook checks | `systems/stages/structure.py:109-229`; tensile thin-wall pressure differential, explicit material temperature; handbook typical yield, not certified allowables. No full engine FEA, creep/fatigue/weld/load/thermal-life qualification. |
| Cycle/feed/turbomachinery | Not implemented in the cycle path | `systems/cycle/models.py:27-34`; workflow deferred note `systems/workflow/graph.py:26-33,60`. |
| Native geometry process boundary | Implemented restricted real-kernel slice | `plugins/geometry/adapters.py:52-129`; supervisor/worker separation, typed protocol/version/correlation/hash checks. Current UI acceptance restricted to fixed fixtures. Fresh native execution is not performed by this reviewer. |
| Geometry QA / STEP / STL | Implemented fixture-specific qualification | `systems/geometry/qa.py`, `step_qa.py`, `service.py:175-196`; independent reader/reimport and topology/dimension checks. Separate representation/tolerance/source-export hashes. No engineering publication `service.py:112-113`. |
| General engine NGG | Not implemented/qualified | `systems/geometry/workbench.py:1-4,76-87`; not connected to engine DesignStore and arbitrary engineering parameters. |
| Simulation | Partial 1D software benchmark | `simulation/contracts.py:35-70`; `simulation/workbench.py:31-44,173-204`; `numerics/finite_volume/radial_diffusion.py:32-95`. Constant k/uniform generation/steady sphere only. |
| Numerical foundation | Broad executable foundation, not production CFD/FEA | Root-finding, interpolation/integration, linear/nonlinear algebra, ODE/PDE, forward AD, 1D FEM/FV, gradient/BFGS/CG, local sensitivity, seeded Monte Carlo/LHS, bounded parallel primitives. FEM expressly 1D scalar and not structural FEA (`numerics/finite_element/fem_solver.py:28-58`); generic FV expressly 1D (`numerics/finite_volume/fv_solver.py:40-64`). Thirteen advanced slots deferred. |
| Solver semantics/monitoring | Implemented for spherical benchmark | Execution, termination, convergence, conservation, physical admissibility, solution verification and experimental validation are separate (`simulation/workbench.py:184-204`). Residual normalization/units/linear scale and steady CFL-not-applicable explicit. |
| Field visualization dataset | Partial 1D radial temperature | `simulation/workbench.py:193-199`; explicit unit/range/clipping and interpretation “not a 3D field”. General large-mesh 3D maps/adapters/lazy loading and engine result views absent from this slice. |
| Comparison / V&V | Partial source-aware evidence preview | `validation/contracts.py:38-70`; `validation/comparison.py:12-55`; external thermal JSON/trusted sphere STEP only, no automatic interpolation, output-only uncertainty. |
| Experimental validation | Data-contract/evaluation infrastructure, no verified engine campaign | Imports require uncertainty/instrumentation metadata at `validation/contracts.py:68-70`; measured data cannot grant acceptance at `validation/comparison.py:48-55`. No real engine-measurement campaign qualified in the inspected modern workbench evidence. |
| Knowledge ingestion / graph / search / review | Substantial implemented foundation | `knowledge/workspace/session.py`, ingestion/parsing/extraction/graph/index/search/reasoning modules; actual content/provider/OCR availability varies and capability failures are explicit. Not all attached documents are approved authoritative engineering data. |
| Modern knowledge provenance | Implemented limited source/claim navigation | `knowledge/workspace/evidence_navigation.py:35-53,55-114`; hash-checked source, exact document binding, recorded source/reference/equation/review status, linked assumptions. It explicitly does not infer units/model applicability or independent engineering acceptance. |
| Modern reports | Partial immutable research report slice | `validation/reporting.py:55-92,136-176`; P09/P10 spherical thermal receipts, deterministic outputs, hashes/source references. No general Rocket Engine report integration, durable restart history or signed acceptance. |
| Hardware/flight/physical readiness | Not established | Design-review disclaimer `systems/stages/design_review.py:129-135`; `simulation/workbench.py:192`; `validation/reporting.py:85,91-92`. Software fixtures and equations do not establish an engine's test/flight readiness. |

## Positive scientific/governance observations

1. The calculation pipeline does not silently promote the unsupported cycle into a successful complete engine. `run_design_review_stage` assembles incomplete/blocked reasons and retains the no-certification statement (`systems/stages/design_review.py:69-102,129-135`).
2. NASA CEA lives behind an explicit external adapter and normalized DTO contract; chamber/output quantities, gamma, composition and station finiteness are checked (`physics/thermochemistry/cea_interface.py:124-150`). Provenance records chemistry mode, infinite-area combustor, convergence and tabulated-reactant-enthalpy limitations (`plugins/nasa_cea/engine.py:230-235`).
3. Injector/cooling/bell limits are specific and visible rather than presented as atomization, closed-cycle, CFD or optimized-MOC results (`systems/workflow/graph.py:62-73`). Cooling includes phase/property/Re/Pr/geometric applicability gates and actual energy/pressure balances.
4. Geometry contracts distinguish analytic B-rep, implicit volume, triangles and faceted B-rep; adapters reject unsupported formats rather than pretending implicit geometry becomes editable analytic STEP (`systems/contracts/geometry/graph.py:12-16`; `systems/contracts/geometry/artifacts.py:42-44`; `plugins/geometry/adapters.py:64-66`).
5. The sphere solver computes an equation residual, not merely a correction norm; it retains actual heat-flux balance, checks cancellation, bounds histories/iterations and separates numerical termination from analytic solution verification (`numerics/finite_volume/radial_diffusion.py:36-95`; `simulation/workbench.py:177-204`).
6. Comparison checks frame/model/operating conditions, explicit conversions, coordinate alignment, reference self-comparison and predeclared server-session ordering. Output uncertainty and claimed coverage are not confused with a full experimental validation decision (`validation/workbench.py:127-145`; `validation/comparison.py:14-55`).
7. Report/knowledge source hashes authenticate exact retained bytes while the UI/API explicitly distinguishes original availability, recorded approval, applicability and independent acceptance (`knowledge/workspace/evidence_navigation.py:96-110`; `validation/reporting.py:89-92`).

## Verification observations and limitations of this review

Existing targeted test files were inspected rather than executed by this scientific reviewer:

- Physics/subsystem/CEA: `tests/unit_tests/physics/test_propulsion_subsystems.py`, `tests/unit_tests/api/test_subsystem_workflow.py`, `tests/unit_tests/plugins/test_nasa_cea_engine.py`, `tests/unit_tests/api/test_cea_workflow.py`, `tests/integration_tests/gui/test_cea_http.py`.
- Foundation/refinement/conservation: `tests/unit_tests/numerics/`, `tests/validation_tests/numerics/test_refinement_studies.py`, `tests/validation_tests/test_physics_conservation.py`, `tests/integration_tests/systems_layer/`.
- Real native fixtures: `tests/integration_tests/geometry/test_native_fixtures.py`, `test_g5_closure.py`, `test_p08_workbench.py`. Native-dependent tests must run with a separately pinned, hash-checked runtime and new evidence directory, not overwrite previous gate fixtures.
- Simulation negative semantics: `tests/integration_tests/simulation/test_native_handoff.py:56-66,80-119` covers actual nonconvergence, corrupt datasets, ownership and source-tamper refusal; `tests/unit_tests/numerics/test_radial_diffusion.py` covers the numerical kernel.
- Comparison/report provenance: `tests/unit_tests/validation/test_comparison.py:33-112`, `test_reporting.py:53-106`; `tests/integration_tests/validation/test_native_comparison.py`.

Only the two pure checks in SCI-03/08/09 were newly executed here (SCI-08 and SCI-09 shared one invocation; SCI-03 had an initial no-throat diagnostic followed by a complete explicit-throat reproduction). **Do not add these to pytest pass counts.** Main audit baseline results are the authoritative refreshed test summary. Existing P12 local evidence is useful historical qualification but not fresh execution of every scientific branch in this review.

This review is not a formal theorem/proof of every equation, an independent hot-fire experiment, a production security certification or a blanket correctness guarantee. Comprehensive tests lower software risk; they do not imply “100% accurate” calculations, zero numerical/model error, universal applicability or physical readiness.

## Recommended completion sequence

1. Fix SCI-03 input validation and SCI-08 defensive-copy/publication semantics with regression tests; fix SCI-09 before MOC consumption. Refresh actual capability documentation (SCI-10).
2. Define the release product boundary honestly: presently a local research preview. Resolve repository/release blockers separately from scientific features.
3. Build approved engine cycle power/mass/energy balance and feed/diversion coupling against independent reference fixtures (SCI-02), preserving current preliminary analysis mode.
4. Connect real engine immutable snapshots to NGG templates with feature-specific geometry QA; then qualify general boundary/material mapping and meshing before engine solver handoff (SCI-01).
5. Expand validated model adapters and general comparison/alignment/refinement/uncertainty workflows (SCI-05) with intended-use-specific acceptance.
6. Integrate durable histories, authentic independent reviewer authority and general Rocket Engine reports (SCI-04/06).
7. Independently establish physical readiness using actual documented measurement datasets, matching operating conditions/materials, instrument/calibration provenance, uncertainty budgets, predeclared criteria and evaluated discrepancies. Do not fabricate experimental evidence or infer this from software gates.

