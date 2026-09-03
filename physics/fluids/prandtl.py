"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.prandtl
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Prandtl number Pr = μ Cp / k.
"""

from __future__ import annotations

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import SPECIFIC_HEAT, THERMAL_CONDUCTIVITY, DYNAMIC_VISCOSITY

__all__ = ("PRANDTL", "prandtl_number")

PRANDTL = ModelIdentity(
    model_id="PHYS-002.dimensionless.prandtl",
    model_name="Prandtl number",
    physical_domain="fluids",
    equations=("Pr = mu * Cp / k",),
    inputs=("mu [Pa s]", "Cp [J/(kg K)]", "k [W/(m K)]"),
    outputs=("Pr [-]",),
    assumptions=("Isotropic Newtonian fluid; scalar transport properties.",),
    validity_range="mu > 0; Cp > 0; k > 0",
    source="Incropera et al., Fundamentals of Heat and Mass Transfer.",
    verification_status="dimensional_analysis: Pr is dimensionless",
    limitations=("Mixture Prandtl numbers require mixture properties, not this identity alone.",),
)


def prandtl_number(
    dynamic_viscosity: Quantity,
    specific_heat: Quantity,
    thermal_conductivity: Quantity,
) -> float:
    """Return Pr = μ Cp / k."""

    mu = as_si(dynamic_viscosity, DYNAMIC_VISCOSITY, "dynamic_viscosity")
    cp = as_si(specific_heat, SPECIFIC_HEAT, "specific_heat")
    k = as_si(thermal_conductivity, THERMAL_CONDUCTIVITY, "thermal_conductivity")
    if mu <= 0.0 or cp <= 0.0 or k <= 0.0:
        raise InvalidInputError("Prandtl inputs must be strictly positive.")
    return mu * cp / k


def as_quantity(prandtl: float) -> Quantity:
    """Wrap a Prandtl number as a dimensionless quantity."""

    return quantity(prandtl, SI.get("1"))
