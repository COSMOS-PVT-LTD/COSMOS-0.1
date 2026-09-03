# COSMOS_0.1 — PROPULSION WORKFLOW PHASE 2 MASTER IMPLEMENTATION DIRECTIVE

**Document ID:** `COSMOS-0.1-PROPULSION-WORKFLOW-PHASE-2-001`  
**Status:** Approved execution directive  
**Phase:** Phase 2 — Domain Model + Calculation Result Contract + Workflow Foundation  
**Repository:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`

---

# 1. MISSION

Build the **foundation of the full COSMOS propulsion calculation workflow** on top of the already frozen Core + Physics foundation.

This phase establishes the engineering domain model, shared propulsion design state, calculation-result contract, workflow graph, dependency tracking, and persistence boundary.

This is **not** the phase to implement every propulsion equation.

The objective is to transform COSMOS from:

```text
independent calculators
```

into:

```text
a coherent propulsion engineering analysis system
```

The architecture must remain open for future higher-fidelity mathematics and physics.

> **Freeze the foundation. Build the system around it.**

---

# 2. AUTHORITATIVE REPOSITORY

Work only against:

```text
/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
```

Do not use an empty or incorrect Cursor workspace as evidence.

Before editing, inspect:

```text
documentation/development/propulsion_workflow_architecture.md
documentation/development/core_physics_independent_vv_report_004.md
documentation/development/core_physics_freeze_blockers_004.md
documentation/development/physics_sme_final_001.md
documentation/development/phys_004_num_closeout_001.md
physics/contracts/PHYS-004-NUM-WAIVER.md
documentation/development/core_layer_architecture.md
```

Also inspect the actual current source tree.

The uploaded Phase 1 architecture map is the authoritative design input for this phase.

---

# 3. ARCHITECTURAL DECISIONS — ALREADY APPROVED

## Package

Use:

```text
systems/
```

Do not use `engineering/` for this milestone.

## Dependency direction

```text
GUI ──HTTP──► API
API ────────► SYSTEMS
SYSTEMS ───► PHYSICS
PHYSICS ────► CORE

CORE ──X──► PHYSICS
GUI ──X───► PHYSICS
GUI ──X───► SYSTEMS INTERNALS
```

The GUI must not import Physics directly.

The GUI must not know internal Systems implementation details.

---

# 4. FROZEN FOUNDATION — DO NOT REOPEN

The existing Core + Physics foundation is frozen.

Do not modify it simply to make Phase 2 easier.

Preserve:

```text
physics → core
core ──X──→ physics
```

Preserve existing:

- dimensional safety;
- quantity semantics;
- affine temperature behavior;
- validation;
- typed exceptions;
- deterministic serialization/hashing;
- Physics model behavior;
- compressible-flow regression behavior;
- thermochemistry regression behavior;
- LOX fail-closed behavior;
- Bartz behavior;
- Core layer independence;
- PHYS-004 PATH A waiver.

If an integration issue appears, first solve it at the Systems/API boundary.

Only modify frozen Core/Physics if an actual defect is demonstrated by a reproducible test and separately authorized.

---

# 5. EXISTING ARCHITECTURE REALITY

Phase 1 established:

```text
GUI
    pywebview + local HTTP shell
        ↓
api/
        ↓
physics/
        ↓
core/
```

Current GUI propulsion pages behave primarily as independent calculators.

There is currently no authoritative server-owned:

```text
PropulsionDesign
```

state.

There is no dedicated:

```text
systems/
```

package.

There is no propulsion-specific design persistence layer.

Phase 2 creates these foundations.

---

# 6. CREATE THE SYSTEMS FOUNDATION

Create the minimum clean package:

```text
systems/
├── __init__.py
│
├── projects/
│   ├── __init__.py
│   └── models.py
│
├── requirements/
│   ├── __init__.py
│   └── models.py
│
├── propellants/
│   ├── __init__.py
│   └── models.py
│
├── cycle/
│   ├── __init__.py
│   └── models.py
│
├── operating_point/
│   ├── __init__.py
│   └── models.py
│
├── contracts/
│   ├── __init__.py
│   └── results.py
│
├── workflow/
│   ├── __init__.py
│   ├── graph.py
│   ├── state.py
│   └── invalidation.py
│
└── persistence/
    ├── __init__.py
    └── design_store.py
