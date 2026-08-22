# COSMOS FINAL SOFTWARE ARCHITECTURE

Version: 1.0

Status: Approved Final Architecture

Approved: June 13, 2026

Project: Cryogenic Optimization and Simulation Multiphysics Operating System

---

# 1. PURPOSE

This document defines the final target directory and module architecture for
COSMOS.

It is the authoritative source for:

* Top-level software layers
* Package and directory locations
* Production module locations
* GUI module locations
* Database file locations
* Test-suite locations

The architecture is a target structure. Directories and modules shall be
created only when their development step begins. Empty placeholder modules
shall not be generated merely to reproduce the complete tree.

The tree enumerates engineering modules and owned data files. Required support
files such as `__init__.py`, `pyproject.toml`, `pytest.ini`, editor settings,
continuous-integration configuration, licenses, and generated cache files are
not engineering modules and therefore are not individually listed. They may be
added when required, but shall not contain physics or system responsibilities.

---

# 2. AUTHORITY AND PRECEDENCE

When specifications disagree about a directory, package, module name, or file
location, this document takes precedence.

The remaining governance documents continue to control their own subjects:

* `COSMOS_MASTER_SPEC.md` controls product requirements and principles.
* `COSMOS_ARCHITECTURE_SPEC.md` controls layer responsibilities and imports.
* `COSMOS_API_SPEC.md` controls canonical data interfaces.
* `COSMOS_CODING_STANDARD.md` controls implementation quality.
* `COSMOS_DATABASE_SPEC.md` controls database schemas and access rules.
* `COSMOS_GUI_SPEC.md` controls GUI behavior and presentation.
* `COSMOS_TESTING_STANDARD.md` controls verification requirements.
* `COSMOS_FILE_SPEC.md` controls module responsibilities.
* `COSMOS_REFERENCE_LIBRARY.md` controls engineering source priority.

No document may silently add, remove, rename, or relocate an item in this
architecture. Such a change requires an explicit versioned amendment to this
document.

---

# 3. DEVELOPMENT METHOD

COSMOS shall be developed incrementally.

For each step:

1. Select the next module in the approved development sequence.
2. Confirm its layer, responsibility, dependencies, inputs, and outputs.
3. Implement only that module and its required tests or package support.
4. Run the related unit tests.
5. Run the complete available test suite.
6. Proceed only after the step satisfies the COSMOS definition of done.

The visual order of files in the tree groups related responsibilities; it does
not by itself override an approved implementation sequence.

---

# 4. FINAL DIRECTORY AND MODULE TREE

