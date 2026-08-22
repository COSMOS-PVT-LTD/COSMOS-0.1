# COSMOS_FILE_SPEC.md

# COSMOS FILE SPECIFICATION

Version: 1.0

Status: Approved

Parent Documents:

* COSMOS_MASTER_SPEC.md
* COSMOS_ARCHITECTURE_SPEC.md
* COSMOS_API_SPEC.md
* COSMOS_CODING_STANDARD.md
* COSMOS_DATABASE_SPEC.md
* COSMOS_GUI_SPEC.md
* COSMOS_TESTING_STANDARD.md

---

# PURPOSE

This document defines:

* Every file
* File ownership
* Responsibilities
* Dependencies
* Inputs
* Outputs

File and directory locations are governed by
`COSMOS_FINAL_ARCHITECTURE.md`. This document governs the responsibilities of
those files. If a location differs, the final architecture takes precedence.

This document is the master blueprint used when generating code.

---

# CORE LAYER

## constants.py

Purpose:

Central repository of physical and mathematical constants.

Inputs:

None

Outputs:

Constants

Dependencies:

None

Imported By:

Entire platform

---

## units.py

Purpose:

Unit conversion utilities.

Inputs:

Values

Outputs:

Converted values

Dependencies:

constants.py

Imported By:

Entire platform

---

## validation.py

Purpose:

Input validation.

Inputs:

User values

Outputs:

Validated values

Dependencies:

exceptions.py

---

## logger.py

Purpose:

Central logging system.

Outputs:

Configured logger

Dependencies:

Python logging

---

## config.py

Purpose:

Application configuration.

Outputs:

Settings

---

## exceptions.py

Purpose:

Custom exception hierarchy.

Outputs:

Exception classes

---

## settings.py

Purpose:

Runtime settings management.

Outputs:

Settings object

---

# PHYSICS

## thermochemistry/cea_interface.py

Purpose:

Interface to NASA CEA.

Inputs:

Fuel
Oxidizer
Mixture Ratio
Pressure

Outputs:

CombustionResult

Dependencies:

API models

---

## thermochemistry/equilibrium.py

Purpose:

Chemical equilibrium calculations.

Inputs:

Propellant data

Outputs:

Equilibrium state

---

## thermochemistry/mixtures.py

Purpose:

Mixture calculations.

Outputs:

Mixture properties

---

## thermochemistry/propellants.py

Purpose:

Propellant definitions.

Outputs:

Propellant models

---

## thermochemistry/cache.py

Purpose:

CEA cache management.

Outputs:

Cached thermochemistry data

---

# FLUIDS

## methane.py

Purpose:

Methane properties.

Outputs:

Density
Cp
Viscosity
Conductivity

---

## lox.py

Purpose:

LOX properties.

Outputs:

Density
Cp
Viscosity
Conductivity

---

## hydrogen.py

Purpose:

Liquid hydrogen properties.

---

## rp1.py

Purpose:

RP-1 properties.

---

## helium.py

Purpose:

Helium properties.

---

## nitrogen.py

Purpose:

Nitrogen properties.

---

## density.py

Purpose:

General density calculations.

---

## viscosity.py

Purpose:

General viscosity calculations.

---

## conductivity.py

Purpose:

General thermal conductivity calculations.

---

## cp.py

Purpose:

Specific heat calculations.

---

## compressibility.py

Purpose:

Compressibility factor calculations.

---

# GAS DYNAMICS

## choked_flow.py

Purpose:

Choked-flow equations.

Output:

Mass flow relationships.

---

## nozzle_1d.py

Purpose:

1D nozzle calculations.

Output:

Mach
Pressure
Temperature
Area Ratio

---

## moc_nozzle.py

Purpose:

Method of Characteristics nozzle design.

Output:

Nozzle contour.

---

## pressure_profile.py

Purpose:

Pressure distribution calculations.

---

## losses.py

Purpose:

Nozzle loss models.

---

# SYSTEMS/PERFORMANCE

## thrust.py

Purpose:

Thrust calculations.

Inputs:

EngineInputs

Outputs:

PerformanceResult

---

## isp.py

Purpose:

Specific impulse calculations.

Outputs:

PerformanceResult

---

## massflow.py

Purpose:

Mass flow calculations.

Outputs:

MassFlowResult

---

## thrust_coefficient.py

Purpose:

Thrust coefficient calculations.

Outputs:

PerformanceResult

---

## altitude_performance.py

Purpose:

Altitude performance analysis.

Outputs:

PerformanceResult

---

# SYSTEMS/GEOMETRY

## throat.py

Purpose:

Throat sizing.

Outputs:

ThroatGeometry

---

## nozzle.py

Purpose:

Nozzle sizing.

Outputs:

NozzleGeometry

---

## nozzle_contour.py

Purpose:

Bell nozzle contour generation.

Outputs:

Nozzle profile

---

## chamber.py

Purpose:

Combustion chamber sizing.

Outputs:

ChamberGeometry

---

## contraction.py

Purpose:

Contraction ratio calculations.

Outputs:

Geometry data

---

# BACKEND

## solver_engine.py

Purpose:

Master orchestration engine.

Inputs:

EngineInputs

Outputs:

EngineSolution

Dependencies:

All systems modules

---

## parameter_handler.py

Purpose:

Parameter preprocessing.

---

## unit_manager.py

Purpose:

Unit conversion management.

---

## convergence_manager.py

Purpose:

Numerical convergence handling.

---

# GUI

## main_window.py

Purpose:

Application shell.

Dependencies:

Backend only.

Must not perform calculations.

---

## dashboard_tab.py

Purpose:

Project overview.

---

## performance_tab.py

Purpose:

Performance workspace.

---

## geometry_tab.py

Purpose:

Geometry workspace.

---

## tanks_tab.py

Purpose:

Tank workspace.

---

## cycle_tab.py

Purpose:

Feed-system workspace.

---

## injector_tab.py

Purpose:

Injector workspace.

---

## cooling_tab.py

Purpose:

Cooling workspace.

---

## structure_tab.py

Purpose:

Structural workspace.

---

## optimization_tab.py

Purpose:

Optimization workspace.

---

## validation_tab.py

Purpose:

Validation workspace.

---

## settings_tab.py

Purpose:

Application settings.

---

# FILE GENERATION RULE

Every file generation request shall define:

1. File Name
2. Layer
3. Purpose
4. Inputs
5. Outputs
6. Dependencies
7. API Models Used
8. Tests Required

No file shall be generated without satisfying these requirements.

END OF DOCUMENT