```

Do not create unnecessary files.

If equivalent existing models already exist, reuse or extend them instead of creating duplicates.

---

# 7. ROOT DOMAIN OBJECT — PROPULSION DESIGN

Create or extend the authoritative propulsion design aggregate.

Conceptual structure:

```text
PropulsionDesign
│
├── identity
├── metadata
├── requirements
├── propellant_configuration
├── cycle_configuration
├── operating_point
├── injector_design
├── chamber_design
├── thermal_design
├── cooling_design
├── nozzle_design
├── structural_design
├── material_selection
├── workflow_state
└── calculation_results
```

Do not require all subsystems to be implemented in Phase 2.

Unavailable subsystem objects may remain:

```text
None
```

or an explicit unavailable-state representation consistent with repository conventions.

Do not fabricate calculations.

---

# 8. DESIGN IDENTITY

Every propulsion design must have stable identity information.

At minimum:

```text
design_id
name
description
revision
created_at
updated_at
software_version
status
```

Use deterministic identifiers where repository conventions require reproducibility.

Do not make timestamps part of numerical computation.

---

# 9. REQUIREMENTS MODEL

Create a requirements object capable of representing:

```text
target_thrust
ambient_pressure
ambient_temperature
operating_altitude
burn_duration
target_chamber_pressure
mixture_ratio
expansion_ratio
cycle_type
propellant_selection
```

Requirements may be optional.

Do not invent defaults that change engineering meaning.

Where defaults are necessary for UI convenience, distinguish:

```text
DEFAULT DISPLAY VALUE
```

from:

```text
ENGINEERING ASSUMPTION
```

---

# 10. PROPELLANT CONFIGURATION

Create a workflow-level propellant configuration that references the existing Physics property/propellant registry.

Conceptually:

```text
PropellantConfiguration

oxidizer_id
fuel_id
mixture_ratio
oxidizer_state
fuel_state
oxidizer_temperature
fuel_temperature
oxidizer_pressure
fuel_pressure
```

Do not duplicate the actual thermophysical property database.

Systems owns the configuration.

Physics owns the physical model.

---

# 11. CYCLE CONFIGURATION

Create an extensible cycle configuration.

At minimum:

```text
cycle_type
implementation_status
parameters
```

Represent unsupported cycles honestly.

For example:

```text
PRESSURE_FED → if supported
GAS_GENERATOR → NOT_IMPLEMENTED
STAGED_COMBUSTION → NOT_IMPLEMENTED
EXPANDER → NOT_IMPLEMENTED
ELECTRIC_PUMP → NOT_IMPLEMENTED
```

Do not implement cycle equations in Phase 2.

---

# 12. OPERATING POINT

Create an OperatingPoint model containing applicable values such as:

```text
chamber_pressure
ambient_pressure
ambient_temperature
chamber_temperature
mass_flow
oxidizer_mass_flow
fuel_mass_flow
mixture_ratio
gamma
molecular_weight
characteristic_velocity
```

Values must be represented using existing Core quantity semantics where they are physical quantities.

Do not use raw floats where doing so bypasses dimensional safety.

---

# 13. CALCULATION RESULT CONTRACT

Create a generic result envelope.

Conceptual structure:

```text
CalculationResult

result_id
calculation_type
status

model_id
model_version

inputs
outputs

assumptions
warnings
errors

validity
verification
validation

provenance

software_version
design_revision
```

The exact implementation may use existing repository contracts if equivalent functionality exists.

The result contract must support:

```text
CURRENT
STALE
FAILED
NOT_CALCULATED
NOT_IMPLEMENTED
OUT_OF_RANGE
```

and execution states such as:

```text
QUEUED
RUNNING
COMPLETED
FAILED
```

Do not create contradictory state semantics.

Define one authoritative status model.

---

# 14. MODEL METADATA

Every significant calculation result must be able to identify:

```text
model_id
model_version
```

This is mandatory for future Physics upgrades.

Example:

```text
bartz
version = 0.1
```

Later:

```text
bartz
version = 0.2
```

must not silently overwrite the meaning of an old saved result.

---

# 15. ASSUMPTIONS

Results must distinguish explicit engineering assumptions from calculated values.

Example:

```text
Assumptions:
    gamma = ...
    ambient_pressure = ...
```

Do not hide assumptions inside functions.

Do not silently insert engineering assumptions.

---

# 16. VALIDITY CONTRACT

Create a validity representation.

Conceptually:

```text
ValidityStatus

