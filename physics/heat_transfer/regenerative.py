"""Steady single-phase cooling of a prescribed gas-side profile.

Each constant-property segment uses the exact energy solution. Rib fin heat
transfer is not credited. Public dimensional inputs are Core quantities;
internal/output records use explicit SI suffixes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise

from core.dimension import (
    DENSITY,
    LENGTH,
    MASS_FLOW_RATE,
    PRESSURE,
    TEMPERATURE,
    Dimension,
)
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_non_negative, validate_positive
from physics.exceptions import OutOfRangeError
from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.si import (
    DYNAMIC_VISCOSITY,
    HEAT_TRANSFER_COEFFICIENT,
    SPECIFIC_HEAT,
    THERMAL_CONDUCTIVITY,
)

REGENERATIVE = ModelIdentity(
    model_id="PHYS-COOL.regenerative.segmented_single_phase",
    model_name="Steady segmented regenerative channel model",
    physical_domain="heat_transfer",
    equations=(
        "Dh = 2 w d / (w+d); u = mdot/(rho N w d)",
        "Nu = 0.023 Re^0.8 Pr^0.4; f_D = 0.3164 Re^-0.25",
        "U_hot^-1 = 1/hg + t/k_wall + (A_hot/A_cold)/hc",
        "T_out = Taw - (Taw-T_in) exp(-U_hot A_hot/(mdot Cp))",
        "delta_p = f_D (ds/Dh) rho u^2/2; Q = mdot Cp (T_out-T_in)",
    ),
    inputs=(
        "gas profile x,r,hg,Taw (Core quantities)",
        "rectangular channel geometry",
        "coolant inlet state and constant rho,mu,k,Cp",
        "property/phase/temperature limits",
    ),
    outputs=(
        "coolant/wall temperatures",
        "heat pickup [W]",
        "pressure loss [Pa]",
        "energy residual [W]",
    ),
    assumptions=(
        "Steady single-phase incompressible coolant; constant properties in a declared window.",
        "Smooth fully developed turbulent channels; hydraulic-diameter approximation for rectangles.",
        "1D planar ligament conduction; uniform circumferential temperatures.",
        "Gas h and Taw prescribed; no gas energy or Bartz wall-temperature iteration.",
        "Channel bottom only: rib/sidewall fin enhancement is not credited.",
    ),
    validity_range="10000 <= Re <= 100000; 0.7 <= Pr <= 160; path/Dh >= 10; t/r <= 0.1; declared single-phase limits",
    source="NASA SP-125 cooling energy/resistance balances; Dittus-Boelter heating relation (NASA TP-2232, 19840013760); Darcy-Blasius smooth-pipe relation.",
    verification_status="analytical constant-profile solution, energy/pressure balances and grid convergence tests",
    limitations=(
        "No boiling, supercritical properties, coking, roughness, manifolds, radiation, transient heating or thermal stress.",
        "Only the supplied gas-side profile is cooled; no implicit chamber/convergent coverage.",
        "Pressure loss and heat pickup are not a closed engine cycle balance.",
    ),
)


@dataclass(frozen=True, slots=True)
class GasWallStation:
    x: Quantity
    radius: Quantity
    coefficient: Quantity
    adiabatic_temperature: Quantity
    film_effectiveness: float = 0.0
    upstream_adiabatic_temperature: Quantity | None = None
    upstream_film_effectiveness: float | None = None


@dataclass(frozen=True, slots=True)
class CoolingInputs:
    mass_flow: Quantity
    inlet_temperature: Quantity
    inlet_pressure: Quantity
    density: Quantity
    viscosity: Quantity
    conductivity: Quantity
    specific_heat: Quantity
    channel_width: Quantity
    channel_depth: Quantity
    rib_width: Quantity
    channel_count: int
    wall_thickness: Quantity
    wall_conductivity: Quantity
    min_temperature: Quantity
    max_temperature: Quantity
    max_wall_temperature: Quantity
    max_vapour_pressure: Quantity
    direction: str


@dataclass(frozen=True, slots=True)
class CoolingSegment:
    x_m: float
    radius_m: float
    path_length_m: float
    gas_coefficient_w_m2_k: float
    gas_adiabatic_temperature_k: float
    coolant_in_temperature_k: float
    coolant_out_temperature_k: float
    coolant_out_pressure_pa: float
    hot_wall_temperature_k: float
    cold_wall_temperature_k: float
    heat_flux_w_m2: float
    heat_w: float
    pressure_loss_pa: float
    film_effectiveness: float
    peak_hot_wall_temperature_k: float
    peak_cold_wall_temperature_k: float


@dataclass(frozen=True, slots=True)
class CoolingEvaluation:
    segments: tuple[CoolingSegment, ...]
    reynolds: float
    prandtl: float
    nusselt: float
    darcy_friction_factor: float
    hydraulic_diameter_m: float
    coolant_coefficient_w_m2_k: float
    velocity_m_s: float
    total_heat_w: float
    total_pressure_loss_pa: float
    outlet_temperature_k: float
    outlet_pressure_pa: float
    energy_residual_w: float


def regenerative_cooling(
    stations: tuple[GasWallStation, ...], inputs: CoolingInputs
) -> CoolingEvaluation:
    def positive(q: Quantity, dimension: Dimension, name: str) -> float:
        return validate_positive(as_si(q, dimension, name), name)

    mdot = positive(inputs.mass_flow, MASS_FLOW_RATE, "mass_flow")
    tin = positive(inputs.inlet_temperature, TEMPERATURE, "inlet_temperature")
    pin = positive(inputs.inlet_pressure, PRESSURE, "inlet_pressure")
    rho = positive(inputs.density, DENSITY, "density")
    mu = positive(inputs.viscosity, DYNAMIC_VISCOSITY, "viscosity")
    kc = positive(inputs.conductivity, THERMAL_CONDUCTIVITY, "conductivity")
    cp = positive(inputs.specific_heat, SPECIFIC_HEAT, "specific_heat")
    width = positive(inputs.channel_width, LENGTH, "channel_width")
    depth = positive(inputs.channel_depth, LENGTH, "channel_depth")
    rib = positive(inputs.rib_width, LENGTH, "rib_width")
    wall = positive(inputs.wall_thickness, LENGTH, "wall_thickness")
    kw = positive(inputs.wall_conductivity, THERMAL_CONDUCTIVITY, "wall_conductivity")
    tmin = positive(inputs.min_temperature, TEMPERATURE, "min_temperature")
    tmax = positive(inputs.max_temperature, TEMPERATURE, "max_temperature")
    twmax = positive(inputs.max_wall_temperature, TEMPERATURE, "max_wall_temperature")
    pv = validate_non_negative(
        as_si(inputs.max_vapour_pressure, PRESSURE, "max_vapour_pressure"),
        "max_vapour_pressure",
    )
    n = inputs.channel_count
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 100000:
        raise InvalidInputError("channel_count must be an integer from 1 to 100000.")
    if inputs.direction not in {"exit_to_throat", "throat_to_exit"}:
        raise InvalidInputError(
            "Specify exit_to_throat or throat_to_exit coolant direction."
        )
    if tmin >= tmax or not tmin <= tin <= tmax or pin <= pv:
        raise OutOfRangeError(
            "Coolant inlet is outside the declared property/single-phase window."
        )
    if not 2 <= len(stations) <= 1002:
        raise InvalidInputError(
            "Require 2 to 1002 gas-wall stations (including an inserted film slot)."
        )
    profile = []
    for s in stations:
        x = as_si(s.x, LENGTH, "station x")
        r = positive(s.radius, LENGTH, "station radius")
        hg = positive(s.coefficient, HEAT_TRANSFER_COEFFICIENT, "gas coefficient")
        taw = positive(s.adiabatic_temperature, TEMPERATURE, "adiabatic temperature")
        if (
            not math.isfinite(x)
            or not math.isfinite(s.film_effectiveness)
            or not 0 <= s.film_effectiveness <= 1
        ):
            raise InvalidInputError("Invalid gas-wall station.")
        if n * (width + rib) > 2 * math.pi * (r + wall):
            raise OutOfRangeError(
                "Channel widths plus ribs do not fit the local circumference."
            )
        if wall / r > 0.1:
            raise OutOfRangeError(
                "Planar wall conduction requires wall thickness/radius <= 0.1."
            )
        taw_left = (
            taw
            if s.upstream_adiabatic_temperature is None
            else positive(s.upstream_adiabatic_temperature, TEMPERATURE, "upstream Taw")
        )
        eta_left = (
            s.film_effectiveness
            if s.upstream_film_effectiveness is None
            else s.upstream_film_effectiveness
        )
        if not math.isfinite(eta_left) or not 0 <= eta_left <= 1:
            raise InvalidInputError("Invalid upstream film effectiveness.")
        profile.append((x, r, hg, taw, s.film_effectiveness, taw_left, eta_left))
    if any(b[0] <= a[0] for a, b in pairwise(profile)):
        raise InvalidInputError("Gas-wall x coordinates must strictly increase.")
    dh = 2 * width * depth / (width + depth)
    velocity = mdot / (rho * n * width * depth)
    reynolds = rho * velocity * dh / mu
    prandtl = mu * cp / kc
    if not 1e4 <= reynolds <= 1e5 or not 0.7 <= prandtl <= 160:
        raise OutOfRangeError(
            f"Smooth-channel Dittus-Boelter/Blasius window exceeded: Re={reynolds:g}, Pr={prandtl:g}."
        )
    nu = 0.023 * reynolds**0.8 * prandtl**0.4
    hc = nu * kc / dh
    friction = 0.3164 * reynolds**-0.25
    total_length = sum(
        math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in pairwise(profile)
    )
    if total_length / dh < 10:
        raise OutOfRangeError(
            "Fully developed model requires coolant path/Dh >= 10; entrance losses are not modeled."
        )
    if inputs.direction == "exit_to_throat":
        # Swap one-sided limits when traversing in the opposite direction.
        profile = [
            (x, r, h, tl, el, tr, er) for x, r, h, tr, er, tl, el in reversed(profile)
        ]
    temperature, pressure = tin, pin
    segments = []
    for a, b in pairwise(profile):
        ds = math.hypot(b[0] - a[0], b[1] - a[1])
        radius, hg = (a[1] + b[1]) / 2, (a[2] + b[2]) / 2
        taw, eta = (a[3] + b[5]) / 2, (a[4] + b[6]) / 2
        ahot = 2 * math.pi * radius * ds
        acold = n * width * ds
        uhot = 1 / (1 / hg + wall / kw + ahot / (acold * hc))
        if taw <= temperature:
            raise OutOfRangeError(
                "Coolant reaches/exceeds gas adiabatic wall temperature; heating correlation is inapplicable."
            )
        rise = (taw - temperature) * -math.expm1(-uhot * ahot / (mdot * cp))
        heat = mdot * cp * rise
        q = heat / ahot
        hot_wall = taw - q / hg
        cold_wall = hot_wall - q * wall / kw
        peak_flux = uhot * (taw - temperature - rise)
        peak_hot_wall = taw - peak_flux / hg
        peak_cold_wall = peak_hot_wall - peak_flux * wall / kw
        loss = friction * ds / dh * rho * velocity**2 / 2
        if not tmin <= temperature + rise <= tmax or peak_cold_wall > tmax:
            raise OutOfRangeError(
                "Coolant bulk or coolant-side wall exceeds declared single-phase/property temperature window."
            )
        if peak_hot_wall > twmax or pressure - loss <= pv:
            raise OutOfRangeError(
                "Wall temperature limit or coolant vapour-pressure margin exceeded."
            )
        row = CoolingSegment(
            (a[0] + b[0]) / 2,
            radius,
            ds,
            hg,
            taw,
            temperature,
            temperature + rise,
            pressure - loss,
            hot_wall,
            cold_wall,
            q,
            heat,
            loss,
            eta,
            peak_hot_wall,
            peak_cold_wall,
        )
        if not all(
            math.isfinite(v)
            for v in (rise, heat, q, hot_wall, cold_wall, pressure - loss)
        ):
            raise InvalidInputError("Cooling calculation produced a non-finite value.")
        segments.append(row)
        temperature += rise
        pressure -= loss
    total_heat = sum(s.heat_w for s in segments)
    return CoolingEvaluation(
        tuple(segments),
        reynolds,
        prandtl,
        nu,
        friction,
        dh,
        hc,
        velocity,
        total_heat,
        sum(s.pressure_loss_pa for s in segments),
        temperature,
        pressure,
        total_heat - mdot * cp * (temperature - tin),
    )
