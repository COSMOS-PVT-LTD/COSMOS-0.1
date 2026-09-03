"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.cea_interface
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Controlled boundary to an external thermochemical engine.

Description:
    COSMOS physics owns the normalized result contract. NASA CEA (or an
    approved adapter) is an external solver. Adapter implementation details
    must not leak through this API.

    This module does not execute CEA and does not re-implement equilibrium.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from core.quantity import Quantity

from physics.exceptions import InsufficientDataError, ThermochemistryError
from physics.model import ModelIdentity
from physics.validity import ValidityStatus

__all__ = (
    "CEA_INTERFACE",
    "CeaRequest",
    "ThermochemicalResult",
    "ThermochemistryEngine",
    "run_thermochemistry",
)

CEA_INTERFACE = ModelIdentity(
    model_id="PHYS-003.cea.interface",
    model_name="External thermochemistry engine interface",
    physical_domain="thermochemistry",
    equations=("equilibrium or frozen composition from an external engine",),
    inputs=("fuel", "oxidizer", "mixture_ratio [-]", "chamber_pressure [Pa]"),
    outputs=("Tc [K]", "gamma [-]", "molar_mass [kg/mol]", "cstar [m/s]", "products"),
    assumptions=(
        "External engine is the thermochemical authority.",
        "COSMOS validates and normalizes the returned contract.",
    ),
    validity_range="Defined by the external engine and the request state.",
    numerical_method_dependency="external thermochemical solver (CEA or approved)",
    source="NASA CEA (Gordon & McBride, NASA RP-1311) as reference engine.",
    verification_status="interface_only: no built-in CEA execution in this batch",
    limitations=(
        "Does not embed a second thermochemistry solver.",
        "External output is not trusted until validated against this contract.",
    ),
)


@dataclass(frozen=True, slots=True)
class CeaRequest:
    """Normalized request to an external thermochemical engine."""

    fuel_id: str
    oxidizer_id: str
    mixture_ratio: float
    chamber_pressure: Quantity
    equilibrium: bool = True
    notes: str = ""


@dataclass(frozen=True, slots=True)
class ThermochemicalResult:
    """
    Normalized COSMOS thermochemical result.

    External solver fields are flattened into SI quantities. Adapter-specific
    objects are forbidden on this type.
    """

    chamber_temperature: Quantity
    gamma: float
    molar_mass: Quantity
    characteristic_velocity: Quantity | None
    mole_fractions: dict[str, float]
    validity: ValidityStatus
    engine_name: str
    identity: ModelIdentity = CEA_INTERFACE


class ThermochemistryEngine(Protocol):
    """External engine contract. Implementations live outside physics."""

    def evaluate(self, request: CeaRequest) -> ThermochemicalResult:
        """Execute the external engine and return a normalized result."""


def run_thermochemistry(
    request: CeaRequest,
    engine: ThermochemistryEngine | None = None,
) -> ThermochemicalResult:
    """
    Dispatch a thermochemical request.

    Raises
    ------
    InsufficientDataError
        If no engine is provided (the default in this foundation batch).
    """

    if engine is None:
        raise InsufficientDataError(
            "No external thermochemistry engine is bound. COSMOS physics "
            "does not implement a second CEA. Provide a ThermochemistryEngine "
            "adapter (for example plugins/rocketcea) to evaluate "
            f"{request.fuel_id}/{request.oxidizer_id}."
        )
    result = engine.evaluate(request)
    if result.gamma <= 1.0 or result.gamma > 3.0:
        raise ThermochemistryError("External engine returned invalid gamma.")
    return result
