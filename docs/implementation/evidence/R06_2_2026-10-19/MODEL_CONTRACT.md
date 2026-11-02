# R06.2a - pressure-fed computational foundation

Approved parent scope: steady single-phase pressure-fed first, then gas-generator. This slice implements a **read-only supplemental assessment**, not a new upstream workflow dependency. The existing cycle node precedes performance; consuming performance there would create a cycle in the dependency graph. No graph, canonical design schema, migration, cycle implementation flag or preliminary bypass is changed. Later durable/UI integration must retain exact baseline, inputs and method identities and resolve this dependency explicitly before stage promotion.

## Primary sources inspected before implementation

1. [DOE-HDBK-1012/3-92, June1992, module HT-03](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL3.pdf): printed pp9-11 (PDF31-33), equations3-1 through3-6, volume/mass flow and steady continuity; printed p25 (PDF47), equation3-12, extended Bernoulli including irreversible head loss. Equation3-12 and its station/sign definitions visually checked. US customary conversion factor `g_c` disappears in coherent SI; multiply the head equation by `rho*g`. Use the resulting pressure form directly, also admitting explicitly declared zero gravity without division by g. No friction factor correlation is implemented. Download SHA256 `0135196976fc613fa7e0129776e9fd74ead03e6cc3a37bab65803d5484140974`.
2. [Cannon2010, Liquid Propulsion: Propellant Feed System Design](https://ntrs.nasa.gov/citations/20100035254), section2, printed/PDF pp5-6, read and visually checked. Supplies the pressure-fed system topology and regulated tank-pressure boundary, not the equations or component coefficients. Its thermal/solubility/ullage cautions are exclusions here. Download SHA256 `57639b0bb32d6ced57b3be88d70a6d90555dabdd3fb589c388b0bae82b23f03b`.

No empirical loss, density, discharge coefficient, regulator curve or uncertainty is inferred from these references. No NASA-SP-125 equation is claimed from metadata alone. References are engineering-method sources, not experimental validation of COSMOS.

## Stations, equations and explicit inputs

Generic Physics path: station1 source static absolute pressure/velocity, station2 required static absolute pressure/flow area. Both are the same constant-density liquid and positive specified mass flow. Positive `dz=z2-z1` is uphill against the nonnegative declared gravitational acceleration. Kinetic correction factors are1 (uniform mean-velocity approximation). No pump/shaft work is present.

- `Q = mdot/rho`, `v2 = Q/A2` (DOE3-1/2/3).
- `dp_kin = rho*(v2^2-v1^2)/2`.
- `dp_elevation = rho*g*dz`.
- `dp_loss = sum(explicit irreversible pressure-equivalent losses)`.
- `p1_required = p2_required + dp_kin + dp_elevation + dp_loss` (SI rearrangement of DOE3-12 with no pump).
- `pressure_residual = p1_supplied - p2_required - dp_kin - dp_elevation - dp_loss`.
- `loss_power = Q*dp_loss` is dissipated mechanical energy rate, **not** shaft/pressurant power.
- `mass_residual = sum(inlets)-sum(outlets)` (DOE3-6), independently for each propellant and total. Existing Physics bipropellant mass split is reused for core demand.

Systems specialization: source1 is the regulated tank liquid free surface, explicitly zero liquid surface speed; station2 is the injector inlet manifold, `p2_required=Pc+specified injector static delta_p`. Its explicit area determines velocity at the **core-required flow**, not the separately supplied tank withdrawal used to test continuity. Feed-line, valve and cooling entries are irreversible losses only **upstream of this manifold**. Injector static delta_p is not added again as an irreversible loss. Data sources must state this station convention and the applicable flow/temperature. The constant tank-pressure boundary is supplied, not a simulated regulator.

Strict specification: schema `cosmos.pressure-fed-assessment-input.v1`; regime `STEADY_SINGLE_PHASE_INCOMPRESSIBLE`; boundary `REGULATED_TANK_PRESSURE`; accounting `CORE_ONLY_NO_DIVERSION`; explicit acceleration, positive absolute pressure/mass tolerances; explicit zero external oxidizer/fuel outflows (nonzero unsupported, never discarded). Each stream requires LIQUID declaration, temperature, density and its source, tank pressure/withdrawal, manifold area, signed elevation rise, injector static delta_p and its source, and exactly three loss entries (`feed_line`, `valves`, `cooling`) with value/source. Zeros are explicit assumptions, not missing values. No unit inference: DTOs use exact `{value,unit}` pairs and are converted to Core Quantity only at the boundary. Unknown fields/units/Boolean/nonfinite/oversized values are refused.

Require selected PRESSURE_FED, current operating-point/thermochemistry/performance baselines and explicit retained O/F/Pc/mdot. Capture their complete original canonical results, baseline canonical SHA256 and exact request in output. No design mutation, saving, inferred project authority, stage activation or hash-only replacement of source data. Initial adapter supports explicit assumed-state performance only; CEA is refused pending separate qualification. Existing current cooling/injector results are not consumed or claimed coupled.

## Status and admissibility

Positive finite dimensional mass flow/density/area/absolute pressures, nonnegative gravity/velocities/irreversible losses, finite signed elevation. Loss labels unique, nonempty and bounded,1-32 entries. Arithmetic overflow/underflow, nonfinite derived values and nonpositive required absolute source pressure refused. No hidden epsilon clamp or solver iteration.

Pressure states: DEFICIT below negative declared tolerance; SURPLUS_REQUIRES_CONTROL above positive tolerance; BALANCED_WITHIN_TOLERANCE otherwise. Surplus is **not closure** at the imposed flow: an additional valve/regulator/control characteristic would be needed. Each mass residual must independently satisfy the declared mass tolerance; cancellation of fuel and oxidizer errors is not a pass. These are declared algebraic tolerances, not measurement uncertainty or a safety margin.

Shaft power NOT_APPLICABLE with null value. Pressurant consumption/work, tank sizing/strength, local cavitation/vapor margins, cryogenic/two-phase transitions, transient blowdown, thermal feedback, film/GG diversion, cooling recirculation and complete engine cycle closure NOT_ASSESSED/UNSUPPORTED. `physical_validation=NOT_PERFORMED`, `workflow_cycle_complete=false` even when balances pass.

## Predeclared independent verification fixtures

Hand-derived synthetic SI examples; no rocket/hardware performance claim. Expected constants written independently of implementation, checked at rel1e-12/abs1e-9 Pa (mass abs1e-14 kg/s).

- rho1000, mdot2, A2=.001, v1=0, g10, dz3, losses20000+30000Pa, p2=100000Pa. Q=.002m3/s, v2=2m/s, kinetic2000Pa, elevation30000Pa, losses50000Pa, required p1=182000Pa, dissipated power100W. Supply182000 balances,181000 deficit1000,183000 surplus1000.
- Same case dz=-3 gives122000Pa. Same case g=0 gives152000Pa. Explicit v1=2m/s cancels kinetic term and gives180000Pa. No implicit gravity constant.
- Station area halved to.0005 gives v2=4, kinetic8000, required188000Pa; pressure varies at imposed flow, not a solved flow.
- Zero losses/velocity-head difference/elevation gives required inlet=outlet pressure and zero dissipated loss power (not zero shaft power).
- Two independent streams supplied2/1 kg/s and consumed2/1 close;2.1/.9 has zero total residual but opposite per-stream errors and must fail closure.
- Real existing assumed-state engine result: evaluate unchanged; source bytes, workflow, source result IDs and cycle NOT_IMPLEMENTED remain unchanged. Stale/missing, wrong cycle, invalid units/regime/phase, nonzero diversion, CEA, malformed/current inconsistent baseline and extreme arithmetic refuse explicitly.

No full UI, durable managed assessment publication or gas-generator completion claimed in this slice. Next R06.2b: exact managed assessment capture/history/HTTP/UI, current downstream source checks and explicit stage dependency design before any graph promotion; then selected GG scope.
