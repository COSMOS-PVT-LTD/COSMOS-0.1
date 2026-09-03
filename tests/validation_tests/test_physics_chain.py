"""
COSMOS Rocket Propulsion Platform

Module: tests.validation_tests.test_physics_chain
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Deterministic scientific chain from propellant-like inputs to structure.

Description:
    Demonstrates CORE-PHYS-INT-001 readiness of the physics layer:

        mixture / thermo state
            -> compressible nozzle station
            -> Bartz heat transfer
            -> material property
            -> thin-wall stress

    This is a physical-model chain, not an engine design workflow.
"""

from __future__ import annotations

from core.quantity import Quantity
from core.unit import SI

from physics.compressible_flow.choked_flow import choked_mass_flow
from physics.compressible_flow.nozzle_1d import station_from_area_ratio
from physics.compressible_flow.thrust_relations import thrust
from physics.heat_transfer.bartz import bartz_heat_transfer_coefficient
from physics.heat_transfer.heat_flux import convective_heat_flux
from physics.heat_transfer.recovery_temperature import adiabatic_wall_temperature
from physics.materials.catalog import STAINLESS_304
from physics.materials.elastic_properties import yield_strength
from physics.quantities import kelvin, metre, pascal, square_metre
from physics.si import UNIT_DYNAMIC_VISCOSITY, UNIT_SPECIFIC_HEAT, UNIT_THERMAL_CONDUCTIVITY
from physics.solid_mechanics.pressure_vessels import cylinder
from physics.thermochemistry.mixtures import from_mole_fractions
from physics.thermodynamics.ideal_gas import evaluate_state


def test_deterministic_physics_chain_smoke() -> None:
    """
    Deterministic wiring smoke test — not a validated engine analysis.

    Uses a fixed gamma and reference-state fluid properties to exercise the
    cross-module call graph. Scientific consistency is not claimed here.
    """
    mixture = from_mole_fractions({"H2": 0.4, "O2": 0.6})
    gamma = 1.2
    chamber_p = pascal(5.0e6)
    chamber_t = kelvin(3000.0)
    state = evaluate_state(chamber_p, chamber_t, mixture.mean_molar_mass, gamma)
    assert state.density.to_si() > 0.0

    throat = square_metre(0.01)
    mdot = choked_mass_flow(
        chamber_p,
        chamber_t,
        throat,
        gamma,
        mixture.mean_molar_mass,
    )
    exit_station = station_from_area_ratio(
        8.0,
        chamber_p,
        chamber_t,
        gamma,
        mixture.mean_molar_mass,
        branch="supersonic",
    )
    force = thrust(
        mdot,
        exit_station.velocity,
        exit_station.pressure,
        pascal(101325.0),
        square_metre(0.08),
    )
    assert force.to_si() > 0.0
    assert exit_station.mach > 1.0

    taw = adiabatic_wall_temperature(
        exit_station.temperature,
        exit_station.mach,
        gamma,
        0.7,
    )
    bartz = bartz_heat_transfer_coefficient(
        metre(0.113),
        Quantity(8.0e-5, UNIT_DYNAMIC_VISCOSITY),
        Quantity(0.3, UNIT_THERMAL_CONDUCTIVITY),
        Quantity(2500.0, UNIT_SPECIFIC_HEAT),
        chamber_p,
        Quantity(1500.0, SI.get("m/s")),
        exit_station.mach,
        gamma,
        kelvin(800.0),
        taw,
        curvature_radius=metre(0.5),
    )
    flux = convective_heat_flux(
        bartz.heat_transfer_coefficient,
        taw,
        kelvin(800.0),
    )
    assert flux.to_si() != 0.0

    # Material catalog is room-temperature scoped; wall T is illustrative only.
    sy = yield_strength(STAINLESS_304, kelvin(300.0)).require_valid()
    wall = cylinder(chamber_p, metre(0.1), metre(0.008))
    assert wall.hoop.to_si() < sy.to_si()
