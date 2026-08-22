# COSMOS API SPECIFICATION

Version: 1.1

Status: Approved

Parent Documents:

* COSMOS_MASTER_SPEC.md
* COSMOS_ARCHITECTURE_SPEC.md

---

# PURPOSE

This document defines the canonical data contracts used throughout COSMOS.

All production modules shall exchange information exclusively through API dataclasses defined in this specification.

All API models shall:

* Use SI units internally
* Use Python dataclasses
* Be type-safe
* Be serializable
* Be testable
* Be immutable where practical

No production solver shall return raw dictionaries.

---

# CORE PROJECT MODELS

## ProjectMetadata

```python
@dataclass(slots=True, frozen=True)
class ProjectMetadata:
    project_name: str
    author: str
    version: str
    created_date: str
    modified_date: str
```

---

## ProjectSettings

```python
@dataclass(slots=True, frozen=True)
class ProjectSettings:
    project_name: str
    author: str

    unit_system: str

    auto_save: bool
    auto_save_interval: int
```

Units:

```text
auto_save_interval    s
```

---

# ENGINE INPUT MODELS

## EngineInputs

```python
@dataclass(slots=True, frozen=True)
class EngineInputs:
    thrust: float
    chamber_pressure: float
    mixture_ratio: float

    ambient_pressure: float

    fuel_name: str
    oxidizer_name: str

    expansion_ratio: float
```

Units:

```text
thrust               N
chamber_pressure     Pa
ambient_pressure     Pa
mixture_ratio        -
expansion_ratio      -
```

---

# MATERIAL MODELS

## Material

```python
@dataclass(slots=True, frozen=True)
class Material:
    name: str
    family: str

    density: float

    elastic_modulus: float
    poisson_ratio: float

    yield_strength: float
    ultimate_strength: float

    thermal_conductivity: float
    specific_heat: float

    thermal_expansion: float

    melting_temperature: float
```

Units:

```text
density                 kg/m³
elastic_modulus         Pa
poisson_ratio           -
yield_strength          Pa
ultimate_strength       Pa
thermal_conductivity    W/(m·K)
specific_heat           J/(kg·K)
thermal_expansion       1/K
melting_temperature     K
```

---

# FLUID AND THERMODYNAMIC MODELS

## Propellant

```python
@dataclass(slots=True, frozen=True)
class Propellant:
    name: str

    temperature: float
    pressure: float

    density: float
    viscosity: float

    thermal_conductivity: float
    specific_heat: float
```

---

## FluidState

```python
@dataclass(slots=True, frozen=True)
class FluidState:
    pressure: float
    temperature: float

    density: float
    viscosity: float

    conductivity: float
    specific_heat: float
```

---

## ThermodynamicState

```python
@dataclass(slots=True, frozen=True)
class ThermodynamicState:
    pressure: float
    temperature: float

    enthalpy: float
    entropy: float

    density: float
```

---

## FlowState

```python
@dataclass(slots=True, frozen=True)
class FlowState:
    pressure: float
    temperature: float

    velocity: float
    mach: float

    mass_flow: float
```

---

# THERMOCHEMISTRY

## CombustionResult

```python
@dataclass(slots=True, frozen=True)
class CombustionResult:
    chamber_temperature: float
    gamma: float

    molecular_weight: float

    characteristic_velocity: float
```

---

# PERFORMANCE

## MassFlowResult

```python
@dataclass(slots=True, frozen=True)
class MassFlowResult:
    total_mass_flow: float
    fuel_mass_flow: float
    oxidizer_mass_flow: float
```

---

## PerformanceResult

```python
@dataclass(slots=True, frozen=True)
class PerformanceResult:
    thrust: float
    isp: float

    thrust_coefficient: float

    exhaust_velocity: float
```

---

# GEOMETRY

## ChamberGeometry

```python
@dataclass(slots=True, frozen=True)
class ChamberGeometry:
    chamber_length: float
    chamber_diameter: float
    chamber_volume: float

    contraction_ratio: float
```

---

## ThroatGeometry

```python
@dataclass(slots=True, frozen=True)
class ThroatGeometry:
    throat_area: float
    throat_diameter: float
    throat_radius: float
```

---

## NozzleGeometry

```python
@dataclass(slots=True, frozen=True)
class NozzleGeometry:
    expansion_ratio: float
    exit_area: float

    exit_diameter: float

    nozzle_length: float
```

---

