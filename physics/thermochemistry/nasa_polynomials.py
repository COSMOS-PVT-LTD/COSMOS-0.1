"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.nasa_polynomials
Author: COSMOS Development Team
Version: 0.1.0
Purpose: NASA 7-coefficient thermodynamic polynomial evaluation.

Description:
    NASA7 (Chemkin / classic CEA) standard-state relations:

        Cp/R = a1 + a2 T + a3 T^2 + a4 T^3 + a5 T^4
        H/RT = a1 + a2 T/2 + a3 T^2/3 + a4 T^3/4 + a5 T^4/5 + a6/T
        S/R  = a1 ln T + a2 T + a3 T^2/2 + a4 T^3/3 + a5 T^4/4 + a7

    Two temperature intervals with a midpoint (typically 1000 K).
    Evaluation outside [Tmin, Tmax] is rejected unless extrapolation
    is explicitly requested.

Sources
-------
    McBride, B. J., Gordon, S., and Reno, M. A., NASA TM-4513, 1993.
    Gordon, S., and McBride, B. J., NASA RP-1311, 1994 (CEA).
    Species coefficients: GRI-Mech 3.0 thermodynamic database
    (Smith, Golden, Frenklach et al.), NASA polynomial format.
    Helium monatomic Cp/R = 5/2 from kinetic theory (not GRI).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.constants import UNIVERSAL_GAS_CONSTANT
from core.dimension import TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_positive

from physics.exceptions import OutOfRangeError
from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import UNIT_MOLAR_ENERGY, UNIT_MOLAR_ENTROPY
from physics.validity import ValidityStatus

__all__ = (
    "NASA7",
    "NASA7_MODEL",
    "NASA7Evaluation",
    "evaluate_nasa7",
)

NASA7_MODEL = ModelIdentity(
    model_id="PHYS-003.nasa7.standard_state",
    model_name="NASA 7-coefficient polynomials",
    physical_domain="thermochemistry",
    equations=(
        "Cp/R = a1 + a2 T + a3 T^2 + a4 T^3 + a5 T^4",
        "H/RT = a1 + a2 T/2 + a3 T^2/3 + a4 T^3/4 + a5 T^4/5 + a6/T",
        "S/R = a1 ln T + a2 T + a3 T^2/2 + a4 T^3/3 + a5 T^4/4 + a7",
    ),
    inputs=("T [K]", "coefficients a1..a7 per interval"),
    outputs=("Cp [J/(mol K)]", "H [J/mol]", "S [J/(mol K)]"),
    assumptions=(
        "Ideal-gas standard state at 1 bar as encoded by the coefficient set.",
        "H includes the formation contribution stored in a6.",
    ),
    validity_range="Per-species Tmin to Tmax; midpoint selects the interval.",
    source="NASA TM-4513 / NASA RP-1311; GRI-Mech 3.0 NASA7 coefficients.",
    verification_status="analytical_verification: Cp/R at Tref; interval continuity checks",
    limitations=(
        "Not a condensed-phase model.",
        "GRI-Mech Tmin may be 300 K; 298.15 K may be OUT_OF_RANGE.",
    ),
)


@dataclass(frozen=True, slots=True)
class NASA7:
    """Two-interval NASA 7-coefficient set."""

    species_id: str
    t_min_k: float
    t_mid_k: float
    t_max_k: float
    low: tuple[float, float, float, float, float, float, float]
    high: tuple[float, float, float, float, float, float, float]
    source: str

    def coefficients_at(self, temperature_k: float) -> tuple[float, ...]:
        """Return the coefficient tuple for ``temperature_k`` without range checks."""

        if temperature_k < self.t_mid_k:
            return self.low
        return self.high


@dataclass(frozen=True, slots=True)
class NASA7Evaluation:
    """Standard-state molar properties at one temperature."""

    species_id: str
    temperature: Quantity
    cp_molar: Quantity
    enthalpy_molar: Quantity
    entropy_molar: Quantity
    cp_over_r: float
    validity: ValidityStatus
    identity: ModelIdentity = NASA7_MODEL


def _cp_over_r(a: tuple[float, ...], t: float) -> float:
    return a[0] + a[1] * t + a[2] * t * t + a[3] * t**3 + a[4] * t**4


def _h_over_rt(a: tuple[float, ...], t: float) -> float:
    return (
        a[0]
        + a[1] * t / 2.0
        + a[2] * t * t / 3.0
        + a[3] * t**3 / 4.0
        + a[4] * t**4 / 5.0
        + a[5] / t
    )


def _s_over_r(a: tuple[float, ...], t: float) -> float:
    return (
        a[0] * math.log(t)
        + a[1] * t
        + a[2] * t * t / 2.0
        + a[3] * t**3 / 3.0
        + a[4] * t**4 / 4.0
        + a[6]
    )


def evaluate_nasa7(
    polynomial: NASA7,
    temperature: Quantity,
    *,
    allow_extrapolation: bool = False,
) -> NASA7Evaluation:
    """Evaluate Cp, H, S at ``temperature``."""

    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    in_range = polynomial.t_min_k <= t <= polynomial.t_max_k
    if not in_range and not allow_extrapolation:
        raise OutOfRangeError(
            f"NASA7 {polynomial.species_id} valid on "
            f"[{polynomial.t_min_k}, {polynomial.t_max_k}] K."
        )
    if t == 0.0:
        raise InvalidInputError("temperature must be positive.")
    coeffs = polynomial.coefficients_at(t)
    cp_r = _cp_over_r(coeffs, t)
    h_rt = _h_over_rt(coeffs, t)
    s_r = _s_over_r(coeffs, t)
    r = UNIVERSAL_GAS_CONSTANT
    validity = ValidityStatus.VALID if in_range else ValidityStatus.EXTRAPOLATED
    return NASA7Evaluation(
        species_id=polynomial.species_id,
        temperature=temperature,
        cp_molar=quantity(cp_r * r, UNIT_MOLAR_ENTROPY),
        enthalpy_molar=quantity(h_rt * r * t, UNIT_MOLAR_ENERGY),
        entropy_molar=quantity(s_r * r, UNIT_MOLAR_ENTROPY),
        cp_over_r=cp_r,
        validity=validity,
    )
