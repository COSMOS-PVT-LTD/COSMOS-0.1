# Injector, cooling and nozzle foundation

Implemented locally on 2026-10-08. This is a **preliminary engineering software foundation**, not a complete rocket-engine design, hardware approval, or physical validation. No zero-error guarantee is made. Cycle power balance is deliberately deferred.

## Available workbench calculations

| Workflow stage | Executable model | Explicit exclusions |
| --- | --- | --- |
| 07 Injector | Two liquid-stream orifice hydraulic sizing: area, hole diameter, mean velocity, Reynolds number, momentum rate and manifold pressure | Spray/atomization, impingement geometry, face layout, acoustic stability, cavitation, gas/flashing injectors |
| 11 Nozzle | Circular divergent throat blend joined tangentially to a quadratic parabolic bell; sampled wall coordinates, angles, area ratios and quasi-1D flow stations | Optimized Rao/MOC, convergent/chamber CAD, separation/side loads, CFD, manufacturing tolerances |
| 10 Cooling System | Segmented steady single-phase regenerative channels; optional gaseous tangential-slot film mixing estimate; heat pickup, coolant/wall temperatures, pressure loss and energy residual | Chamber/convergent cooling in this workflow, liquid-film evaporation, boiling/supercritical properties, roughness/manifold losses, radiation, thermal stress, transient/coking models |

Inputs are blank until explicitly entered or loaded from a saved design. Synthetic values in test fixtures are **not** recommended fluid properties, design settings, or empirical validation data.

## Usage and dependency order

1. Open/create a saved design and establish CURRENT Phase 3 Performance. The existing assumed-state path still requires explicit chamber temperature, gamma and molecular weight when no CEA engine is bound.
2. Run Phase 4 to provide CURRENT thermal boundary inputs (gas viscosity, conductivity, Cp and the assumed wall temperature).
3. Run **07 Injector** with the selected liquid propellants' actual sourced properties, discharge coefficients, pressure drops and hole counts. This sizing does not feed a spray model into chamber L* sizing.
4. Run **11 Nozzle** with explicit bell length fraction, start/exit angles, divergent blend-radius ratio and point count.
5. Run **10 Cooling System**, choosing a coolant direction and either explicitly disabled film or the gaseous-slot estimate. Cooling requires the CURRENT contour and thermal inputs, despite its earlier presentation number.
6. Inspect the assumptions, warnings and validity status. Download CURRENT contour/station or cooling-segment CSV data in SI units. Save/Reload retains subsystem inputs and results; changed dependency inputs stale affected results and exclude them from current-result exports.

The workspace's existing Recalculate chain also runs configured subsystems, generating the contour before cooling. An explicitly requested subsystem with missing inputs fails; unconfigured optional subsystems in the legacy Phase 4 chain remain NOT_CALCULATED. No inferred properties or hidden geometry defaults are used to fill these inputs.

## Model definitions and verification boundaries

### Liquid injector hydraulics

For each core stream, `mdot = Cd A sqrt(2 rho delta_p)`, `d = sqrt(4 A/(pi N))`, and `u = mdot/(rho A)`. The velocity is the average through the geometric hole area, not a vena-contracta jet velocity. O/F splits the CURRENT core flow into oxidizer/fuel streams. The reported momentum ratio is hydraulic bookkeeping, not proof of mixing performance.

Bounds: positive finite mass flow, density, pressure drop and viscosity; `0 < Cd <= 1`; integer hole count 1–100000. The workflow requires liquid registry identities. Actual single-phase state, cavitation margin and Cd applicability still require engineering assessment.