status
checks
violations
valid_range
```

Possible statuses:

```text
VALID
OUT_OF_RANGE
UNKNOWN
NOT_APPLICABLE
```

Do not invent validity ranges.

Where a model does not expose a validated range, say:

```text
UNKNOWN
```

or the repository's equivalent.

---

# 17. VERIFICATION / VALIDATION CONTRACT

Results must preserve the distinction:

```text
Verification
Validation
```

Never collapse them into one field.

Example:

```text
verification:
    status = PASS
    reference = ...

validation:
    status = NOT_CLAIMED
```

A verified analytical model is not automatically experimentally validated.

---

# 18. PROVENANCE CONTRACT

Capture sufficient information to answer:

> Why did COSMOS produce this result?

At minimum, where available:

```text
source
reference
model
version
software_version
implementation_revision
calculation_revision
```

Do not invent citations.

---

# 19. WORKFLOW GRAPH

Create a graph representation.

Conceptual:

```text
WorkflowGraph

nodes
edges
dependencies
status
```

Node example:

```text
Node:
    id = thermochemistry
    dependencies = [operating_point, propellants]
    status = CURRENT
```

The graph must represent calculation dependencies rather than GUI navigation only.

---

# 20. INITIAL WORKFLOW NODES

Create the stage registry for:

```text
00 design_project
01 requirements
02 propellants
03 cycle
04 operating_point
05 thermochemistry
06 performance
07 injector
08 chamber
09 thermal
10 cooling
11 nozzle
12 structure
13 materials
14 performance_summary
15 consistency
16 design_review
```

Each node must have:

```text
stage_id
name
dependencies
implementation_status
```

---

# 21. INITIAL DEPENDENCY GRAPH

Implement the architecture established in Phase 1:

```text
Requirements
     ↓
Propellant Definition
     ↓
Operating Point
     ↓
Thermochemistry
     ↓
Mass Flow / Performance
     ↓
Injector
     ↓
Chamber
   ↙   ↘
Thermal  Structure
   ↓        ↑
Cooling  Materials
   ↘      ↙
      Nozzle
         ↓
Performance Summary
         ↓
Consistency
         ↓
Design Review
```

Cycle may influence Operating Point when implemented.

Until then:

```text
cycle = NOT_IMPLEMENTED
```

must not block unrelated workflow construction.

---

# 22. NODE IMPLEMENTATION STATUS

Every stage must distinguish:

```text
IMPLEMENTED
PARTIAL
NOT_IMPLEMENTED
UNAVAILABLE
OUT_OF_RANGE
```

Do not equate "node exists" with "physics exists."

A node can exist architecturally while its calculation is unavailable.

---

# 23. DEPENDENCY INVALIDATION

This is a critical engineering requirement.

If a fundamental input changes:

```text
Pc
O/F
propellant
ambient pressure
geometry
material
```

identify dependent calculations and mark them:

```text
STALE
```

Example:

```text
Pc changed
   ↓
Operating Point       STALE
Thermochemistry       STALE
Performance           STALE
Chamber               STALE
Thermal               STALE
Cooling               STALE
Nozzle                STALE
Structure             STALE
Design Review         STALE
```

Do not delete the previous results.

Historical results must remain available as prior revisions.

---

# 24. NO STALE RESULT DISPLAY

The GUI must never present a stale result as current.

Every displayed result must have a status:

```text
CURRENT
STALE
FAILED
NOT_CALCULATED
NOT_IMPLEMENTED
OUT_OF_RANGE
```

This rule belongs in the Systems contract, not only in JavaScript.

---

# 25. CHANGE TRACKING

A design input change should create a revision/event capable of identifying:

```text
field
old value
new value
revision
timestamp
source
```

Use existing serialization conventions.

Do not build a complete enterprise audit system in Phase 2.

Create only the foundation required for reproducible design revisions.

---

# 26. PERSISTENCE

Create a dedicated propulsion design persistence boundary.

Do NOT use the knowledge graph/vault as the propulsion design store.

Do NOT use audit storage as the design store.

Do NOT treat browser localStorage as authoritative engineering state.

The authoritative state must be server/application owned.

Use the repository's existing persistence capabilities where possible.

Initial target:

```text
systems/persistence/
```

with a design store interface.

The backend storage mechanism may be JSON or SQLite depending on what already exists and what best fits the repository.

Do not introduce unnecessary infrastructure.

---

# 27. SERIALIZATION

Use existing:

```text
core.serialization
```

for canonical serialization where appropriate.

Design serialization must preserve:

```text
design identity
requirements
propellant configuration
cycle configuration
operating point
workflow state
calculation results
model versions
warnings
V&V metadata
revision
```

Avoid serializing transient GUI state.

---

# 28. GUI INTEGRATION PREPARATION

Phase 2 does not need to rebuild the GUI.

Prepare the backend contracts so the GUI can later consume:

```text
GET design
GET workflow
GET stage
POST/update inputs
POST calculate stage
GET result
GET status
```

Exact endpoints should follow existing API conventions.

Do not create dozens of endpoints without necessity.

---

# 29. API BOUNDARY

The intended architecture is:

```text
GUI
  │
  │ HTTP/JSON
  ▼
