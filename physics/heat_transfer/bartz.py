"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.bartz
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Bartz rocket-nozzle gas-side heat-transfer correlation (SI form).

Description:
    The original Bartz (1957) dimensional coefficient is unit-system
    dependent. COSMOS implements the unit-safe Nusselt origin:

        Nu_D = 0.026 Re_D^{0.8} Pr^{0.4}

        h = Nu_D * k / D

    with throat mass flux G* = p_c / c* as the Bartz substitution for
    ρ u, and a property-variation factor σ:

        σ = 1 / [ 0.5 T_w/T_aw * (1 + ((γ-1)/2) M^2) + 0.5 ]^{0.68}
            / [ 1 + ((γ-1)/2) M^2 ]^{0.12}

    The correlation identity, assumptions, and validity are explicit.
    This is an engineering correlation, not a first-principles wall law.

Sources
-------
    Bartz, D. R., "A Simple Equation for Rapid Estimation of Rocket
    Nozzle Convective Heat Transfer Coefficients," Jet Propulsion, 1957.
    Huzel & Huang, NASA SP-125.
    Incropera et al. (pipe-flow Nu-Re-Pr origin of the 0.026 coefficient).
"""

from __future__ import annotations

from dataclasses import dataclass

from core.dimension import LENGTH, PRESSURE, TEMPERATURE, VELOCITY
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity, require_gamma, require_mach
from physics.si import (
    DYNAMIC_VISCOSITY,
    SPECIFIC_HEAT,
    THERMAL_CONDUCTIVITY,
    UNIT_HTC,
)
from physics.validity import ValidityStatus

__all__ = (
    "BARTZ",
    "BartzEvaluation",
    "bartz_heat_transfer_coefficient",
    "sigma_correction",
)

BARTZ = ModelIdentity(
    model_id="PHYS-005.bartz.nusselt_si",
    model_name="Bartz nozzle heat-transfer correlation (SI Nusselt form)",
    physical_domain="heat_transfer",
    equations=(
        "Nu_D = 0.026 * Re_D**0.8 * Pr**0.4",
        "Re_D = G * D / mu",
        "G* = p_c / cstar  (throat mass flux substitution)",
        "h = (Nu_D * k / D) * sigma * (D / R)**0.1  when R supplied",
    ),
    inputs=(
        "D [m]",
        "R [m] optional nozzle radius of curvature for (D/R)**0.1",
        "mu [Pa s]",
        "k [W/(m K)]",
        "Cp [J/(kg K)]",
        "p_c [Pa]",
        "cstar [m/s]",
        "M [-]",
        "gamma [-]",
        "T_w [K]",
        "T_aw [K]",
    ),
    outputs=("h [W/(m2 K)]",),
    assumptions=(
        "Pipe-flow Nu=0.026 Re^0.8 Pr^0.4 origin.",
        "Throat mass flux G* = p_c / c* represents ρu.",
        "Calorically perfect σ correction.",
        "No knowledge of a specific engine or chamber design method.",
    ),
    validity_range=(
        "Turbulent pipe-flow Re typically > 1e4; rocket-nozzle gas side; "
        "correlation uncertainty is historical (order 10-25%), not claimed as 2%."
    ),
    source=(
        "Bartz 1957; Huzel & Huang NASA SP-125; Incropera Nu-Re-Pr origin."
    ),
    verification_status=(
        "analytical_verification: Nu dimensions; Re=ρUD/μ; σ(M=0,Tw=Taw)=1; "
        "reference: software verification against the stated SI equations. "
        "Not experimental validation."
    ),
    limitations=(
        "Empirical; do not treat as first-principles CFD.",
        "The 0.026 coefficient is from the dimensionless Nu relation, "
        "not the English-unit Bartz dimensional package.",
        "Film cooling and roughness are not included.",
    ),
)


@dataclass(frozen=True, slots=True)
class BartzEvaluation:
    """Bartz correlation result with traceability."""

    heat_transfer_coefficient: Quantity
    nusselt: float
    reynolds: float
    prandtl: float
    sigma: float
    curvature_factor: float
    validity: ValidityStatus
    identity: ModelIdentity = BARTZ


def sigma_correction(
    mach: float,
    gamma: float,
    wall_temperature: Quantity,
    adiabatic_wall_temperature: Quantity,
) -> float:
    """Return the Bartz property-variation factor σ."""

    m = require_mach(mach)
    g = require_gamma(gamma)
    tw = validate_positive(as_si(wall_temperature, TEMPERATURE, "T_w"), "T_w")
    taw = validate_positive(
        as_si(adiabatic_wall_temperature, TEMPERATURE, "T_aw"),
        "T_aw",
    )
    recovery = 1.0 + 0.5 * (g - 1.0) * m * m
    inner = 0.5 * (tw / taw) * recovery + 0.5
    return 1.0 / (inner ** 0.68 * recovery ** 0.12)


def bartz_heat_transfer_coefficient(
    diameter: Quantity,
    viscosity: Quantity,
    conductivity: Quantity,
    specific_heat: Quantity,
    chamber_pressure: Quantity,
    characteristic_velocity: Quantity,
    mach: float,
    gamma: float,
    wall_temperature: Quantity,
    adiabatic_wall_temperature: Quantity,
    *,
    curvature_radius: Quantity | None = None,
) -> BartzEvaluation:
    """
    Evaluate the SI Bartz heat-transfer coefficient.

    Throat mass flux G* = p_c / c* is used as the Bartz ρu substitution.
    """

    d = validate_positive(as_si(diameter, LENGTH, "diameter"), "diameter")
    mu = validate_positive(as_si(viscosity, DYNAMIC_VISCOSITY, "viscosity"), "mu")
    k = validate_positive(
        as_si(conductivity, THERMAL_CONDUCTIVITY, "conductivity"),
        "k",
    )
    cp = validate_positive(as_si(specific_heat, SPECIFIC_HEAT, "Cp"), "Cp")
    pc = validate_positive(
        as_si(chamber_pressure, PRESSURE, "chamber_pressure"),
        "p_c",
    )
    cstar = validate_positive(
        as_si(characteristic_velocity, VELOCITY, "characteristic_velocity"),
        "cstar",
    )
    g_star = pc / cstar
    reynolds = g_star * d / mu
    prandtl = mu * cp / k
    if reynolds <= 0.0 or prandtl <= 0.0:
        raise InvalidInputError("Bartz Re and Pr must be positive.")
    nusselt = 0.026 * reynolds**0.8 * prandtl**0.4
    sigma = sigma_correction(
        mach,
        gamma,
        wall_temperature,
        adiabatic_wall_temperature,
    )
    curvature_factor = 1.0
    if curvature_radius is not None:
        radius = validate_positive(
            as_si(curvature_radius, LENGTH, "curvature_radius"),
            "curvature_radius",
        )
        curvature_factor = (d / radius) ** 0.1
    h = nusselt * k / d * sigma * curvature_factor
    validity = (
        ValidityStatus.VALID if reynolds >= 1.0e4 else ValidityStatus.OUT_OF_RANGE
    )
    return BartzEvaluation(
        heat_transfer_coefficient=quantity(h, UNIT_HTC),
        nusselt=nusselt,
        reynolds=reynolds,
        prandtl=prandtl,
        sigma=sigma,
        curvature_factor=curvature_factor,
        validity=validity,
    )
