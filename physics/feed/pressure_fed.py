"""Specified-flow liquid pressure budget, not a flow/network/regulator solver."""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import (
    ACCELERATION,
    AREA,
    DENSITY,
    LENGTH,
    MASS_FLOW_RATE,
    PRESSURE,
    VELOCITY,
    Dimension,
)
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from physics.model import ModelIdentity
from physics.quantities import as_si

PRESSURE_FED = ModelIdentity(
    model_id="PHYS-FEED.steady_liquid_pressure_budget",
    model_name="Specified-flow incompressible liquid feed pressure budget",
    physical_domain="feed",
    equations=(
        "Q = mdot/rho; v2 = Q/A2",
        "dp_kinetic = rho*(v2^2-v1^2)/2; dp_elevation = rho*g*(z2-z1)",
        "p1_required = p2_required + dp_kinetic + dp_elevation + sum(dp_loss)",
        "pressure_residual = p1_supplied - p1_required",
        "loss_power = Q*sum(dp_loss)",
        "mass_residual = sum(mdot_in)-sum(mdot_out)",
    ),
    inputs=(
        "mdot [kg/s]",
        "rho [kg/m3]",
        "p1,p2 [Pa absolute]",
        "A2 [m2]",
        "v1 [m/s]",
        "z2-z1 [m]",
        "g [m/s2]",
        "irreversible losses [Pa]",
    ),
    outputs=(
        "Q [m3/s]",
        "v2 [m/s]",
        "required source pressure [Pa absolute]",
        "signed pressure residual [Pa]",
        "dissipated mechanical power [W]",
    ),
    assumptions=(
        "Steady single-phase incompressible liquid with explicit constant density.",
        "Uniform mean-velocity energy correction factors equal one.",
        "Explicit upstream irreversible losses at the specified mass flow; no pump work.",
        "Static absolute station pressures; positive elevation rise is uphill.",
    ),
    validity_range="Positive finite flow/density/area/absolute pressures; nonnegative losses, gravity and speeds.",
    required_properties=("liquid density at declared operating conditions",),
    source=(
        "DOE-HDBK-1012/3-92, HT-03 pp9-11 eq3-1..3-6 and p25 eq3-12; coherent SI pressure form, no pump; "
        "https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL3.pdf"
    ),
    verification_status="independent synthetic pressure/continuity fixtures and dimensional/admissibility regression tests",
    limitations=(
        "Specified-flow budget only; surplus requires an unmodelled control characteristic, not closure.",
        "No local cavitation, phase transition, thermal feedback, compressible liquid or transient prediction.",
        "No pressurant/regulator consumption, tank strength, shaft power or complete engine cycle model.",
        "No physical validation or hardware safety assessment.",
    ),
)


def _si(
    value: Quantity,
    dimension: Dimension,
    name: str,
    *,
    positive: bool = False,
    nonnegative: bool = False,
) -> float:
    if not isinstance(value, Quantity) or isinstance(value.magnitude, bool):
        raise InvalidInputError(
            f"{name} requires a finite Core Quantity, not Boolean/bare input."
        )
    try:
        result = as_si(value, dimension, name)
    except OverflowError as error:
        raise InvalidInputError(f"{name} exceeds representable SI range.") from error
    if (
        not math.isfinite(result)
        or (positive and result <= 0)
        or (nonnegative and result < 0)
    ):
        raise InvalidInputError(
            f"{name} is nonfinite or outside its declared sign domain."
        )
    return result


@dataclass(frozen=True, slots=True)
class PressureLoss:
    """Irreversible pressure-equivalent loss, not a static station delta-p."""

    name: str
    pressure_drop: Quantity


@dataclass(frozen=True, slots=True)
class FeedBudget:
    mass_flow_kg_s: float
    volumetric_flow_m3_s: float
    outlet_velocity_m_s: float
    kinetic_pressure_change_pa: float
    elevation_pressure_change_pa: float
    irreversible_loss_pa: float
    required_source_pressure_pa: float
    supplied_source_pressure_pa: float
    required_sink_pressure_pa: float
    pressure_residual_pa: float
    dissipated_mechanical_power_w: float


