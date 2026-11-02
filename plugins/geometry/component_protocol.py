"""Qualified component slice, deliberately separate from fixtures and nozzle V1."""

from systems.contracts.geometry import Representation
from systems.contracts.geometry._wire import require
from systems.geometry.component_model import VERSION, from_contracts


def validate(request,snapshot,graph):
    plan = from_contracts(snapshot,graph)
    values = {p.name:p.value_si for p in snapshot.parameters_si}
    require(request.snapshot_id == snapshot.snapshot_id and request.feature_graph_sha256 == graph.content_sha256 and request.feature_graph_id == graph.graph_id,
            "STALE_REQUEST", "Component request must bind exact immutable snapshot/graph")
    require(request.backend_id == "occt" and request.backend_version == VERSION and request.representation is Representation.ANALYTIC_BREP
            and request.approximation_profile == "none" and request.voxel_resolution_m is None and request.frame_id == snapshot.frame_id == "world"
            and {f.value for f in request.output_formats} == {"step","stl"}, "UNSUPPORTED_COMPONENT_BUILD", "Pinned analytic component policy with explicit paired STEP/STL and world frame required")
    require(request.source_tolerance_m == values["source_tolerance"] and request.export_tolerance_m == values["export_tolerance"], "COMPONENT_TOLERANCE", "No replacement of retained source/export tolerances")
    return plan
