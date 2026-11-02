"""Engine-derived nozzle intent only; no native build/export acceptance."""

from __future__ import annotations

import math
from copy import deepcopy
from hashlib import sha256
from itertools import pairwise
from typing import Any

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from systems.contracts.geometry import (
    CoordinateFrame,
    DesignSnapshot,
    GeometryFeature,
    GeometryFeatureGraph,
    Representation,
    SIParameter,
    SourceReference,
)
from systems.contracts.geometry._wire import digest
from systems.contracts.results import CalculationResult, ResultStatus, ValidationInfo
from systems.cycle.operating_contract import scalar
from systems.cycle.pressure_fed import _keys, _source
from systems.projects.models import PropulsionDesign

SCHEMA = "cosmos.engine-geometry-intent-input.v1"
TEMPLATE = "divergent-nozzle-radial-wall-v1"


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    _keys(spec, {"schema", "template", "wall_thickness", "source_tolerance", "export_tolerance", "wall_source", "frame"}, "engine geometry intent")
    if spec["schema"] != SCHEMA or spec["template"] != TEMPLATE or spec["frame"] != "THROAT_X_AXIS_RIGHT_HANDED_M":
        raise InvalidInputError("Only the declared divergent nozzle radial-wall template in a right-handed throat +X frame is supported.")
    _source(spec["wall_source"], "radial wall thickness design intent")
    values = {key: scalar(spec[key], "m", key) for key in ("wall_thickness", "source_tolerance", "export_tolerance")}
    if max(values["source_tolerance"], values["export_tolerance"]) >= values["wall_thickness"] / 2:
        raise InvalidInputError("Source and export tolerances must each be less than half the radial wall thickness; no automatic tolerance conversion.")
    return values


def prepare(design: PropulsionDesign, specification: dict[str, Any]) -> CalculationResult:
    cfg = validate(specification)
    original = design.to_canonical_json()
    contour = design.workflow.current_result("nozzle")
    if contour is None or design.workflow.graph.get("nozzle").status is not ResultStatus.CURRENT:
        raise InvalidInputError("Save and calculate an actual CURRENT nozzle contour before capturing geometry intent.")
    stations = contour.outputs.get("stations")
    if not isinstance(stations, list) or not 2 <= len(stations) <= 257:
        raise InvalidInputError("A retained 2–257-station divergent nozzle contour is required, not 1D area-only geometry.")
    points = [(row["x_m"], row["radius_m"]) for row in stations]
    if any(type(v) not in {int, float} or not math.isfinite(v) for row in points for v in row):
        raise InvalidInputError("Contour coordinates must be finite SI numbers.")
    if points[0][0] != 0 or any(r <= 0 for _, r in points) or any(b[0] <= a[0] or b[1] <= a[1] for a, b in pairwise(points)):
        raise InvalidInputError("Require throat x=0 and strictly increasing positive radius and x; no frame/contour repair or smoothing.")
    base_hash = sha256(original.encode()).hexdigest()
    spec_hash = digest(specification)
    refs = (
        SourceReference("baseline", f"propulsion/{design.design_id}/{base_hash}.json", base_hash),
        SourceReference("intent", f"geometry-intent/{spec_hash}.json", spec_hash),
    )
    parameters = []

    def parameter(name: str, value: float, source: str) -> str:
        parameters.append(SIParameter.from_quantity(name, Quantity(value, SI.get("m")), si_unit="m", source_ref_id=source))
        return name

    point_refs = tuple(parameter(f"station-{i}-{key}", value, "baseline") for i, row in enumerate(points) for key, value in zip(("x", "radius"), row, strict=True))
    wall = parameter("radial-wall-thickness", cfg["wall_thickness"], "intent")
    for key in ("source_tolerance", "export_tolerance"):
        parameter(key.replace("_", "-"), cfg[key], "intent")
    frame = CoordinateFrame("throat-x", None, (0., 0., 0.), (1., 0., 0., 0., 1., 0., 0., 0., 1.))
    snapshot = DesignSnapshot(
        "engine-design-" + design.design_id, "intent-" + spec_hash,
        tuple(parameters), (frame,), frame.frame_id, refs, design.updated_at,
    )
    features = (
        GeometryFeature("inner-profile", "polyline_profile_intent", point_refs, (), frame.frame_id, Representation.ANALYTIC_BREP),
        GeometryFeature("wall-profile", "radial_offset_closed_profile_intent", (wall,), ("inner-profile",), frame.frame_id, Representation.ANALYTIC_BREP),
        GeometryFeature("nozzle-wall", "revolve_x_intent", (), ("wall-profile",), frame.frame_id, Representation.ANALYTIC_BREP),
    )
    graph = GeometryFeatureGraph("engine-nozzle-" + spec_hash, snapshot.snapshot_id, features, ("nozzle-wall",))
    graph.validate_snapshot(snapshot)
    profile = [{"x_m": x, "inner_radius_m": r, "outer_radius_m": r + cfg["wall_thickness"]} for x, r in points]
    if any(not math.isfinite(row["outer_radius_m"]) or row["outer_radius_m"] <= row["inner_radius_m"] for row in profile):
        raise InvalidInputError("Radial wall offset is nonfinite or below source numerical precision.")
    return CalculationResult(
        calculation_type="geometry.engine_nozzle_intent", status=ResultStatus.CURRENT,
        model_id=TEMPLATE, model_version="1",
        inputs={"baseline_canonical_text": original, "specification": deepcopy(specification), "contour_result_id": contour.result_id, "contour_model_id": contour.model_id},
        outputs={"workflow_cycle_complete": False, "intent_status": "CAPTURED_NOT_BUILT", "snapshot_json": snapshot.to_json(), "snapshot_id": snapshot.snapshot_id, "graph_json": graph.to_json(), "graph_sha256": graph.content_sha256, "profile": profile, "feature_order": list(graph.topological_order()), "feature_fingerprints": dict(graph.fingerprints(snapshot)), "source_tolerance_m": cfg["source_tolerance"], "export_tolerance_m": cfg["export_tolerance"], "representation_intent": "analytic_brep", "profile_approximation": "piecewise-linear through exact saved contour stations; not the original continuous bell curve", "wall_convention": "constant radial offset, not normal thickness or a structural sizing result", "backend": None, "artifacts": [], "engineering_export_eligible": False, "production_handoff": False, "physical_validation": "NOT_PERFORMED", "residuals": []},
        assumptions=("Divergent nozzle only; positive +X from throat, metres, right-handed identity frame. No chamber/injector/channel dimensions invented.", "Project/commit authority is the outer managed envelope; snapshot namespace identifies the source engine design, not a new Project record."),
        warnings=("Feature operations describe intent, not qualified backend capability. Native fixture allowlist is unchanged.", "A sampled profile intent is not a built solid, accepted CAD export or manufacturing/physical acceptance."),
        validation=ValidationInfo(status="NOT_PERFORMED"),
    )
