"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.reynolds
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Reynolds number Re = ρ V L / μ.
"""

from __future__ import annotations

from core.dimension import DENSITY, LENGTH, VELOCITY
from core.exceptions import InvalidInputError
from core.quantity import Quantity

from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.si import DYNAMIC_VISCOSITY

__all__ = ("REYNOLDS", "reynolds_number")

REYNOLDS = ModelIdentity(
    model_id="PHYS-002.dimensionless.reynolds",
    model_name="Reynolds number",
    physical_domain="fluids",
    equations=("Re = rho * V * L / mu",),
    inputs=("rho [kg/m3]", "V [m/s]", "L [m]", "mu [Pa s]"),
    outputs=("Re [-]",),
    assumptions=("Single characteristic length and velocity; Newtonian viscosity.",),
    validity_range="rho > 0; L > 0; mu > 0; V >= 0",
    source="Incropera et al.; White, Viscous Fluid Flow.",
    verification_status="dimensional_analysis: Re is dimensionless",
    limitations=("Does not select a turbulence model.",),
)


def reynolds_number(
    density: Quantity,
    velocity: Quantity,
    length: Quantity,
    dynamic_viscosity: Quantity,
) -> float:
    """Return Re = ρ V L / μ."""

    rho = as_si(density, DENSITY, "density")
    vel = as_si(velocity, VELOCITY, "velocity")
    length_si = as_si(length, LENGTH, "length")
    mu = as_si(dynamic_viscosity, DYNAMIC_VISCOSITY, "dynamic_viscosity")
    if rho <= 0.0 or length_si <= 0.0 or mu <= 0.0:
        raise InvalidInputError("Reynolds density, length, and viscosity must be positive.")
    if vel < 0.0:
        raise InvalidInputError("Reynolds velocity must be non-negative.")
    return rho * vel * length_si / mu
