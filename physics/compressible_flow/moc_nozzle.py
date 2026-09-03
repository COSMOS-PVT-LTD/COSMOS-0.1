"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.moc_nozzle
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Physical Method-of-Characteristics relations (not a numerical MOC solver).

Description:
    Mach angle:
        μ = arcsin(1/M)
    Compatibility (2D irrotational isentropic flow):
        C+:  θ + ν = constant
        C−:  θ − ν = constant

    Numerical characteristic marching, mesh generation, and contour
    construction belong to numerics/. This module exposes the physical
    relations required by a future MOC algorithm.

Sources
-------
    Anderson, Modern Compressible Flow (MOC chapter).
    Johns Hopkins / NASA method-of-characteristics nozzle reports
    (design-basis reference for a future numerical implementation).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.exceptions import InvalidInputError

from physics.compressible_flow.expansion_fan import prandtl_meyer
from physics.exceptions import InsufficientDataError
from physics.model import ModelIdentity
from physics.quantities import require_gamma, require_mach

__all__ = (
    "MOC_PHYSICS",
    "CharacteristicInvariants",
    "mach_angle",
    "invariants",
    "generate_contour",
)

MOC_PHYSICS = ModelIdentity(
    model_id="PHYS-004.moc.physical_relations",
    model_name="Method of characteristics physical relations",
    physical_domain="compressible_flow",
    equations=(
        "mu = arcsin(1/M)",
        "C+: theta + nu = const",
        "C-: theta - nu = const",
    ),
    inputs=("M [-]", "theta [rad]", "gamma [-]"),
    outputs=("mu [rad]", "nu [rad]", "C+ [-]", "C- [-]"),
    assumptions=("2D irrotational isentropic flow; calorically perfect.",),
    validity_range="M >= 1",
    numerical_method_dependency="MOC marching belongs to numerics (NUM-CONTRACT-ISSUE)",
    source="Anderson, Modern Compressible Flow; NASA/JHU MOC nozzle reports.",
    verification_status="analytical_verification: mu(1)=pi/2; C+ / C- definitions",
    limitations=(
        "Does not generate a nozzle contour.",
        "Does not discretize the characteristic network.",
    ),
)


@dataclass(frozen=True, slots=True)
class CharacteristicInvariants:
    """Physical C+ / C− invariants at a flow point."""

    mach: float
    mach_angle_rad: float
    prandtl_meyer_rad: float
    flow_angle_rad: float
    c_plus: float
    c_minus: float
    identity: ModelIdentity = MOC_PHYSICS


def mach_angle(mach: float) -> float:
    """Return μ = arcsin(1/M) [rad]."""

    m = require_mach(mach, minimum=1.0)
    return math.asin(1.0 / m)


def invariants(mach: float, flow_angle_rad: float, gamma: float) -> CharacteristicInvariants:
    """Return physical characteristic invariants at one point."""

    m = require_mach(mach, minimum=1.0)
    g = require_gamma(gamma)
    nu = prandtl_meyer(m, g)
    mu = mach_angle(m)
    return CharacteristicInvariants(
        mach=m,
        mach_angle_rad=mu,
        prandtl_meyer_rad=nu,
        flow_angle_rad=flow_angle_rad,
        c_plus=flow_angle_rad + nu,
        c_minus=flow_angle_rad - nu,
    )


def generate_contour(*_args: object, **_kwargs: object) -> None:
    """Contour generation is a numerical algorithm, not a physics model."""

    raise InsufficientDataError(
        "MOC nozzle contour generation is assigned to numerics/. "
        "NUM-CONTRACT-ISSUE: numerics.mesh / numerics.moc marching is not delivered. "
        "Physics provides only mu(M) and C+/C- invariants."
    )


def validate_flow_angle(flow_angle_rad: float) -> float:
    """Reject non-finite flow angles."""

    if not math.isfinite(flow_angle_rad):
        raise InvalidInputError("flow angle must be finite.")
    return flow_angle_rad
