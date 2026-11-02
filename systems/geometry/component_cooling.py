"""Read-only exact source geometry for existing sector cooling passages.

No native builder changes, rectangular-channel substitution or thermal sizing.
"""

from __future__ import annotations

import math
from dataclasses import asdict
from hashlib import sha256
from itertools import pairwise
from pathlib import Path

from core.quantity import Quantity
from core.unit import SI
from physics.fluids.sector_passage import SECTOR_PASSAGE, annular_sector_section
from systems.geometry.component_model import ComponentPlan
from systems.projects.authority import StoreUnavailable

SCHEMA = "cosmos.component-sector-cooling-handoff.v1"
LIMITS = (
    "Axial-plane sections are not flow-normal sections on sloping passages.",
    "4A/P is geometry only; no heat-transfer/friction correlation is qualified here.",
    "Sector CAD is not the existing constant-width rectangular thermal model; no automatic conversion.",
    "No coolant routing/manifold, flow split, wall conduction, phase-change, thermal or structural solution.",
    "Geometric coverage is not gas-side thermal coverage or hardware approval.",
)


def method_sources() -> dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    names = ("physics/fluids/sector_passage.py", "systems/geometry/component_cooling.py", "api/component_cooling.py")
    return {name: sha256((root / name).read_bytes()).hexdigest() for name in names}


_LOADED_METHOD_SOURCES = method_sources()


def geometry_handoff(plan: ComponentPlan) -> dict:
    """Measure exported cooled metal parts, including unexported void domains."""
    if method_sources() != _LOADED_METHOD_SOURCES:
        raise StoreUnavailable("Cooling geometry analysis methods changed after loading; restart before claiming new source hashes")
    passages = []
    for part in plan.parts:
        if part.cooling is None:
            continue
        c = part.cooling
        rows = []
        for x, radius, outer in part.profile:
            inner, outer_channel = radius + c.hot_ligament, radius + c.hot_ligament + c.depth
            section = annular_sector_section(Quantity(inner, SI.get("m")), Quantity(outer_channel, SI.get("m")), Quantity(c.width_rad, SI.get("rad")))
            rows.append({"x_m": x, "gas_bore_radius_m": radius,
                         "channel_inner_radius_m": inner, "channel_outer_radius_m": outer_channel,
                         "radial_roof_thickness_m": outer - outer_channel, **asdict(section)})
        segments = []
        for a, b in pairwise(rows):
            dx = b["x_m"] - a["x_m"]
            ri0, ro0 = a["channel_inner_radius_m"], a["channel_outer_radius_m"]
            ri1, ro1 = b["channel_inner_radius_m"], b["channel_outer_radius_m"]
            mid_area = c.width_rad * ((ro0 + ro1) - (ri0 + ri1)) * ((ro0 + ro1) + (ri0 + ri1)) / 8
            volume = dx * (a["area_m2"] + 4 * mid_area + b["area_m2"]) / 6
            inner_area = c.width_rad * (ri0 + ri1) / 2 * math.hypot(dx, ri1 - ri0)
            outer_area = c.width_rad * (ro0 + ro1) / 2 * math.hypot(dx, ro1 - ro0)
            side_area = dx * ((ro0 - ri0) + (ro1 - ri1)) / 2
            slope = b["gas_bore_radius_m"] - a["gas_bore_radius_m"]
            segments.append({"x_start_m": a["x_m"], "x_end_m": b["x_m"],
                             "shape": "CONVERGING" if slope < 0 else "DIVERGING" if slope > 0 else "CONSTANT_RADIUS",
                             "volume_per_channel_m3": volume,
                             "inner_lateral_area_per_channel_m2": inner_area,
                             "outer_lateral_area_per_channel_m2": outer_area,
                             "radial_side_area_per_channel_m2": 2 * side_area,
                             "axial_length_m": dx})
        passages.append({"part_id": part.part_id, "feature_id": part.feature_id, "frame_id": part.frame_id,
                         "channel_count": c.count, "angular_width_rad": c.width_rad,
                         "phase_rad": c.phase_rad, "radial_hot_ligament_m": c.hot_ligament,
                         "radial_depth_m": c.depth, "fluid_domains_exported": c.fluid_domains,
                         "section_plane": "LOCAL_AXIAL_NOT_FLOW_NORMAL",
                         "volume_per_channel_m3": math.fsum(s["volume_per_channel_m3"] for s in segments),
                         "total_channel_volume_m3": c.count * math.fsum(s["volume_per_channel_m3"] for s in segments),
                         "minimum_axial_hydraulic_diameter_m": min(r["hydraulic_diameter_m"] for r in rows),
                         "maximum_axial_hydraulic_diameter_m": max(r["hydraulic_diameter_m"] for r in rows),
                         "stations": rows, "segments": segments})
    return {"schema": SCHEMA, "physics_model": SECTOR_PASSAGE.to_canonical_dict(), "passages": passages, "has_sector_passages": bool(passages),
            "thermal_mapping": "UNSUPPORTED_SECTOR_TO_RECTANGULAR" if passages else "NO_SECTOR_PASSAGES",
            "thermally_sized": False, "physical_validation": "NOT_PERFORMED",
            "engineering_acceptance": "NOT_PERFORMED", "limitations": list(LIMITS), "method_sources": dict(_LOADED_METHOD_SOURCES)}