```text
COSMOS/
│
├── core/
│   ├── constants.py
│   ├── units.py
│   ├── validation.py
│   ├── logger.py
│   ├── config.py
│   ├── exceptions.py
│   └── settings.py
│
├── physics/
│
│   ├── thermochemistry/
│   │   ├── cea_interface.py
│   │   ├── equilibrium.py
│   │   ├── mixtures.py
│   │   ├── propellants.py
│   │   └── cache.py
│
│   ├── fluids/
│   │   ├── methane.py
│   │   ├── lox.py
│   │   ├── hydrogen.py
│   │   ├── rp1.py
│   │   ├── helium.py
│   │   ├── nitrogen.py
│   │   ├── density.py
│   │   ├── viscosity.py
│   │   ├── conductivity.py
│   │   ├── cp.py
│   │   └── compressibility.py
│
│   ├── cryogenics/
│   │   ├── boiloff.py
│   │   ├── chilldown.py
│   │   ├── insulation.py
│   │   ├── tank_heat_leak.py
│   │   ├── stratification.py
│   │   └── self_pressurization.py
│
│   ├── gas_dynamics/
│   │   ├── choked_flow.py
│   │   ├── nozzle_1d.py
│   │   ├── moc_nozzle.py
│   │   ├── pressure_profile.py
│   │   └── losses.py
│
│   ├── combustion/
│   │   ├── cstar.py
│   │   ├── efficiency.py
│   │   ├── residence_time.py
│   │   ├── stability_criteria.py
│   │   ├── acoustic_modes.py
│   │   └── rayleigh_index.py
│
│   ├── heat_transfer/
│   │   ├── bartz.py
│   │   ├── heat_flux.py
│   │   ├── recovery_temp.py
│   │   └── film_cooling.py
│
│   ├── materials/
│   │   ├── copper_alloys.py
│   │   ├── inconel_alloys.py
│   │   ├── creep_models.py
│   │   ├── fatigue_models.py
│   │   └── thermal_properties.py
│
│   ├── dynamics/
│   │   ├── ignition.py
│   │   ├── shutdown.py
│   │   ├── transient_flow.py
│   │   └── combustion_instability.py
│
│   ├── cycle/
│   │   ├── feed_system.py
│   │   ├── pressurant.py
│   │   ├── tank_blowdown.py
│   │   ├── line_losses.py
│   │   ├── valves.py
│   │   ├── injector_feed.py
│   │   └── cycle_balance.py
│
│   └── cfd/
│       ├── mesh_generator.py
│       ├── boundary_conditions.py
│       ├── solver_interface.py
│       ├── turbulence_models.py
│       ├── post_processing.py
│       └── reduced_order_models.py
│
├── systems/
│
│   ├── performance/
│   │   ├── thrust.py
│   │   ├── isp.py
│   │   ├── massflow.py
│   │   ├── thrust_coefficient.py
│   │   └── altitude_performance.py
│
│   ├── geometry/
│   │   ├── throat.py
│   │   ├── nozzle.py
│   │   ├── nozzle_contour.py
│   │   ├── chamber.py
│   │   └── contraction.py
│
│   ├── tanks/
│   │   ├── lox_tank.py
│   │   ├── fuel_tank.py
│   │   ├── helium_tank.py
│   │   ├── dome_design.py
│   │   ├── tank_sizing.py
│   │   └── pressurization.py
│
│   ├── injector/
│   │   ├── injector_dp.py
│   │   ├── momentum_ratio.py
│   │   ├── stability.py
│   │
│   │   ├── impinging/
│   │   │   ├── doublet.py
│   │   │   └── triplet.py
│   │
│   │   └── coaxial/
│   │       ├── shear.py
│   │       └── swirl.py
│
│   ├── cooling/
│   │   ├── channels/
│   │   │   ├── rectangular.py
│   │   │   └── helical.py
│   │   │
│   │   ├── coolant_properties.py
│   │   ├── heat_transfer.py
│   │   ├── pressure_drop.py
│   │   ├── wall_temperature.py
│   │   └── thermal_stress.py
│
│   ├── structure/
│   │   ├── pressure_vessel.py
│   │   ├── wall_thickness.py
│   │   ├── buckling.py
│   │   └── safety_margins.py
│
│   ├── coupling/
│   │   ├── thermo_flow_coupling.py
│   │   ├── flow_heat_coupling.py
│   │   ├── heat_structure_coupling.py
│   │   └── injector_combustion_coupling.py
│
│   └── reliability/
│       ├── failure_modes.py
│       ├── thermal_runaway.py
│       ├── burnout_prediction.py
│       └── safety_envelope.py
│
├── backend/
│
│   ├── solver_engine.py
│   ├── parameter_handler.py
│   ├── unit_manager.py
│   ├── convergence_manager.py
│
│   ├── multiphysics/
│   │   ├── multiphysics_solver.py
│   │   ├── dependency_graph.py
│   │   ├── solver_scheduler.py
│   │   └── parallel_executor.py
│
│   ├── optimization/
│   │   ├── genetic_algorithm.py
│   │   ├── bayesian_optimizer.py
│   │   ├── gradient_optimizer.py
│   │   ├── multi_objective.py
│   │   └── design_space.py
│
│   └── surrogate/
│       ├── response_surface.py
│       ├── neural_net_model.py
│       └── reduced_order_model.py
│
├── validation/
│   ├── compare_cea.py
│   ├── compare_test_data.py
│   ├── compare_cad.py
│   ├── uncertainty_analysis.py
│   ├── cfd_validation.py
│   └── cycle_validation.py
│
├── gui/
│
│   ├── main_window.py
│
│   ├── tabs/
│   │   ├── dashboard_tab.py
│   │   ├── performance_tab.py
│   │   ├── geometry_tab.py
│   │   ├── tanks_tab.py
│   │   ├── cycle_tab.py
│   │   ├── injector_tab.py
│   │   ├── cooling_tab.py
│   │   ├── structure_tab.py
│   │   ├── optimization_tab.py
│   │   ├── validation_tab.py
│   │   └── settings_tab.py
│
│   ├── widgets/
│   │   ├── propellant_selector.py
│   │   ├── material_selector.py
│   │   ├── engine_summary.py
│   │   └── unit_selector.py
│
│   ├── plots/
│   │   ├── pressure_plot.py
│   │   ├── temperature_plot.py
│   │   ├── heat_flux_plot.py
│   │   ├── coolant_plot.py
│   │   ├── stress_plot.py
│   │   ├── injector_plot.py
│   │   └── performance_plot.py
│
│   └── export/
│       ├── csv_export.py
│       ├── pdf_report.py
│       ├── step_export.py
│       ├── stl_export.py
│       └── excel_export.py
│
├── databases/
│   ├── materials.db
│   ├── propellants.db
│   ├── injector_library.db
│   └── standards.db
│
└── tests/
    ├── unit_tests/
    ├── integration_tests/
    └── regression_tests/
```

---

# 5. ARCHITECTURE CHANGE CONTROL

The architecture may change only when a new engineering requirement cannot be
implemented within the existing ownership boundaries.

Every proposed change shall document:

1. The engineering need.
2. The affected layer and ownership boundary.
3. New or changed dependencies.
4. API, database, GUI, and test impacts.
5. Migration requirements.
6. The new architecture version.

Convenience alone is not sufficient reason to change this architecture.

END OF DOCUMENT
