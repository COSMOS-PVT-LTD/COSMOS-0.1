"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.records
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Sourced liquid and reference-state property catalog.

Description:
    Values are reference-state properties, not complete equations of state.
    Each record names its source and validity window. Outside that window
    evaluation returns OUT_OF_RANGE (or EXTRAPOLATED if requested).
"""

from __future__ import annotations

from core.constants import STANDARD_ATMOSPHERE
from core.dimension import DENSITY, PRESSURE
from core.unit import SI

from physics.fluids.fluid_properties import PropertyRecord
from physics.si import (
    SPECIFIC_HEAT,
    THERMAL_CONDUCTIVITY,
    UNIT_DYNAMIC_VISCOSITY,
    UNIT_SPECIFIC_HEAT,
    UNIT_SURFACE_TENSION,
    UNIT_THERMAL_CONDUCTIVITY,
    DYNAMIC_VISCOSITY,
    SURFACE_TENSION,
)

_ATM = STANDARD_ATMOSPHERE
_K = 1.0  # kelvin window half-width for NBP liquid points


LOX_NBP_DENSITY = PropertyRecord(
    fluid_id="lox",
    property_name="density",
    value=1141.0,
    unit=SI.get("kg/m3"),
    dimension=DENSITY,
    phase="liquid",
    temperature_min_k=90.188 - _K,
    temperature_max_k=90.188 + _K,
    pressure_min_pa=_ATM * 0.95,
    pressure_max_pa=_ATM * 1.05,
    source="NIST Chemistry WebBook, saturated liquid oxygen at 1 atm NBP.",
    reference_temperature_k=90.188,
    reference_pressure_pa=_ATM,
    notes="Normal boiling point liquid density. Not a dense-gas EOS.",
)

LH2_NBP_DENSITY = PropertyRecord(
    fluid_id="hydrogen",
    property_name="density",
    value=70.85,
    unit=SI.get("kg/m3"),
    dimension=DENSITY,
    phase="liquid",
    temperature_min_k=20.369 - _K,
    temperature_max_k=20.369 + _K,
    pressure_min_pa=_ATM * 0.95,
    pressure_max_pa=_ATM * 1.05,
    source="NIST Chemistry WebBook, saturated liquid hydrogen (parahydrogen) at 1 atm NBP.",
    reference_temperature_k=20.369,
    reference_pressure_pa=_ATM,
)

LCH4_NBP_DENSITY = PropertyRecord(
    fluid_id="methane",
    property_name="density",
    value=422.6,
    unit=SI.get("kg/m3"),
    dimension=DENSITY,
    phase="liquid",
    temperature_min_k=111.67 - _K,
    temperature_max_k=111.67 + _K,
    pressure_min_pa=_ATM * 0.95,
    pressure_max_pa=_ATM * 1.05,
    source="NIST Chemistry WebBook, saturated liquid methane at 1 atm NBP.",
    reference_temperature_k=111.67,
    reference_pressure_pa=_ATM,
)

LN2_NBP_DENSITY = PropertyRecord(
    fluid_id="nitrogen",
    property_name="density",
    value=806.1,
    unit=SI.get("kg/m3"),
    dimension=DENSITY,
    phase="liquid",
    temperature_min_k=77.355 - _K,
    temperature_max_k=77.355 + _K,
    pressure_min_pa=_ATM * 0.95,
    pressure_max_pa=_ATM * 1.05,
    source="NIST Chemistry WebBook, saturated liquid nitrogen at 1 atm NBP.",
    reference_temperature_k=77.355,
    reference_pressure_pa=_ATM,
)

LHE_NBP_DENSITY = PropertyRecord(
    fluid_id="helium",
    property_name="density",
    value=124.9,
    unit=SI.get("kg/m3"),
    dimension=DENSITY,
    phase="liquid",
    temperature_min_k=4.22 - 0.5,
    temperature_max_k=4.22 + 0.5,
    pressure_min_pa=_ATM * 0.95,
    pressure_max_pa=_ATM * 1.05,
    source="NIST Chemistry WebBook, saturated liquid helium-4 at 1 atm NBP.",
    reference_temperature_k=4.22,
    reference_pressure_pa=_ATM,
)

RP1_DENSITY = PropertyRecord(
    fluid_id="rp1",
    property_name="density",
    value=810.0,
    unit=SI.get("kg/m3"),
    dimension=DENSITY,
    phase="liquid",
    temperature_min_k=288.0,
    temperature_max_k=298.0,
    pressure_min_pa=_ATM * 0.9,
    pressure_max_pa=_ATM * 1.1,
    source=(
        "Typical RP-1 density near 15 C from Huzel & Huang, NASA SP-125, "
        "and MIL-DTL-25576 density band. Not a unique specification value."
    ),
    reference_temperature_k=288.7,
    reference_pressure_pa=_ATM,
    notes="RP-1 density varies with blend; treat as typical, not certified.",
)

WATER_300K_DENSITY = PropertyRecord(
    fluid_id="water",
    property_name="density",
    value=997.0,
    unit=SI.get("kg/m3"),
    dimension=DENSITY,
    phase="liquid",
    temperature_min_k=299.0,
    temperature_max_k=301.0,
    pressure_min_pa=_ATM * 0.9,
    pressure_max_pa=_ATM * 1.1,
    source="Incropera et al., Fundamentals of Heat and Mass Transfer, Table A.6, liquid water at 300 K.",
    reference_temperature_k=300.0,
    reference_pressure_pa=_ATM,
)

WATER_300K_VISCOSITY = PropertyRecord(
    fluid_id="water",
    property_name="dynamic_viscosity",
    value=855.0e-6,
    unit=UNIT_DYNAMIC_VISCOSITY,
    dimension=DYNAMIC_VISCOSITY,
    phase="liquid",
    temperature_min_k=299.0,
    temperature_max_k=301.0,
    pressure_min_pa=_ATM * 0.9,
    pressure_max_pa=_ATM * 1.1,
    source="Incropera et al., Table A.6, liquid water at 300 K.",
    reference_temperature_k=300.0,
    reference_pressure_pa=_ATM,
)

WATER_300K_CONDUCTIVITY = PropertyRecord(
    fluid_id="water",
    property_name="thermal_conductivity",
    value=0.613,
    unit=UNIT_THERMAL_CONDUCTIVITY,
    dimension=THERMAL_CONDUCTIVITY,
    phase="liquid",
    temperature_min_k=299.0,
    temperature_max_k=301.0,
    pressure_min_pa=_ATM * 0.9,
    pressure_max_pa=_ATM * 1.1,
    source="Incropera et al., Table A.6, liquid water at 300 K.",
    reference_temperature_k=300.0,
    reference_pressure_pa=_ATM,
)

WATER_300K_CP = PropertyRecord(
    fluid_id="water",
    property_name="cp",
    value=4179.0,
    unit=UNIT_SPECIFIC_HEAT,
    dimension=SPECIFIC_HEAT,
    phase="liquid",
    temperature_min_k=299.0,
    temperature_max_k=301.0,
    pressure_min_pa=_ATM * 0.9,
    pressure_max_pa=_ATM * 1.1,
    source="Incropera et al., Table A.6, liquid water at 300 K.",
    reference_temperature_k=300.0,
    reference_pressure_pa=_ATM,
)

WATER_300K_SURFACE_TENSION = PropertyRecord(
    fluid_id="water",
    property_name="surface_tension",
    value=0.0717,
    unit=UNIT_SURFACE_TENSION,
    dimension=SURFACE_TENSION,
    phase="liquid",
    temperature_min_k=299.0,
    temperature_max_k=301.0,
    pressure_min_pa=_ATM * 0.9,
    pressure_max_pa=_ATM * 1.1,
    source="Incropera et al., Table A.6, liquid water at 300 K (air interface).",
    reference_temperature_k=300.0,
    reference_pressure_pa=_ATM,
)

WATER_NBP_VAPOR_PRESSURE = PropertyRecord(
    fluid_id="water",
    property_name="vapor_pressure",
    value=_ATM,
    unit=SI.get("Pa"),
    dimension=PRESSURE,
    phase="saturation",
    temperature_min_k=373.12,
    temperature_max_k=373.18,
    pressure_min_pa=None,
    pressure_max_pa=None,
    source="Definition of the water normal boiling point at 1 atm (ITS-90 / standard atmosphere).",
    reference_temperature_k=373.15,
    reference_pressure_pa=_ATM,
)

AIR_300K_CONDUCTIVITY = PropertyRecord(
    fluid_id="air",
    property_name="thermal_conductivity",
    value=0.0263,
    unit=UNIT_THERMAL_CONDUCTIVITY,
    dimension=THERMAL_CONDUCTIVITY,
    phase="gas",
    temperature_min_k=299.0,
    temperature_max_k=301.0,
    pressure_min_pa=_ATM * 0.9,
    pressure_max_pa=_ATM * 1.1,
    source="Incropera et al., Table A.4, air at 300 K, 1 atm.",
    reference_temperature_k=300.0,
    reference_pressure_pa=_ATM,
)

AIR_300K_PRANDTL = PropertyRecord(
    fluid_id="air",
    property_name="prandtl",
    value=0.707,
    unit=SI.get("1"),
    dimension=SI.get("1").dimension,
    phase="gas",
    temperature_min_k=299.0,
    temperature_max_k=301.0,
    pressure_min_pa=_ATM * 0.9,
    pressure_max_pa=_ATM * 1.1,
    source="Incropera et al., Table A.4, air at 300 K, 1 atm.",
    reference_temperature_k=300.0,
    reference_pressure_pa=_ATM,
)