## EngineGeometry

```python
@dataclass(slots=True, frozen=True)
class EngineGeometry:
    chamber: ChamberGeometry
    throat: ThroatGeometry
    nozzle: NozzleGeometry
```

---

# FEED SYSTEMS

## Tank

```python
@dataclass(slots=True, frozen=True)
class Tank:
    propellant_name: str

    volume: float
    pressure: float

    diameter: float
    length: float
```

---

## TankSizingResult

```python
@dataclass(slots=True, frozen=True)
class TankSizingResult:
    fuel_tank: Tank
    oxidizer_tank: Tank
```

---

## PressurantTankResult

```python
@dataclass(slots=True, frozen=True)
class PressurantTankResult:
    volume: float
    pressure: float
    mass: float
```

---

## FeedSystemResult

```python
@dataclass(slots=True, frozen=True)
class FeedSystemResult:
    inlet_pressure: float
    injector_pressure: float
    total_pressure_drop: float
```

---

# INJECTOR

## InjectorResult

```python
@dataclass(slots=True, frozen=True)
class InjectorResult:
    injector_type: str

    pressure_drop: float

    total_orifices: int

    fuel_orifice_diameter: float
    oxidizer_orifice_diameter: float
```

---

# COOLING

## CoolingChannel

```python
@dataclass(slots=True, frozen=True)
class CoolingChannel:
    width: float
    height: float

    rib_thickness: float

    channel_count: int
```

---

## WallState

```python
@dataclass(slots=True, frozen=True)
class WallState:
    hot_wall_temperature: float
    cold_wall_temperature: float

    heat_flux: float
    thermal_stress: float
```

---

## CoolingResult

```python
@dataclass(slots=True, frozen=True)
class CoolingResult:
    coolant_inlet_temp: float
    coolant_exit_temp: float

    pressure_drop: float

    max_wall_temp: float

    heat_removed: float
```

---

# STRUCTURES

## StructuralResult

```python
@dataclass(slots=True, frozen=True)
class StructuralResult:
    max_stress: float
    max_strain: float

    factor_of_safety: float
```

---

# RELIABILITY

## ReliabilityResult

```python
@dataclass(slots=True, frozen=True)
class ReliabilityResult:
    burnout_margin: float
    thermal_margin: float
    life_cycles: float
```

---

# CFD

## CFDResult

```python
@dataclass(slots=True, frozen=True)
class CFDResult:
    mesh_cells: int

    max_temperature: float
    max_velocity: float

    pressure_loss: float
```

---

# OPTIMIZATION

## OptimizationProblem

```python
@dataclass(slots=True, frozen=True)
class OptimizationProblem:
    objectives: list[str]
    constraints: list[str]
    variables: list[str]
```

---

## BestDesign

```python
@dataclass(slots=True, frozen=True)
class BestDesign:
    design_id: str
    objective_value: float
    parameters: tuple[float, ...]
```

---

## OptimizationResult

```python
@dataclass(slots=True, frozen=True)
class OptimizationResult:
    best_design: BestDesign
    objective_value: float
    iterations: int
```

---

# VALIDATION

## ValidationResult

```python
@dataclass(slots=True, frozen=True)
class ValidationResult:
    reference_source: str
    predicted_value: float
    reference_value: float
    percent_error: float
```

---

# SOLVER MODELS

## SolverSettings

```python
@dataclass(slots=True, frozen=True)
class SolverSettings:
    max_iterations: int
    tolerance: float
    relaxation_factor: float
    enable_parallel: bool
```

---

## SolverStatus

```python
class SolverStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    CONVERGED = "CONVERGED"
    FAILED = "FAILED"
```

---

# MASTER ENGINE SOLUTION

## EngineSolution

```python
@dataclass(slots=True, frozen=True)
class EngineSolution:
    inputs: EngineInputs

    combustion: CombustionResult

    massflow: MassFlowResult

    geometry: EngineGeometry

    performance: PerformanceResult

    tanks: TankSizingResult

    injector: InjectorResult | None

    cooling: CoolingResult | None

    structure: StructuralResult | None

    reliability: ReliabilityResult | None
```

---

# FUTURE EXPANSION

Future modules may add:

* TurbopumpState
* CycleAnalysisResult
* FlightCondition
* TrajectoryResult
* TVCResult
* TelemetryRecord
* DigitalTwinState

Backward compatibility shall be maintained across all API versions.

END OF DOCUMENT
