"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.sutherland
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Sutherland viscosity correlation for dilute gases.

Description:
    μ(T) = μ_ref * (T/T_ref)**1.5 * (T_ref + S) / (T + S)

    The coefficient 0.026 in some engineering forms is not used here.
    Constants are per-gas and must be sourced. Temperature outside the
    documented window is reported, not clamped.

Sources
-------
    Sutherland, W., "The viscosity of gases and molecular force,"
    Philosophical Magazine, 1893.
    White, F. M., Viscous Fluid Flow (Sutherland constants).
    Incropera, DeWitt, Bergman, Lavine, Fundamentals of Heat and Mass Transfer
    (air viscosity table cross-check).
"""

from __future__ import annotations

from dataclasses import dataclass

from core.dimension import TEMPERATURE
from core.quantity import Quantity
from core.validation import validate_positive

from physics.exceptions import OutOfRangeError
from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import UNIT_DYNAMIC_VISCOSITY
from physics.validity import ValidityStatus

__all__ = (
    "SUTHERLAND_MODEL",
    "SutherlandLaw",
    "evaluate_sutherland",
)

SUTHERLAND_MODEL = ModelIdentity(
    model_id="PHYS-002.viscosity.sutherland",
    model_name="Sutherland dynamic viscosity",
    physical_domain="fluids",
    equations=(
        "mu = mu_ref * (T/T_ref)**(3/2) * (T_ref + S) / (T + S)",
    ),
    inputs=("T [K]", "mu_ref [Pa s]", "T_ref [K]", "S [K]"),
    outputs=("mu [Pa s]",),
    assumptions=(
        "Dilute gas; continuum; moderate pressure (density effects neglected).",
        "Constants are gas-specific and sourced.",
    ),
    validity_range="Per-gas temperature window; typically ~170 K to ~1900 K for air.",
    source="Sutherland 1893; White, Viscous Fluid Flow; Incropera et al.",
    verification_status="analytical_verification: mu(T_ref)=mu_ref; monotonic in T for S>0",
    limitations=(
        "Not valid for liquids or dense supercritical states.",
        "Not a substitute for kinetic-theory mixture viscosity.",
    ),
)


@dataclass(frozen=True, slots=True)
class SutherlandLaw:
    """Sourced Sutherland constants for one gas."""

    fluid_id: str
    mu_ref_pa_s: float
    t_ref_k: float
    sutherland_k: float
    temperature_min_k: float
    temperature_max_k: float
    source: str


@dataclass(frozen=True, slots=True)
class SutherlandEvaluation:
    """Sutherland viscosity with validity."""

    viscosity: Quantity
    validity: ValidityStatus
    identity: ModelIdentity = SUTHERLAND_MODEL


def evaluate_sutherland(
    law: SutherlandLaw,
    temperature: Quantity,
    *,
    allow_extrapolation: bool = False,
) -> SutherlandEvaluation:
    """Evaluate μ(T) with explicit range status."""

    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    in_range = law.temperature_min_k <= t <= law.temperature_max_k
    if not in_range and not allow_extrapolation:
        raise OutOfRangeError(
            f"Sutherland viscosity for {law.fluid_id} is tabulated for "
            f"[{law.temperature_min_k}, {law.temperature_max_k}] K."
        )
    mu = (
        law.mu_ref_pa_s
        * (t / law.t_ref_k) ** 1.5
        * (law.t_ref_k + law.sutherland_k)
        / (t + law.sutherland_k)
    )
    validity = ValidityStatus.VALID if in_range else ValidityStatus.EXTRAPOLATED
    return SutherlandEvaluation(
        viscosity=quantity(mu, UNIT_DYNAMIC_VISCOSITY),
        validity=validity,
    )


# Published air constants: Incropera et al. / White. μ_ref at 273.15 K.
AIR_SUTHERLAND = SutherlandLaw(
    fluid_id="air",
    mu_ref_pa_s=1.716e-5,
    t_ref_k=273.15,
    sutherland_k=110.4,
    temperature_min_k=170.0,
    temperature_max_k=1900.0,
    source=(
        "White, Viscous Fluid Flow; Incropera et al., Fundamentals of "
        "Heat and Mass Transfer (air Sutherland constants)."
    ),
)

NITROGEN_SUTHERLAND = SutherlandLaw(
    fluid_id="nitrogen",
    mu_ref_pa_s=1.663e-5,
    t_ref_k=273.15,
    sutherland_k=107.0,
    temperature_min_k=200.0,
    temperature_max_k=1500.0,
    source="White, Viscous Fluid Flow (nitrogen Sutherland constants).",
)

OXYGEN_SUTHERLAND = SutherlandLaw(
    fluid_id="oxygen",
    mu_ref_pa_s=1.919e-5,
    t_ref_k=273.15,
    sutherland_k=139.0,
    temperature_min_k=200.0,
    temperature_max_k=1500.0,
    source="White, Viscous Fluid Flow (oxygen Sutherland constants).",
)

HYDROGEN_SUTHERLAND = SutherlandLaw(
    fluid_id="hydrogen",
    mu_ref_pa_s=8.411e-6,
    t_ref_k=273.15,
    sutherland_k=97.0,
    temperature_min_k=200.0,
    temperature_max_k=1200.0,
    source="White, Viscous Fluid Flow (hydrogen Sutherland constants).",
)

METHANE_SUTHERLAND = SutherlandLaw(
    fluid_id="methane",
    mu_ref_pa_s=1.024e-5,
    t_ref_k=273.15,
    sutherland_k=164.0,
    temperature_min_k=200.0,
    temperature_max_k=1000.0,
    source="White, Viscous Fluid Flow (methane Sutherland constants).",
)

HELIUM_SUTHERLAND = SutherlandLaw(
    fluid_id="helium",
    mu_ref_pa_s=1.870e-5,
    t_ref_k=273.15,
    sutherland_k=79.4,
    temperature_min_k=200.0,
    temperature_max_k=1500.0,
    source="White, Viscous Fluid Flow (helium Sutherland constants).",
)
