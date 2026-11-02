# R06 remaining limits — validation preparation and solver contracts

User asks to work toward full operating-point solving, bidirectional thermal/combustion feedback and physical validation. User explicitly confirms **no measurements yet; prepare the validation workflow**. This is not authorization to fabricate measurements, approve engineering acceptance, migrate owner data or operate hardware.

Entry HEAD293223ebef190eaa647e67dc581eb186b2b5d987; previous R06.3/4 source manifest governs preservation. Existing dirty work and all past evidence are retained.

## Concrete work in this increment

1. Extend the existing V&V infrastructure additively with propulsion-specific immutable validation plans tied to exact managed baseline/results. The current `validation/contracts.py` and `comparison.py` only support spherical conduction, so they must not be relabelled as rocket validation.
2. Predeclare intended use, applicability basis, output discrepancy limits, output uncertainties/correlation/coverage and context/property tolerances **before** measurement import. Derive candidate predictions, operating conditions and relevant properties from the retained current model; never trust client-posted predictions or success flags.
3. Generate an **empty** explicit-unit CSV measurement template and metadata checklist. Preserve raw imported CSV bytes/hash, instrumentation/calibration/uncertainty provenance and held-out/calibration/synthetic distinction. Strict SI fields, exact measurands/conditions/properties, bounded rows, duplicate and nonfinite refusal. No automatic matching, resampling, unit conversion, uncertainty defaults or missing-value substitution.
4. Compare independently supplied measurements with their predeclared exact candidate. Require matching conditions/property tolerances and complete reported uncertainty for a passing software comparison. Imported assertions/checksums do not establish authenticity or qualified physical validation. No route may post or infer physical acceptance.
5. Reuse R05 project membership/CAS/idempotent immutable snapshots/dependencies, authenticated scoped API and Projects presentation. Persist a plan before data and data before assessment. Keep missing measurements, method/baseline drift, synthetic/calibration-only evidence, model applicability and independent review visible.
6. Test with explicitly synthetic software fixtures only: empty template/no evidence gate, matching/mismatched contexts/properties, independent quantities, uncertainty/sign/units/duplicates, raw originals, stale source, exact replay/restart, foreign/read-only denial and no acceptance escalation. Run focused and full qualification; retain exact test-mutated CEA cache.

## Solver work deliberately not faked by this increment

`physics/heat_transfer/regenerative.py` and `systems/stages/subsystems.py` state divergent-nozzle-only cooling with prescribed gas h/Taw, frozen gas-side heat-transfer assumptions and no core gas energy iteration. `plugins/nasa_cea/engine.py` calls a fixed-enthalpy equilibrium rocket solve with an **adiabatic nozzle**. A loop that heats injected fuel but leaves nozzle energy extraction unchanged can violate the total engine energy budget or double-count recovered heat.

The full solver therefore needs independently reviewed contracts for:

- steady pressure-fed/GG feed network with actual flow-dependent injector/line/cooling characteristics and (for GG) supplied pump/turbine maps or explicitly bounded characteristic functions; unknown Pc, core flows/O/F, GG diversion, shaft speed/work and component states;
- supported phase/property windows and source-backed heated-reactant enthalpy, not extrapolated liquid-temperature database values;
- location-resolved non-adiabatic nozzle/chamber heat extraction and fuel-return enthalpy, with an engine control-volume ledger showing internal regenerative heat cancels exactly once;
- nonlinear residual scales, brackets/constraints, solution uniqueness/admissibility, convergence versus independent mass/energy/power residuals, no-root/nonconvergence termination and complete iteration history;
- immutable solved candidate results in the existing downstream authority; no circular back-edge or mutation/promotion of the frozen upstream cycle stage.

The existing NASA CEA interface is authoritative for chemistry; do not create a second equilibrium solver or silently pass heat loss as a changed ideal-gas temperature. Primary-source equation mappings and independent coupled reference cases must precede these new models. Completion of this evidence workflow is **not** completion of those solvers or whole R06.

## Physical-validation gate

Needs genuine measurement files and test description, compatible geometry/operating conditions/material and propellant properties, traceable calibration, measurement uncertainty and a reviewed complete uncertainty budget, predeclared criteria, evaluated comparison, independent qualified scope/authenticity review and acceptance. No measurements are available. Software readiness can be established now; physical validation remains NOT_PERFORMED/AWAITING_MEASUREMENTS.
