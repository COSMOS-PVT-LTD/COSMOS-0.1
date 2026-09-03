# CORE-CONTRACT-ISSUE

Status: OPEN (consumed in-progress Core surface; physics does not patch Core)

Owner: Physics Foundation Agent (PHYS-001..007)
Consumer: `physics/`
Provider: Core Agent (CORE-001..CORE-005)

## Observed Core surface at implementation time

The Core Agent is simultaneously implementing typed computational contracts.
Physics consumes the following modules as they exist on the working tree and
does **not** modify `core/`:

| Contract | Module | Physics usage |
|----------|--------|---------------|
| `Quantity` | `core.quantity` | Public physics I/O |
| `Unit` / `UnitRegistry` / `SI` | `core.unit` | SI unit identity |
| `Dimension` | `core.dimension` | Dimensional checks |
| `ObjectMetadata` / `ProvenanceRecord` | `core.metadata` | Model traceability |
| `ValidationResult` | `core.contracts` | Validation envelopes |
| Scalar validators | `core.validation` | Finite / positive / gamma |
| Exception hierarchy | `core.exceptions` | `CosmosError`, `DimensionError`, `InvalidInputError`, `SolverConvergenceError` |
| Constants | `core.constants` | `UNIVERSAL_GAS_CONSTANT`, `STEFAN_BOLTZMANN_CONSTANT`, `G0`, `STANDARD_ATMOSPHERE` |

## Gaps physics worked around (do not patch Core)

1. **Derived units missing from `SI` registry**
   Physics constructs derived `Unit` objects in `physics/si.py` using Core
   `Unit` + `Dimension` algebra (`J/kg`, `J/(kg K)`, `W/(m K)`, `Pa s`, ...).
   Request: Core register common thermodynamic and transport units.

2. **`validate_gamma` permits `gamma == 1.0`**
   That value is singular for isentropic and shock relations.
   Physics enforces `1 < gamma <= 3` in `physics.quantities.require_gamma`.
   Request: Core distinguish "heat-capacity ratio interval" from
   "gasdynamic gamma excluding the singular point 1".

3. **No `SpecificHeat`, `DynamicViscosity`, or `HeatFlux` dimensions in Core**
   Physics derives them as `ENERGY/(MASS*TEMPERATURE)`, `MASS/(LENGTH*TIME)`,
   `POWER/AREA`. Request: optional Core convenience dimensions.

4. **Quantity public API is computational, not yet frozen**
   Physics treats `Quantity.to_si()`, `convert_to`, and dimensional arithmetic
   as the CORE-002 contract. If Core changes serialization field names,
   physics tests that round-trip Core objects will fail loudly.

5. **Knowledge `Unit`/`Dimension`/`Quantity` are not computational**
   Physics does **not** import `knowledge.models.quantity` for solver math.

## Physics policy until Core freeze

- Internal solver algebra uses SI `float` after `as_si(...)`.
- Public dimensional arguments are Core `Quantity`.
- Dimensionless arguments may be Core `Quantity` or `float`.
- Physics will not create `PhysicsQuantity`, `ThermoQuantity`, or `FluidUnit`.
