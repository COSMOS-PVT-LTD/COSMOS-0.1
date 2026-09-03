"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.first_law
Author: COSMOS Development Team
Version: 0.1.0
Purpose: First law of thermodynamics energy balances.

Description:
    Closed-system convention used by COSMOS:

        ΔU = Q - W

    Q is heat transfer *to* the system; W is work *done by* the system.

    Steady-flow specific energy residual:

        h2 - h1 + (V2^2 - V1^2)/2 + g (z2 - z1) - q + w_shaft = 0

Sources
-------
    Cengel & Boles, Thermodynamics: An Engineering Approach.
    Moran & Shapiro, Fundamentals of Engineering Thermodynamics.
"""

from __future__ import annotations

from core.dimension import ACCELERATION, ENERGY, LENGTH, VELOCITY
from core.quantity import Quantity
from core.unit import SI

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import SPECIFIC_ENERGY, UNIT_SPECIFIC_ENERGY

__all__ = (
    "FIRST_LAW_CLOSED",
    "closed_system_delta_u",
    "steady_flow_energy_residual",
    "specific_energy",
)

FIRST_LAW_CLOSED = ModelIdentity(
    model_id="PHYS-001.first_law.closed",
    model_name="First law, closed system (heat-in work-out)",
    physical_domain="thermodynamics",
    equations=("Delta U = Q - W",),
    inputs=("heat_in [J]", "work_out [J]"),
    outputs=("delta_internal_energy [J]",),
    assumptions=(
        "Closed system (no mass flow).",
        "Heat-in / work-out sign convention.",
    ),
    validity_range="Finite energy transfers; path-independent first-law statement.",
    source="Cengel & Boles; Moran & Shapiro (closed-system first law).",
    verification_status="analytical_verification: adiabatic ΔU = -W; workless ΔU = Q",
    limitations=("Do not mix with heat-out / work-in sign conventions.",),
)


def closed_system_delta_u(heat_in: Quantity, work_out: Quantity) -> Quantity:
    """Return ΔU = Q - W for a closed system."""

    q = as_si(heat_in, ENERGY, "heat_in")
    w = as_si(work_out, ENERGY, "work_out")
    return quantity(q - w, SI.get("J"))


def steady_flow_energy_residual(
    delta_enthalpy: Quantity,
    velocity_in: Quantity,
    velocity_out: Quantity,
    height_in: Quantity,
    height_out: Quantity,
    heat_in_specific: Quantity,
    shaft_work_out_specific: Quantity,
    gravity: Quantity,
) -> float:
    """
    Return the specific steady-flow energy residual [J/kg].

    A satisfied energy balance returns 0 within floating-point roundoff.
    """

    dh = as_si(delta_enthalpy, SPECIFIC_ENERGY, "delta_enthalpy")
    v1 = as_si(velocity_in, VELOCITY, "velocity_in")
    v2 = as_si(velocity_out, VELOCITY, "velocity_out")
    z1 = as_si(height_in, LENGTH, "height_in")
    z2 = as_si(height_out, LENGTH, "height_out")
    q = as_si(heat_in_specific, SPECIFIC_ENERGY, "heat_in_specific")
    w = as_si(shaft_work_out_specific, SPECIFIC_ENERGY, "shaft_work_out_specific")
    g = as_si(gravity, ACCELERATION, "gravity")
    return dh + 0.5 * (v2 * v2 - v1 * v1) + g * (z2 - z1) - q + w


def specific_energy(value: float) -> Quantity:
    """Construct a specific-energy quantity [J/kg]."""

    from core.validation import validate_finite

    return quantity(validate_finite(value, "specific_energy"), UNIT_SPECIFIC_ENERGY)