def liquid_feed_budget(
    *,
    mass_flow: Quantity,
    density: Quantity,
    source_pressure: Quantity,
    required_sink_pressure: Quantity,
    outlet_area: Quantity,
    source_velocity: Quantity,
    elevation_rise: Quantity,
    gravitational_acceleration: Quantity,
    losses: tuple[PressureLoss, ...],
) -> FeedBudget:
    """Evaluate one imposed-flow path without changing pressures or solving flow."""
    mdot = _si(mass_flow, MASS_FLOW_RATE, "mass_flow", positive=True)
    rho = _si(density, DENSITY, "density", positive=True)
    supplied = _si(source_pressure, PRESSURE, "source_pressure", positive=True)
    sink = _si(
        required_sink_pressure, PRESSURE, "required_sink_pressure", positive=True
    )
    area = _si(outlet_area, AREA, "outlet_area", positive=True)
    v1 = _si(source_velocity, VELOCITY, "source_velocity", nonnegative=True)
    dz = _si(elevation_rise, LENGTH, "elevation_rise")
    gravity = _si(
        gravitational_acceleration,
        ACCELERATION,
        "gravitational_acceleration",
        nonnegative=True,
    )
    if type(losses) is not tuple or not 1 <= len(losses) <= 32:
        raise InvalidInputError(
            "Supply an explicit tuple of 1-32 irreversible losses, including explicit zeros."
        )
    names: set[str] = set()
    drops = []
    for loss in losses:
        if (
            not isinstance(loss, PressureLoss)
            or type(loss.name) is not str
            or not loss.name.strip()
            or len(loss.name) > 80
            or loss.name in names
        ):
            raise InvalidInputError(
                "Loss labels must be unique, nonempty strings of at most 80 characters."
            )
        names.add(loss.name)
        drops.append(_si(loss.pressure_drop, PRESSURE, loss.name, nonnegative=True))
    try:
        volume = mdot / rho
        v2 = volume / area
        kinetic = rho * (v2 - v1) * ((v2 + v1) / 2)
        elevation = rho * gravity * dz
        loss_pa = math.fsum(drops)
        required = math.fsum((sink, kinetic, elevation, loss_pa))
        residual = math.fsum((supplied, -sink, -kinetic, -elevation, -loss_pa))
        power = volume * loss_pa
    except (OverflowError, ValueError, ZeroDivisionError) as error:
        raise InvalidInputError(
            "Feed arithmetic overflow/underflow; rescale explicit inputs."
        ) from error
    values = (volume, v2, kinetic, elevation, loss_pa, required, residual, power)
    if (
        not all(math.isfinite(v) for v in values)
        or volume <= 0
        or v2 <= 0
        or required <= 0
        or (any(drops) and (loss_pa <= 0 or power <= 0))
        or (gravity > 0 and dz != 0 and elevation == 0)
        or (v2 != v1 and kinetic == 0)
    ):
        raise InvalidInputError(
            "Feed result is nonfinite, underflows, or requires nonpositive absolute source pressure."
        )
    return FeedBudget(
        mdot,
        volume,
        v2,
        kinetic,
        elevation,
        loss_pa,
        required,
        supplied,
        sink,
        residual,
        power,
    )


def steady_mass_residual(
    *, inlets: tuple[Quantity, ...], outlets: tuple[Quantity, ...]
) -> float:
    """Signed independent continuity residual; no accumulation or balancing edit."""
    for flows in (inlets, outlets):
        if type(flows) is not tuple or not 1 <= len(flows) <= 32:
            raise InvalidInputError("Supply 1-32 explicit inlet and outlet mass flows.")
    incoming = [_si(flow, MASS_FLOW_RATE, "inlet", nonnegative=True) for flow in inlets]
    outgoing = [
        _si(flow, MASS_FLOW_RATE, "outlet", nonnegative=True) for flow in outlets
    ]
    try:
        result = math.fsum((*incoming, *(-value for value in outgoing)))
    except (ValueError, OverflowError) as error:
        raise InvalidInputError("Mass balance exceeds representable range.") from error
    if not math.isfinite(result):
        raise InvalidInputError("Mass balance is not finite.")
    return result
