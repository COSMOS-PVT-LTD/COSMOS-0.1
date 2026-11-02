"""Synthetic P06 contract fixtures. No geometry execution/acceptance evidence."""
from dataclasses import replace

from core.quantity import Quantity
from core.unit import SI
from systems.contracts.geometry import (
    BuildState,
    CoordinateFrame,
    DesignSnapshot,
    Disposition,
    GeometryArtifact,
    GeometryBuildEvent,
    GeometryBuildRecord,
    GeometryBuildRequest,
    GeometryCheck,
    GeometryFeature,
    GeometryFeatureGraph,
    GeometryValidationReport,
    MappingStatus,
    NamedSelection,
    OutputFormat,
    Representation,
    SIParameter,
    SourceReference,
)

STAMP = "2026-10-09T00:00:00+00:00"
HASH = "a" * 64
IDENTITY = (1.0, 0, 0, 0, 1.0, 0, 0, 0, 1.0)


def snapshot(*, radius=10.0, revision="r1"):
    source = SourceReference("fixture-only", "tests/fixtures/geometry_contracts.py", HASH)
    parameters = tuple(SIParameter.from_quantity(name, Quantity(value, SI.get("mm")), si_unit="m", source_ref_id=source.ref_id)
                       for name, value in [("radius", radius), ("length", 100.0), ("unrelated", 5.0)])
    return DesignSnapshot("fixture-project", revision, parameters,
                          (CoordinateFrame("world", None, (0, 0, 0), IDENTITY),), "world", (source,), STAMP)


def graph(value=None):
    value = snapshot() if value is None else value
    return GeometryFeatureGraph("fixture-graph", value.snapshot_id, (
        GeometryFeature("chamber", "primitive.cylinder", ("radius", "length"), (), "world", Representation.ANALYTIC_BREP),
        GeometryFeature("interface", "intent.interface", (), ("chamber",), "world", Representation.ANALYTIC_BREP),
        GeometryFeature("independent", "primitive.cylinder", ("length",), (), "world", Representation.ANALYTIC_BREP),
    ), ("interface",))


def request(value=None, features=None):
    value = snapshot() if value is None else value
    features = graph(value) if features is None else features
    return GeometryBuildRequest("fixture-request", value.snapshot_id, features.graph_id, features.content_sha256,
                                "mock-contract-backend", "not-executed-v1", Representation.ANALYTIC_BREP, "none",
                                1e-5, 2e-5, None, (OutputFormat.STEP,), "world", "fixture-correlation")


def artifact(value=None, features=None, build_request=None):
    value = snapshot() if value is None else value
    features = graph(value) if features is None else features
    build_request = request(value, features) if build_request is None else build_request
    return GeometryArtifact("fixture-artifact", "fixture-job", "geometry-r1", value.snapshot_id, features.content_sha256,
                            build_request.representation, build_request.approximation_profile, build_request.backend_id,
                            build_request.backend_version, "m", "world", build_request.source_tolerance_m,
                            build_request.export_tolerance_m, build_request.voxel_resolution_m, HASH, "b" * 64,
                            OutputFormat.STEP, "synthetic-not-created/fixture.step", 123, "fixture-report", STAMP)


def report(geometry=None):
    geometry = artifact() if geometry is None else geometry
    checks = tuple(GeometryCheck(name, True, None, None, "1", ("mock-only-not-qa-evidence",))
                   for name in ["topology", "dimensions", "export_round_trip"])
    return GeometryValidationReport("fixture-report", geometry.artifact_id, checks, "mock-only-policy",
                                    "mock-reviewer-not-human-acceptance", Disposition.ACCEPTED)


def events(states=(BuildState.DRAFT, BuildState.VALIDATING, BuildState.QUEUED, BuildState.RUNNING,
                   BuildState.QA, BuildState.ACCEPTED, BuildState.PUBLISHED)):
    return tuple(GeometryBuildEvent("fixture-job", i, STAMP, state, "fixture-stage", None,
                                   "MOCK_TERMINATION" if state in {BuildState.FAILED, BuildState.REJECTED, BuildState.CANCELLED} else None,
                                   "Synthetic contract event; not real worker evidence", ("fixture-report",) if state is BuildState.PUBLISHED else (),
                                   ("fixture-artifact",) if state is BuildState.PUBLISHED else (), "fixture-correlation")
                 for i, state in enumerate(states))


def record(states=None):
    value = snapshot()
    features = graph(value)
    build_request = request(value, features)
    geometry = artifact(value, features, build_request)
    log = events() if states is None else events(states)
    published = log[-1].state is BuildState.PUBLISHED
    selection = NamedSelection("inlet", geometry.geometry_revision_id, "chamber", ("face:1",), 1, MappingStatus.EXACT)
    return GeometryBuildRecord("fixture-job", build_request, value, features, log,
                               (geometry,) if published else (), (selection,) if published else (), (report(geometry),) if published else ())


def all_contracts():
    value = record()
    return (value.snapshot.source_refs[0], value.snapshot.parameters_si[0], value.snapshot.frames[0], value.snapshot,
            value.feature_graph.features[0], value.feature_graph, value.request, value.artifacts[0],
            value.named_selections[0], value.reports[0].checks[0], value.reports[0], value.events[0], value)


def next_revision(value=None):
    value = snapshot() if value is None else value
    return replace(value, revision_id="r2")
