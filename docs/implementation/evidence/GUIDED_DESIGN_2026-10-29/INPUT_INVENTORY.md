# GD-00 input disposition and interaction contract

Scope: Rocket Engine workflow and its injector/nozzle/cooling editors. Existing
standalone scientific calculators, component editors and managed-cycle detail
forms remain in Expert Mode; they are not deleted or declared automatically solved.
User approved GD-00 through GD-06 on 2026-10-29. Source proposal is retained in
docs/implementation/proposals/GUIDED_ENGINE_DESIGN_2026-10-29/PLAN.md.

## Primary decisions

- Thrust: user requirement, explicit N internally / kN in the form.
- Propellant pair: explicit user choice; initial guided coverage LCH4/LOX only.
- Chamber pressure: user requirement, explicit Pa absolute / bar absolute display.
- Environment: standard sea-level convention, explicit vacuum or custom Pa.
- Duration: user requirement, or explicitly omitted for steady-performance scope.
- Cycle: explicit selection; initial guided automation is pressure-fed only.
- Project/name/description: metadata, not engineering inputs. New guided runs
  append ordinary propulsion objects; never overwrite an existing design.

## Existing normal workflow fields

Source: gui/static/propulsion-suite.js, buildWorkflowCard(),
thermochemistryFields() and engineeringBoundaryFields().

- O/F: bounded CEA ideal-performance selection, or explicit backend lock.
- Expansion ratio: ambient-matched CEA study, explicit finite vacuum cap or lock.
- Tc, gamma and molecular weight: calculated CEA state; assumed-state tools stay
  in Expert Mode and are never a silent fallback for CEA failure.
- Throat area: target sizing from the ideal nozzle result; a conflicting user
  lock is rejected instead of adjusting thrust/feed silently.
- L*, contraction ratio: explicit provisional reviewed profile parameters.
- Fuel/oxidizer inlet temperatures: explicit provisional reviewed inlet profile,
  not measurements and not automatically the heated injector state.
- Nozzle length fraction, start/exit angles, blend radius and point count:
  reviewed profile parameters; contour is the existing tangent-bell model.
- Wall thickness, external wall pressure, material/process/temperature, wall
  temperature, gas heat-transfer properties and throat curvature: not resolved
  by ideal sizing. These retain their Expert editors; thermal/strength conclusions
  are visibly BLOCKED pending applicable source/geometry conditions. No hot
  allowable or certified thickness is synthesized.
- Gas-property source mode and pressure model: explicit Expert model choices;
  no silent source substitution or thin-wall/closed-end-Lame promotion.

## Injector editor

- Fuel/oxidizer density and viscosity: original-byte NIST exact cold states,
  pinned species, pressure, temperature, phase, reference-state and SHA256.
  Not interpolated/extrapolated into unmatched conditions.
- Both injector pressure drops: explicitly reviewed provisional drop.
- Both Cd values: explicitly reviewed provisional coefficient, not measured.
- Both hole counts: explicitly reviewed positive integer.
- Properties/Cd/source text: populated from the exact package and review hash;
  retained in the ordinary injector result and export.
- Different manifold T/P: block cold-hydraulic auto-sizing only; retain ideal
  performance. Heated fuel, cavitation, layout, atomization and stability are
  not established by the reference-row lookup.

## Cooling editor

Every current cooling field remains accessible in Expert Mode:

- Flow, inlet temperature and pressure: require actual selected branch/feed
  coupling; the cold manifold profile does not establish a regenerative outlet.
- Density, viscosity, conductivity, cp, minimum/maximum property temperatures
  and maximum vapor pressure: require a matched, valid fluid/phase package.
- Channel width/depth/count, rib width, wall ligament and direction: require
  matched geometry and constrained thermal/hydraulic candidate selection.
- Wall conductivity and maximum wall temperature: require material/process
  evidence at the evaluated temperature; do not borrow room-temperature yield.
- Film mode, slot position/height, blowing ratio, film temperature/cp, boundary
  thickness/growth, valid length and source: retain explicit model applicability.
  No automatic liquid-film or boiling support is implied.

GD-03 therefore has cold-injector assistance and clearly labelled pressure
screening, but broader matched cooling/material/operating closure is OPEN.

## Traceability contract

systems/guided_engine/resolution.py defines every guided profile parameter,
allowed unit/domain, original recommendation, override flag, basis, evidence
category and unknown uncertainty. A preview hash includes the brief, effective
inputs, complete property package, selection policy and method fingerprints.
Accepting a different hash is refused. Old approval is never copied into a new
case. Source edits invalidate currentness without rewriting saved bytes.

Case lifecycle: Define -> Review -> Accept exact basis -> Queued/Running ->
Completed/Failed/Cancelled/Interrupted -> Reopen exact saved result. COMPLETED
is execution completion only; the report separately states blocked checks,
physical_validation NOT_PERFORMED and engine_complete false.

## Current UI boundary

Guided mode hides the advanced input/editor chrome but retains every original
control in Expert Mode. It also hides the unrelated legacy inspector/job panel
to avoid contradictory 'No inspected design / No jobs' messages. Native menus
and workbench navigation remain available. The mode toggle and saved-result
link open the exact calculated ordinary propulsion design. Retained CAD is
explicitly labelled by its own physics/model/attempt identity; it is not rebound.
