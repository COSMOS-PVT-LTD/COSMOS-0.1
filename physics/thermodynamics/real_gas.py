"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.real_gas
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Real-fluid EOS interface without unsourced cubic coefficients.

Description:
    Real-gas behaviour is expressed through the compressibility factor:

        Z = p / (ρ R T)

    Predictive cubic equations of state (Peng–Robinson, Soave–Redlich–Kwong)
    require sourced critical constants and acentric factors for each fluid.
    Those coefficients are **not invented** here.

    OPEN SCIENTIFIC ISSUE: per-fluid cubic-EOS coefficients from an
    approved NIST / NASA dataset have not been ingested into physics.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.quantity import Quantity

from physics.exceptions import InsufficientDataError
from physics.model import ModelIdentity
from physics.thermodynamics.equations_of_state import compressibility_factor
from physics.validity import ValidityStatus

__all__ = (
    "REAL_GAS_INTERFACE",
    "RealGasEvaluation",
    "evaluate_compressibility",
    "peng_robinson",
)

REAL_GAS_INTERFACE = ModelIdentity(
    model_id="PHYS-001.real_gas.compressibility",
    model_name="Real-gas compressibility interface",
    physical_domain="thermodynamics",
    equations=("Z = p / (rho * R * T)",),
    inputs=("p [Pa]", "rho [kg/m3]", "T [K]", "R [J/(kg K)]"),
    outputs=("Z [-]",),
    assumptions=("Single-phase continuum; R is the specific gas constant.",),
    validity_range="T > 0 K; p > 0 Pa; rho > 0 kg/m3",
    source="Thermal EOS identity. Cubic EOS coefficients: OPEN SCIENTIFIC ISSUE.",
    verification_status="analytical_verification: Z identity only",
    limitations=(
        "No predictive cubic EOS until sourced Tc, pc, ω are provided.",
        "Do not treat Z=1 as a real-fluid result.",
    ),
)


@dataclass(frozen=True, slots=True)
class RealGasEvaluation:
    """Compressibility evaluation with explicit validity."""

    compressibility: float
    validity: ValidityStatus
    identity: ModelIdentity = REAL_GAS_INTERFACE


def evaluate_compressibility(
    pressure: Quantity,
    density: Quantity,
    temperature: Quantity,
    specific_gas_constant: Quantity,
) -> RealGasEvaluation:
    """Evaluate Z from a complete thermodynamic state."""

    z = compressibility_factor(
        pressure,
        density,
        temperature,
        specific_gas_constant,
    )
    return RealGasEvaluation(compressibility=z, validity=ValidityStatus.VALID)


def peng_robinson(*_args: object, **_kwargs: object) -> RealGasEvaluation:
    """
    Peng–Robinson EOS is not executed without sourced coefficients.

    Raises
    ------
    InsufficientDataError
    """

    raise InsufficientDataError(
        "Peng-Robinson coefficients (Tc, pc, acentric factor) are not "
        "sourced in COSMOS physics. OPEN SCIENTIFIC ISSUE: ingest NIST/NASA "
        "critical constants before enabling a cubic EOS."
    )