api/
  │
  ▼
systems/
  │
  ▼
physics/
  │
  ▼
core/
```

API responsibilities:

- authentication;
- request validation;
- DTO mapping;
- HTTP error mapping;
- calling Systems services.

Systems responsibilities:

- design state;
- workflow orchestration;
- dependency management;
- persistence;
- calculation-result contracts.

Physics responsibilities:

- physical calculations.

Core responsibilities:

- quantities;
- units;
- validation;
- foundational contracts.

---

# 30. NO GUI EQUATIONS

Do not modify JavaScript to reproduce Physics.

Do not write:

```text
pressure = ...
temperature = ...
Mach = ...
thrust = ...
```

as engineering equations in the GUI.

The GUI must request the calculation from the backend.

---

# 31. FIRST CALCULATION INTEGRATION

Do not integrate every Physics capability in Phase 2.

Prove the Systems architecture using one existing Physics capability.

Preferred candidate:

```text
compressible-flow / isentropic
```

or:

```text
area-mach
```

because these already have established regression evidence.

The path must be:

```text
API
 ↓
Systems
 ↓
Physics
 ↓
Core
 ↓
CalculationResult
 ↓
API
```

GUI integration can consume this result in the next phase.

---

# 32. ENGINEERING RESULT EXAMPLE

Conceptual result:

```text
CalculationResult
----------------------------

calculation_type:
    compressible.isentropic

status:
    CURRENT

model_id:
    isentropic_flow

model_version:
    <actual implementation version>

inputs:
    Mach = 2.0
    gamma = 1.4

outputs:
    T0/T = ...
    p0/p = ...
    rho0/rho = ...

verification:
    PASS

validation:
    NOT_CLAIMED

warnings:
    []

provenance:
    ...
```

Use actual repository model identifiers.

Do not invent version metadata if the implementation does not yet expose it; create the smallest appropriate contract.

---

# 33. TESTING

Phase 2 is incomplete without tests.

## Unit tests

Test:

```text
PropulsionDesign
Requirements
PropellantConfiguration
CycleConfiguration
OperatingPoint
CalculationResult
Validity
Verification
Validation
Provenance
WorkflowGraph
Node dependencies
Invalidation
Persistence serialization
```

## Integration tests

At minimum:

```text
Systems → Physics
Physics → Core
Systems → CalculationResult
Persistence → Design reload
```

## Architecture tests

Verify:

```text
Core does not import Physics
Systems may import Physics
GUI does not import Physics
GUI does not import Systems internals
API does not contain engineering equations
```

---

# 34. REGRESSION REQUIREMENT

All existing Core + Physics regression tests must remain green.

Phase 2 must not weaken:

```text
affine temperature
Core layering
Anderson gas dynamics
NASA7
LOX fail-closed
Bartz
deterministic hashing
Numerics port
```

Do not replace old tests with weaker workflow tests.

---

# 35. DETERMINISM

For identical:

```text
design state
model version
inputs
configuration
solver settings
```

the calculation result must be deterministic wherever the underlying Physics
model is deterministic.

Do not introduce random behavior.

Do not use GUI state as a calculation input.

---

# 36. ERROR PROPAGATION

Typed Physics/Core errors must survive through Systems.

Do not convert all engineering failures into:

```text
"Calculation failed"
```

without diagnostic information.

Preserve:

```text
error type
message
stage
model
input context
```

The API may serialize the error safely for the GUI.

---

# 37. HONEST CAPABILITY STATES

The following remain explicitly unavailable unless actual implementations
already exist:

```text
CEA execution
Cycle power balance
Advanced injector calculations
Regenerative cooling
Full film cooling
MOC nozzle contour
Full FEA
Experimental validation
```

Do not create fake calculations.

Example:

```text
Stage:
    regenerative_cooling

