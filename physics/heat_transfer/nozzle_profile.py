"""Prescribed Bartz/recovery gas-side profile and explicit gaseous-slot mixing.

Boundary-layer growth is supplied by the caller with provenance, not inferred
from a flat-plate correlation in accelerating nozzle flow. One-sided values
at the slot prevent film protection leaking upstream during segment averaging.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import LENGTH, MASS_FLOW_RATE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_non_negative, validate_positive
from numerics.interpolation.linear import interpolate
from physics.compressible_flow.bell_nozzle import (
    ContourPoint,
    NozzleFlowStation,
    flow_stations,
)
from physics.exceptions import OutOfRangeError
from physics.heat_transfer.bartz import bartz_heat_transfer_coefficient
from physics.heat_transfer.film_cooling import effectiveness, film_adiabatic_temperature
from physics.heat_transfer.recovery_temperature import adiabatic_wall_temperature
from physics.heat_transfer.regenerative import GasWallStation
from physics.quantities import as_si, kelvin, metre
from physics.si import DYNAMIC_VISCOSITY, SPECIFIC_HEAT, THERMAL_CONDUCTIVITY, UNIT_HTC
from physics.validity import ValidityStatus


@dataclass(frozen=True, slots=True)
class NozzleGasInputs:
    chamber_pressure: Quantity
    chamber_temperature: Quantity
    gamma: float
    characteristic_velocity: Quantity
    core_mass_flow: Quantity
    viscosity: Quantity
    conductivity: Quantity
    specific_heat: Quantity
    assumed_wall_temperature: Quantity
    throat_blend_radius: Quantity


@dataclass(frozen=True, slots=True)
class GaseousSlotFilm:
    slot_x: Quantity
    slot_height: Quantity
    blowing_ratio: float
    temperature: Quantity
    specific_heat: Quantity
    initial_boundary_layer_thickness: Quantity
    thickness_growth_rate: float
    valid_length: Quantity


def nozzle_wall_profile(
    stations: tuple[NozzleFlowStation, ...],
    gas: NozzleGasInputs,
    film: GaseousSlotFilm | None = None,
) -> tuple[tuple[GasWallStation, ...], float]:
    if len(stations) < 2:
        raise InvalidInputError("Require at least two contour flow stations.")
    mu = validate_positive(
        as_si(gas.viscosity, DYNAMIC_VISCOSITY, "gas viscosity"), "gas viscosity"
    )
    kg = validate_positive(
        as_si(gas.conductivity, THERMAL_CONDUCTIVITY, "gas conductivity"),
        "gas conductivity",
    )
    cpg = validate_positive(as_si(gas.specific_heat, SPECIFIC_HEAT, "gas Cp"), "gas Cp")
    pr, rt = mu * cpg / kg, stations[0].radius_m
    rows = stations
    slot_x, film_flow = 0.0, 0.0
    if film is not None:
        slot_x = validate_non_negative(as_si(film.slot_x, LENGTH, "slot x"), "slot x")
        height = validate_positive(
            as_si(film.slot_height, LENGTH, "slot height"), "slot height"
        )
        blowing = validate_positive(film.blowing_ratio, "blowing ratio")
        valid_length = validate_positive(
            as_si(film.valid_length, LENGTH, "film valid length"), "film valid length"
        )
        validate_non_negative(film.thickness_growth_rate, "film thickness growth rate")
        if (
            not rows[0].x_m <= slot_x < rows[-1].x_m
            or valid_length < rows[-1].x_m - slot_x
        ):
            raise OutOfRangeError(
                "Slot must lie inside the contour; film validity length must cover its downstream wall."
            )
        xs = [row.x_m for row in rows]
        radius = interpolate(xs, [row.radius_m for row in rows], slot_x)
        if slot_x not in xs:
            angle = interpolate(xs, [row.wall_angle_deg for row in rows], slot_x)
            added = flow_stations(
                (ContourPoint(slot_x, radius, angle, (radius / rt) ** 2),),
                gas.chamber_pressure,
                gas.chamber_temperature,
                gas.gamma,
            )[0]
            rows = tuple(sorted((*rows, added), key=lambda row: row.x_m))
        core_flow = validate_positive(
            as_si(gas.core_mass_flow, MASS_FLOW_RATE, "core mass flow"),
            "core mass flow",
        )
        film_flow = (
            blowing * core_flow / (math.pi * radius**2) * 2 * math.pi * radius * height
        )
    profile = []
    for row in rows:
        taw = adiabatic_wall_temperature(
            kelvin(row.temperature_k), row.mach, gas.gamma, pr
        )
        unfilmed_taw = taw
        h = bartz_heat_transfer_coefficient(
            metre(2 * rt),
            gas.viscosity,
            gas.conductivity,
            gas.specific_heat,
            gas.chamber_pressure,
            gas.characteristic_velocity,
            row.mach,
            gas.gamma,
            gas.assumed_wall_temperature,
            taw,
            curvature_radius=gas.throat_blend_radius,
        )
        if h.validity is not ValidityStatus.VALID:
            raise OutOfRangeError("Gas-side Bartz Reynolds validity exceeded.")
        eta = 0.0
        if film is not None and row.x_m >= slot_x:
            delta0 = validate_positive(
                as_si(film.initial_boundary_layer_thickness, LENGTH, "film delta0"),
                "film delta0",
            )
            cpc = validate_positive(
                as_si(film.specific_heat, SPECIFIC_HEAT, "film Cp"), "film Cp"
            )
            eta = effectiveness(
                boundary_layer_thickness=metre(
                    delta0 + film.thickness_growth_rate * (row.x_m - slot_x)
                ),
                slot_height=film.slot_height,
                blowing_ratio=film.blowing_ratio,
                heat_capacity_ratio=cpg / cpc,
            )
            taw = film_adiabatic_temperature(taw, film.temperature, eta)
        at_slot = film is not None and row.x_m == slot_x
        profile.append(
            GasWallStation(
                metre(row.x_m),
                metre(row.radius_m),
                Quantity(
                    h.heat_transfer_coefficient.to_si() * row.area_ratio**-0.9, UNIT_HTC
                ),
                taw,
                eta,
                unfilmed_taw if at_slot else None,
                0.0 if at_slot else None,
            )
        )
    return tuple(profile), film_flow