Reference: [NASA SP-8089, Liquid Rocket Engine Injectors](https://ntrs.nasa.gov/citations/19760023196).

### Tangent bell contour

Let `Rt` be the CURRENT Performance throat radius, `Re = Rt sqrt(epsilon)` and `Rb` the supplied divergent blend radius. The axial bell length is a fraction of the equivalent 15-degree cone with the circular-blend correction:

`L = fraction * [Re - Rt + Rb(sec(15 degrees)-1)] / tan(15 degrees)`.

The circular arc ends at the specified start-wall angle. Intersecting the start and exit tangents defines a quadratic Bezier control point. Nonphysical intersections and nonmonotonic geometry are rejected. Sampling lives in Numerics; construction and area-Mach/isentropic equations live in Physics. Stations use the same frozen/assumed chamber state as Performance, not a solved 2D characteristic net.

Bounds: epsilon > 1; `0 < length_fraction <= 1`; `0 < exit_angle < start_angle < 90 degrees`; positive blend ratio; integer point count 11–1001; feasible tangent intersection. More points improve sampling, not physical fidelity. The NASA SP-125 worked example is a geometry regression check, not validation of an engine.

Reference: [Huzel and Huang, NASA SP-125, section 4.3, figure 4-13](https://ntrs.nasa.gov/citations/19710019929).

### Regenerative cooling

Smooth rectangular channels use hydraulic diameter `Dh = 2wd/(w+d)`, Dittus-Boelter heating `Nu = 0.023 Re^0.8 Pr^0.4`, and Darcy-Blasius `fD = 0.3164 Re^-0.25`. Parallel-channel mass flow is evenly divided. Only channel-bottom cooling area is credited: no rib-fin enhancement.

Each segment has prescribed constant gas-side h and adiabatic wall temperature, planar wall conduction and constant coolant properties. The exact segment energy solution is used, and the accumulated heat is checked against coolant enthalpy rise. Local peak wall temperature is evaluated at the segment coolant outlet, not just from its averaged heat flux. Both flow directions are supported.

The workflow builds a divergent-nozzle gas profile using the existing SI Bartz model, an `(At/A)^0.9` area correction and a Prandtl-based recovery temperature. Bartz h is frozen at the explicit thermal-stage wall-temperature assumption, not iterated with the predicted wall. This is a prescribed approximate boundary condition; gas energy loss does not feed back into thrust or mixture state.

Enforced envelope: Re 10000–100000; Pr 0.7–160; total path/Dh >= 10; wall thickness/radius <= 0.1; channel/rib packing at every radius; positive pressure above the declared maximum vapour pressure; coolant bulk and coolant-side wall within the supplied property/single-phase temperature window; hot wall below the supplied limit. These checks **do not prove** smooth fully developed flow, constant-property accuracy or absence of boiling. Property source/state and the window must be supplied by the engineer.

References: [NASA SP-125](https://ntrs.nasa.gov/citations/19710019929), [NASA TP-2232 Dittus-Boelter heating relation](https://ntrs.nasa.gov/citations/19840013760), and [NASA smooth-pipe friction reference](https://ntrs.nasa.gov/citations/19840009459). Hydraulic-diameter use for noncircular channels is explicitly an approximation.

### Gaseous-slot film cooling

The Goldstein mixing estimate as stated by Peter and Kloker is `xi = 7 delta/(8 F s)` and `eta_ad = 1/[1+(Cp_g/Cp_c)xi]`. The adiabatic wall temperature becomes `Taw_f = Taw_g - eta_ad(Taw_g-Tfilm)`.

Slot location/height, blowing ratio, coolant temperature/Cp, boundary-layer thickness at the slot, declared linear thickness growth and applicability length are **explicit sourced inputs**. The declared window must cover the whole downstream contour. A station is inserted at the slot with one-sided temperatures, preventing film protection from leaking upstream through segment averaging. No empirical DNS fit is generalized to arbitrary nozzles. The reported film mass-flow estimate uses the declared blowing ratio and core mass flux at the slot; this stream is not deducted from the engine core or coolant budget.

Reference: [Peter and Kloker (2020), equations 2–3 and discussion of accelerating nozzle flow](https://doi.org/10.1007/978-3-030-53847-7_5). It is a gaseous tangential-slot estimate; accelerating-flow applicability is NOT_VALIDATED. Liquid fuel films require evaporation and coupled chemistry models that are not implemented here.

## API and ownership

Authenticated endpoint: `POST /api/propulsion/designs/<id>/run/subsystems`.

Body: `{"inputs":{"injector":{...},"nozzle":{...},"cooling":{...}},"stages":["injector","nozzle","cooling"]}`. Either member is optional; omitted inputs use explicit saved configuration. Stage selection must be nonempty, unique and drawn from these three stages. The orchestration order is injector, nozzle, cooling.

`save_design(..., edits={"subsystem_inputs": {...}})` atomically validates all configuration updates. A submitted stage object replaces that stage's configuration; omitted stages are retained. Null values remove fields. Unknown fields/stages, booleans in numeric fields, nonfinite values and fractional counts are rejected. Source strings are required for execution.

Field definitions: `systems/configuration/subsystems.py`; GUI labels and units: `gui/static/propulsion-suite.js`. Quantity-consuming physical functions live in `physics/injectors/orifice.py`, `physics/compressible_flow/bell_nozzle.py`, `physics/heat_transfer/regenerative.py`, `physics/heat_transfer/nozzle_profile.py` and `physics/heat_transfer/film_cooling.py`. Systems persists source inputs separately from derived slots and records upstream result identities; API/GUI do not duplicate these equations.

CURRENT means fresh for saved inputs, not physically validated. Successful results remain `validation=NOT_CLAIMED` and engineering applicability `UNKNOWN` where the actual physical setup is unverified. Recognized legacy placeholder graph edges are migrated without inventing new results; custom dependencies are retained. Cycle power balance stays NOT_IMPLEMENTED, and a whole-engine review cannot become complete merely because these subsystem tests pass.

## Reproducible software checks

Tests include analytical orifice round trips/scaling, NASA bell geometry, exact constant-profile cooling/pressure balances, energy conservation, refinement convergence, film slot discontinuity, invalid dimensions/domain inputs, save/reload and dependency invalidation, authenticated HTTP execution, and browser DTO/CSV freshness guards.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv-remediation/bin/python -m pytest -p no:cacheprovider -q
.venv-remediation/bin/python -m ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools
.venv-remediation/bin/python -m mypy core physics numerics systems api
node --test tests/js/*.test.cjs
node --check gui/static/propulsion-suite.js
git diff --check
```

Fixtures in `tests/fixtures/propulsion_subsystems.py` deliberately use synthetic constant properties and generous windows to test software identities. Independent fluid/material datasets, calibration, full chamber cooling, coupled mass/energy/cycle closure, atomization/stability analysis, CFD and hardware tests remain necessary before a real engine design can be substantiated.

### Local execution evidence (2026-10-08)

- Full Python suite: **2204 passed, 6 skipped**.
- JavaScript suite: **21 passed**; propulsion script syntax check passed.
- Ruff: all configured source/test/tool targets passed.
- Mypy: no issues in **316 source files**.
- Diff whitespace check passed.
- Isolated headless app startup and authenticated browser execution verified all three subsystem actions. Saved-design reload, contour-to-cooling invalidation, explicit film-mode controls and cold-start injector registry initialization were checked.
- Browser-generated nozzle and cooling CSV files each contained 101 data rows for the selected synthetic grid and matched CURRENT persisted results within the Core canonical serializer's numeric precision.

The browser fixture was stored outside the repository and outside the user's real design store. No Git commit, push, hosted CI execution or physical validation is claimed by these checks.