Status:
    NOT_IMPLEMENTED

Reason:
    No validated implementation available.
```

---

# 38. DO NOT OVERBUILD

Do NOT implement in this phase:

- full propulsion optimizer;
- AI model selection;
- CFD solver;
- complete FEA solver;
- complete CEA engine;
- full cycle simulation;
- digital twin;
- cloud backend;
- CAD kernel;
- automatic design optimization.

Phase 2 is the **workflow foundation**.

---

# 39. CODE QUALITY

Use the repository's existing:

- typing conventions;
- linting;
- formatting;
- exception conventions;
- logging;
- serialization;
- testing structure.

Do not create a second framework inside `systems/`.

Keep classes small and composable.

Avoid giant `PropulsionDesign.calculate_everything()` functions.

Prefer:

```text
workflow orchestrator
    ↓
stage service
    ↓
Physics
    ↓
result
```

---

# 40. DOCUMENTATION

Create:

```text
documentation/development/propulsion_workflow_phase2.md
```

Document:

- new Systems package;
- domain objects;
- result contract;
- workflow graph;
- dependency rules;
- invalidation;
- persistence;
- API boundary;
- implemented stage(s);
- unavailable stages;
- test results;
- known limitations.

Do not declare the complete propulsion workflow implemented if only the
foundation exists.

---

# 41. PHASE 2 DEFINITION OF DONE

Phase 2 is complete only when:

```text
[ ] systems/ package exists
[ ] PropulsionDesign exists
[ ] Requirements model exists
[ ] PropellantConfiguration exists
[ ] CycleConfiguration exists
[ ] OperatingPoint exists
[ ] CalculationResult contract exists
[ ] Validity contract exists
[ ] Verification/Validation metadata exists
[ ] Provenance exists
[ ] WorkflowGraph exists
[ ] Stage registry 00–16 exists
[ ] Dependencies are explicit
[ ] Invalidation works
[ ] Stale results cannot be treated as current
[ ] Design persistence boundary exists
[ ] Canonical serialization is used
[ ] One existing Physics calculation is wired through Systems
[ ] API boundary is established or prepared
[ ] Core → Physics remains forbidden
[ ] GUI → Physics remains forbidden
[ ] Existing Core + Physics regression suite remains green
[ ] New Systems tests pass
[ ] Architecture tests pass
[ ] Documentation created
```

---

# 42. STOP CONDITIONS

STOP and report instead of improvising if:

```text
an existing model conflicts with the proposed Systems model;
a frozen Physics contract must be changed;
a Physics capability does not exist;
a calculation requires an undocumented assumption;
the existing GUI requires architectural rewriting;
persistence conflicts with existing repository architecture;
a dependency cycle appears;
the implementation would require fake physics.
```

Do not silently work around these conditions.

---

# 43. PHASE 3 HANDOFF

After Phase 2 passes its gate, the next phase will be:

```text
PHASE 3
Requirements
    ↓
Propellants
    ↓
Operating Point
    ↓
Thermochemistry
    ↓
Performance
```

Only after this deterministic backend chain works should broader subsystem
integration begin.

---

# 44. FINAL DIRECTIVE

Build COSMOS as an engineering platform, not a collection of calculators.

The architectural objective is:

```text
                    COSMOS PROPULSION
                           │
                    PropulsionDesign
                           │
                    WorkflowGraph
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   Requirements       Operating Point     Propellants
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                     Thermochemistry
                           │
                      Performance
                           │
                  ┌────────┴────────┐
                  │                 │
              Subsystems        V&V/Validity
                  │                 │
                  └────────┬────────┘
                           │
                     Calculation
                        Results
                           │
                           ▼
                          API
                           │
                           ▼
                         GUI
```

The frozen Core + Physics foundation remains the trusted computational
substrate.

The new `systems/` layer becomes the controlled bridge between those
calculations and the real propulsion-design workflow.

Future higher-fidelity mathematics and Physics must be introduced through
versioned, traceable model upgrades rather than silent modification of the
frozen baseline.

**Execute Phase 2 only. Do not expand scope.**
