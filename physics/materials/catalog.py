"""
COSMOS Rocket Propulsion Platform

Module: physics.materials.catalog
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Temperature-windowed material property records.

Description:
    Room-temperature handbook values are not treated as universally valid.
    Each record states its temperature window. Interpolation is not performed.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.dimension import DENSITY, PRESSURE
from core.unit import SI, Unit

from physics.fluids.fluid_properties import PropertyRecord
from physics.si import (
    SPECIFIC_HEAT,
    THERMAL_CONDUCTIVITY,
    THERMAL_EXPANSION,
    UNIT_ALPHA,
    UNIT_SPECIFIC_HEAT,
    UNIT_STRESS,
    UNIT_THERMAL_CONDUCTIVITY,
)

__all__ = ("MaterialRecord", "get_material")


@dataclass(frozen=True, slots=True)
class MaterialRecord:
    """Material identity plus sourced property records."""

    material_id: str
    condition: str
    source: str
    density: PropertyRecord
    youngs_modulus: PropertyRecord
    poisson_ratio: PropertyRecord
    yield_strength: PropertyRecord | None
    ultimate_strength: PropertyRecord | None
    conductivity: PropertyRecord
    specific_heat: PropertyRecord
    thermal_expansion: PropertyRecord


def _mechanical(
    material_id: str,
    name: str,
    value: float,
    unit: Unit,
    dimension,
    t_ref: float,
    source: str,
    *,
    t_span: float = 10.0,
) -> PropertyRecord:
    return PropertyRecord(
        fluid_id=material_id,
        property_name=name,
        value=value,
        unit=unit,
        dimension=dimension,
        phase="solid",
        temperature_min_k=t_ref - t_span,
        temperature_max_k=t_ref + t_span,
        pressure_min_pa=None,
        pressure_max_pa=None,
        source=source,
        reference_temperature_k=t_ref,
        notes="Typical published value; not a certified allowables dataset.",
    )


_INC = "Incropera et al., Fundamentals of Heat and Mass Transfer, Appendix A, 300 K."
_TYP = (
    "Typical published engineering value near 300 K. Not MMPDS certified "
    "allowables. OPEN SCIENTIFIC ISSUE: temperature-dependent allowables."
)

OFHC_COPPER = MaterialRecord(
    material_id="ofhc_copper",
    condition="annealed, near 300 K",
    source=_INC,
    density=_mechanical("ofhc_copper", "density", 8933.0, SI.get("kg/m3"), DENSITY, 300.0, _INC),
    youngs_modulus=_mechanical(
        "ofhc_copper", "E", 117.0e9, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    poisson_ratio=_mechanical(
        "ofhc_copper", "nu", 0.34, SI.get("1"), SI.get("1").dimension, 300.0, _TYP
    ),
    yield_strength=None,
    ultimate_strength=None,
    conductivity=_mechanical(
        "ofhc_copper", "k", 401.0, UNIT_THERMAL_CONDUCTIVITY, THERMAL_CONDUCTIVITY, 300.0, _INC
    ),
    specific_heat=_mechanical(
        "ofhc_copper", "cp", 385.0, UNIT_SPECIFIC_HEAT, SPECIFIC_HEAT, 300.0, _INC
    ),
    thermal_expansion=_mechanical(
        "ofhc_copper", "alpha", 17.0e-6, UNIT_ALPHA, THERMAL_EXPANSION, 300.0, _INC
    ),
)

STAINLESS_304 = MaterialRecord(
    material_id="stainless_304",
    condition="AISI 304, near 300 K",
    source=_INC,
    density=_mechanical("stainless_304", "density", 7900.0, SI.get("kg/m3"), DENSITY, 300.0, _INC),
    youngs_modulus=_mechanical(
        "stainless_304", "E", 193.0e9, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    poisson_ratio=_mechanical(
        "stainless_304", "nu", 0.29, SI.get("1"), SI.get("1").dimension, 300.0, _TYP
    ),
    yield_strength=_mechanical(
        "stainless_304", "Sy", 215.0e6, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    ultimate_strength=_mechanical(
        "stainless_304", "Su", 505.0e6, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    conductivity=_mechanical(
        "stainless_304", "k", 15.2, UNIT_THERMAL_CONDUCTIVITY, THERMAL_CONDUCTIVITY, 300.0, _INC
    ),
    specific_heat=_mechanical(
        "stainless_304", "cp", 477.0, UNIT_SPECIFIC_HEAT, SPECIFIC_HEAT, 300.0, _INC
    ),
    thermal_expansion=_mechanical(
        "stainless_304", "alpha", 15.9e-6, UNIT_ALPHA, THERMAL_EXPANSION, 300.0, _INC
    ),
)

ALUMINUM_6061_T6 = MaterialRecord(
    material_id="aluminum_6061_t6",
    condition="6061-T6, near 300 K",
    source=_TYP,
    density=_mechanical(
        "aluminum_6061_t6", "density", 2700.0, SI.get("kg/m3"), DENSITY, 300.0, _INC
    ),
    youngs_modulus=_mechanical(
        "aluminum_6061_t6", "E", 68.9e9, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    poisson_ratio=_mechanical(
        "aluminum_6061_t6", "nu", 0.33, SI.get("1"), SI.get("1").dimension, 300.0, _TYP
    ),
    yield_strength=_mechanical(
        "aluminum_6061_t6", "Sy", 276.0e6, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    ultimate_strength=_mechanical(
        "aluminum_6061_t6", "Su", 310.0e6, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    conductivity=_mechanical(
        "aluminum_6061_t6", "k", 167.0, UNIT_THERMAL_CONDUCTIVITY, THERMAL_CONDUCTIVITY, 300.0, _INC
    ),
    specific_heat=_mechanical(
        "aluminum_6061_t6", "cp", 896.0, UNIT_SPECIFIC_HEAT, SPECIFIC_HEAT, 300.0, _INC
    ),
    thermal_expansion=_mechanical(
        "aluminum_6061_t6", "alpha", 23.0e-6, UNIT_ALPHA, THERMAL_EXPANSION, 300.0, _INC
    ),
)

INCONEL_718 = MaterialRecord(
    material_id="inconel_718",
    condition="typical aged, near 300 K",
    source=_TYP,
    density=_mechanical("inconel_718", "density", 8220.0, SI.get("kg/m3"), DENSITY, 300.0, _TYP),
    youngs_modulus=_mechanical(
        "inconel_718", "E", 200.0e9, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    poisson_ratio=_mechanical(
        "inconel_718", "nu", 0.29, SI.get("1"), SI.get("1").dimension, 300.0, _TYP
    ),
    yield_strength=_mechanical(
        "inconel_718", "Sy", 1034.0e6, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    ultimate_strength=_mechanical(
        "inconel_718", "Su", 1240.0e6, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    conductivity=_mechanical(
        "inconel_718", "k", 11.4, UNIT_THERMAL_CONDUCTIVITY, THERMAL_CONDUCTIVITY, 300.0, _TYP
    ),
    specific_heat=_mechanical(
        "inconel_718", "cp", 435.0, UNIT_SPECIFIC_HEAT, SPECIFIC_HEAT, 300.0, _TYP
    ),
    thermal_expansion=_mechanical(
        "inconel_718", "alpha", 13.0e-6, UNIT_ALPHA, THERMAL_EXPANSION, 300.0, _TYP
    ),
)

TI6AL4V = MaterialRecord(
    material_id="ti6al4v",
    condition="Ti-6Al-4V typical, near 300 K",
    source=_INC + " / typical elastic values.",
    density=_mechanical("ti6al4v", "density", 4430.0, SI.get("kg/m3"), DENSITY, 300.0, _INC),
    youngs_modulus=_mechanical(
        "ti6al4v", "E", 114.0e9, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    poisson_ratio=_mechanical(
        "ti6al4v", "nu", 0.34, SI.get("1"), SI.get("1").dimension, 300.0, _TYP
    ),
    yield_strength=_mechanical(
        "ti6al4v", "Sy", 880.0e6, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    ultimate_strength=_mechanical(
        "ti6al4v", "Su", 950.0e6, UNIT_STRESS, PRESSURE, 300.0, _TYP
    ),
    conductivity=_mechanical(
        "ti6al4v", "k", 7.0, UNIT_THERMAL_CONDUCTIVITY, THERMAL_CONDUCTIVITY, 300.0, _INC
    ),
    specific_heat=_mechanical(
        "ti6al4v", "cp", 565.0, UNIT_SPECIFIC_HEAT, SPECIFIC_HEAT, 300.0, _INC
    ),
    thermal_expansion=_mechanical(
        "ti6al4v", "alpha", 8.6e-6, UNIT_ALPHA, THERMAL_EXPANSION, 300.0, _INC
    ),
)

MATERIALS: dict[str, MaterialRecord] = {
    OFHC_COPPER.material_id: OFHC_COPPER,
    STAINLESS_304.material_id: STAINLESS_304,
    ALUMINUM_6061_T6.material_id: ALUMINUM_6061_T6,
    INCONEL_718.material_id: INCONEL_718,
    TI6AL4V.material_id: TI6AL4V,
}


def get_material(material_id: str) -> MaterialRecord:
    """Return a catalog material."""

    from physics.exceptions import MaterialPropertyError

    try:
        return MATERIALS[material_id]
    except KeyError as exc:
        raise MaterialPropertyError(f"Unknown material: {material_id!r}.") from exc
