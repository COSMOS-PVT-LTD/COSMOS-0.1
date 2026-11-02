"""Axial preloaded bolt-group screen while the joint remains in contact.

Not flange bending, pressure-vessel code compliance, torque or seal qualification.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import AREA, FORCE, LENGTH, PRESSURE, Dimension
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.validation import validate_non_negative, validate_positive
from physics.exceptions import OutOfRangeError
from physics.model import ModelIdentity
from physics.quantities import as_si

AXIAL_BOLT_GROUP = ModelIdentity(
    model_id="PHYS-JOINT.preloaded_axial_group",
    model_name="Contact-limited preloaded axial bolt-group screen",
    physical_domain="solid_mechanics",
    equations=("F_pressure=(Pi-Po)*pi*r_effective_seal²; F_external=F_pressure+F_axial",
               "C=Kb/(Kb+Kmember); F_bolt,max=preload_max+C*F_external/N",
               "F_clamp,min=N*preload_min-(1-C)*F_external; stress=F_bolt,max/At"),
    inputs=("absolute pressures [Pa]", "effective pressure/seal radius [m]", "bolt count and tensile area [m2]",
            "per-bolt stiffnesses [N/m]", "retained service preload interval [N/bolt]", "service allowable [Pa]", "required seal seating force [N]"),
    outputs=("pressure separating load [N]", "retained clamp [N]", "bolt stress [Pa] if contact remains", "declared-screen pass/fail"),
    assumptions=("Identical bolts with uniform purely axial load sharing; linear elastic stiffnesses.",
                 "Supplied preload bounds already include installation scatter, relaxation and thermal effects at the evaluated service state."),
    validity_range="Contact retained at minimum preload; positive sourced stiffness/area/allowable; Pi>=Po; no prying/moment/shear",
    source="NASA RP-1228 (1990), printed p13: preload plus Kb/(Kb+Kc) external load; axial force equilibrium for clamp reduction.",
    verification_status="independent spring compatibility, axial force balance, scaling and domain tests",
    limitations=("No flange bending, bolt bending/shear/fatigue, thread pullout, bearing, gasket stress distribution or leakage prediction.",
                 "No generic preload, service strength, effective seal radius or thermal-contraction default; not hardware acceptance."),
)


@dataclass(frozen=True, slots=True)
class BoltGroupScreen:
    separating_force_n: float
    stiffness_load_fraction: float
    minimum_retained_clamp_n: float
    required_seating_force_n: float
    contact_retained: bool
    peak_bolt_load_n: float | None
    bolt_stress_pa: float | None
    stress_over_allowable: float | None
    passed_declared_screen: bool


def _value(q: Quantity, dimension: Dimension, name: str, *, zero=False) -> float:
    if not isinstance(q,Quantity) or isinstance(q.magnitude,bool):
        raise InvalidInputError(name+" requires a non-Boolean Core Quantity")
    value=as_si(q,dimension,name)
    return (validate_non_negative if zero else validate_positive)(value,name)


def axial_bolt_group(*, internal_pressure: Quantity, external_pressure: Quantity,
                     effective_seal_radius: Quantity, additional_axial_force: Quantity,
                     bolt_count: int, tensile_area: Quantity, bolt_allowable: Quantity,
                     bolt_stiffness: Quantity, member_stiffness: Quantity,
                     preload_min: Quantity, preload_max: Quantity,
                     required_seating_force: Quantity) -> BoltGroupScreen:
    pi=_value(internal_pressure,PRESSURE,"internal pressure",zero=True)
    po=_value(external_pressure,PRESSURE,"external pressure",zero=True)
    if pi<po:raise OutOfRangeError("External-pressure buckling/compression is not this tensile joint model")
    radius=_value(effective_seal_radius,LENGTH,"effective seal radius")
    load=_value(additional_axial_force,FORCE,"additional separating axial force",zero=True)
    if type(bolt_count) is not int or not 1<=bolt_count<=10000:raise InvalidInputError("Explicit integer bolt count1..10000 required")
    area=_value(tensile_area,AREA,"bolt tensile area")
    allowable=_value(bolt_allowable,PRESSURE,"service bolt allowable")
    kb=_value(bolt_stiffness,FORCE/LENGTH,"per-bolt stiffness")
    km=_value(member_stiffness,FORCE/LENGTH,"per-bolt equivalent member stiffness")
    low=_value(preload_min,FORCE,"minimum retained service preload")
    high=_value(preload_max,FORCE,"maximum retained service preload")
    seating=_value(required_seating_force,FORCE,"required total seating force",zero=True)
    if high<low:raise InvalidInputError("Maximum service preload must be >= minimum service preload")
    fraction=1/(1+km/kb)
    external=(pi-po)*math.pi*radius*radius+load
    clamp=bolt_count*low-(1-fraction)*external
    if not all(math.isfinite(v) for v in (external,clamp,fraction)) or not 0<fraction<1:
        raise InvalidInputError("Joint loads/stiffness ratio exceed representable finite bounds")
    if clamp<=0:
        # Once contact is lost, the linear load-partition relation is inapplicable.
        return BoltGroupScreen(external,fraction,clamp,seating,False,None,None,None,False)
    peak=high+fraction*external/bolt_count
    stress=peak/area; ratio=stress/allowable
    if not all(math.isfinite(v) for v in (peak,stress,ratio)):raise InvalidInputError("Bolt stress exceeds representable bounds")
    return BoltGroupScreen(external,fraction,clamp,seating,True,peak,stress,ratio,clamp>=seating and ratio<=1)
