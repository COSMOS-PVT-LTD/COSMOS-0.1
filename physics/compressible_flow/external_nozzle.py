"""Dimensional scaling of a converged external ideal-nozzle solution.

No equilibrium or area-Mach solver is implemented here. NASA CEA supplies
c*, Ve and Pe; these standard relations apply throat area and ambient pressure.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.dimension import AREA, PRESSURE, VELOCITY
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_non_negative, validate_positive
from physics.compressible_flow.thrust_relations import thrust
from physics.exceptions import OutOfRangeError
from physics.quantities import as_si, quantity


@dataclass(frozen=True, slots=True)
class ExternalNozzlePerformance:
    mass_flow: Quantity
    force: Quantity
    thrust_coefficient: float
    specific_impulse_s: float


def scale_external_nozzle(
    chamber_pressure: Quantity, ambient_pressure: Quantity, throat_area: Quantity,
    expansion_ratio: float, cstar: Quantity, exit_velocity: Quantity, exit_pressure: Quantity,
) -> ExternalNozzlePerformance:
    """mdot=Pc At/c*, F=mdot Ve+(Pe-Pa)Ae, Isp=F/(mdot g0)."""
    pc = validate_positive(as_si(chamber_pressure, PRESSURE, "Pc"), "Pc")
    pa = validate_non_negative(as_si(ambient_pressure, PRESSURE, "Pa"), "Pa")
    if pa >= pc:
        raise OutOfRangeError("Ambient pressure must be below chamber pressure for this ideal rocket model.")
    at = validate_positive(as_si(throat_area, AREA, "At"), "At")
    cs = validate_positive(as_si(cstar, VELOCITY, "cstar"), "cstar")
    eps = validate_positive(expansion_ratio, "expansion_ratio")
    mdot = quantity(pc * at / cs, SI.get("kg/s"))
    force = thrust(mdot, exit_velocity, exit_pressure, ambient_pressure, quantity(at * eps, SI.get("m2")))
    if force.to_si() <= 0:
        raise OutOfRangeError("Ideal attached CEA exit state gives non-positive thrust at this ambient pressure; shock/separation modeling is required.")
    return ExternalNozzlePerformance(mdot, force, force.to_si() / (pc * at), force.to_si() / (mdot.to_si() * 9.80665))
