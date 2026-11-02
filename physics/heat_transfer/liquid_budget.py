"""Steady enthalpy threshold for bulk saturation onset; no cooling design."""

import math
from dataclasses import dataclass

from core.dimension import MASS_FLOW_RATE, TIME
from core.quantity import Quantity
from core.validation import validate_positive
from physics.exceptions import OutOfRangeError
from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.si import SPECIFIC_ENERGY

LIQUID_HEATING_THRESHOLD = ModelIdentity(
    model_id="PHYS-COOL.bulk_saturation_enthalpy_threshold",
    model_name="Steady bulk-saturation heating threshold",
    physical_domain="heat_transfer",
    equations=("Q_threshold = mdot (h_sat_liquid(P_selected) - h_in)", "E_duration = Q_threshold duration"),
    inputs=("mass flow [kg/s]", "common-reference inlet/saturated-liquid enthalpies [J/kg]", "duration [s]"),
    outputs=("bulk-saturation threshold [W]", "duration heat [J]"),
    assumptions=("Steady one-inlet/one-outlet first-law balance; negligible kinetic/elevation changes.",
                 "Caller establishes same fluid, common enthalpy reference and chosen pressure applicability."),
    validity_range="Positive flow/duration and strictly positive subcooled enthalpy margin; sourced subcritical saturation states",
    required_properties=("inlet specific enthalpy", "saturated-liquid enthalpy at explicitly selected pressure"),
    source="Steady-flow first law; property values and phase boundaries must be supplied from an explicit same-fluid reference.",
    verification_status="independent energy balance, reference-shift invariance, scale/dimension/domain tests",
    limitations=("A necessary bulk-energy bound, not a sufficient single-phase guarantee, safe heat load or cooling design.",
                 "No wall boiling onset, pressure path, local heat flux, transient storage or physical validation."),
)


@dataclass(frozen=True, slots=True)
class LiquidHeatingThreshold:
    specific_enthalpy_margin_j_kg: float
    saturation_onset_heat_w: float
    duration_heat_j: float


def liquid_heating_threshold(*, mass_flow: Quantity, inlet_enthalpy: Quantity,
                             saturated_liquid_enthalpy: Quantity, duration: Quantity) -> LiquidHeatingThreshold:
    """Q at h_out = h_sat_liquid for a chosen pressure, same enthalpy reference.

    Valid only as a steady bulk-energy bound, neglecting kinetic/elevation terms.
    This does not establish wall boiling onset, heat flux, pressure path, thermal
    feasibility, transient wall storage or a safe operating limit. Staying below
    this threshold is necessary, not sufficient, for all-liquid bulk flow.
    The caller must supply same-fluid, common-reference source states explicitly.
    """
    mdot = validate_positive(as_si(mass_flow, MASS_FLOW_RATE, "mass flow"), "mass flow")
    time = validate_positive(as_si(duration, TIME, "duration"), "duration")
    incoming = as_si(inlet_enthalpy, SPECIFIC_ENERGY, "inlet enthalpy")
    saturation = as_si(saturated_liquid_enthalpy, SPECIFIC_ENERGY, "saturated liquid enthalpy")
    margin = saturation - incoming
    validate_positive(margin, "positive subcooled enthalpy margin")
    heat = mdot * margin
    if not all(math.isfinite(v) for v in (incoming, saturation, heat, heat * time)):
        raise OutOfRangeError("Liquid heating threshold requires finite common-reference states.")
    return LiquidHeatingThreshold(margin, heat, heat * time)
