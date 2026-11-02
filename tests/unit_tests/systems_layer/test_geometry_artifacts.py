from dataclasses import replace

import pytest

from systems.contracts.geometry import (
    Disposition,
    GeometryContractError,
    MappingStatus,
    NamedSelection,
    OutputFormat,
    Representation,
)
from tests.fixtures.geometry_contracts import (
    artifact,
    graph,
    record,
    report,
    request,
    snapshot,
)


def test_source_export_tolerances_hashes_and_manifest_checksum_are_distinct():
    value = artifact()
    assert value.source_tolerance_m != value.export_tolerance_m
    assert value.source_artifact_sha256 != value.sha256
    assert value.sha256 != value.content_sha256
    assert value == type(value).from_json(value.to_json())


@pytest.mark.parametrize("source,profile,voxel,output,exported", [
    (Representation.ANALYTIC_BREP, "none", None, OutputFormat.STEP, Representation.ANALYTIC_BREP),
    (Representation.ANALYTIC_BREP, "none", None, OutputFormat.STL, Representation.TESSELLATED_SURFACE),
    (Representation.ANALYTIC_BREP, "none", None, OutputFormat.GLB, Representation.TESSELLATED_SURFACE),
    (Representation.IMPLICIT_FIELD, "sparse_volume", .001, OutputFormat.VDB, Representation.IMPLICIT_FIELD),
    (Representation.IMPLICIT_FIELD, "sparse_volume", .001, OutputFormat.STL, Representation.TESSELLATED_SURFACE),
    (Representation.FACETED_BREP, "planar_facets", None, OutputFormat.STEP, Representation.FACETED_BREP),
    (Representation.TESSELLATED_SURFACE, "surface_mesh", None, OutputFormat.STL, Representation.TESSELLATED_SURFACE),
])
def test_mesh_export_never_inherits_analytic_source_label(source, profile, voxel, output, exported):
    value = replace(artifact(), representation=source, approximation_profile=profile, voxel_resolution_m=voxel,
                    output_format=output, storage_uri="synthetic-not-created/fixture." + output.value)
    assert value.representation is source
    assert value.export_representation is exported
    assert type(value).from_json(value.to_json()).export_representation is exported


@pytest.mark.parametrize("representation,profile,voxel,formats", [
    (Representation.ANALYTIC_BREP, "none", None, (OutputFormat.STEP,)),
    (Representation.IMPLICIT_FIELD, "sparse_volume", .001, (OutputFormat.VDB, OutputFormat.STL)),
    (Representation.TESSELLATED_SURFACE, "surface_mesh", None, (OutputFormat.STL,)),
    (Representation.FACETED_BREP, "planar_facets", None, (OutputFormat.STEP,)),
])
def test_representations_remain_explicit_and_never_claim_conversion(representation, profile, voxel, formats):
    value = replace(request(), representation=representation, approximation_profile=profile, voxel_resolution_m=voxel, output_formats=formats)
    assert value == type(value).from_json(value.to_json())


@pytest.mark.parametrize("changes", [
    {"representation": Representation.IMPLICIT_FIELD, "approximation_profile": "sparse_volume", "voxel_resolution_m": .001},
    {"approximation_profile": "implicit-is-parametric-cad"}, {"voxel_resolution_m": .001},
    {"output_formats": (OutputFormat.VDB,)}, {"output_formats": ()}, {"output_formats": (OutputFormat.STEP, OutputFormat.STEP)},
    {"source_tolerance_m": 0}, {"export_tolerance_m": -1}, {"export_tolerance_m": float("nan")},
])
def test_invalid_representation_tolerances_formats_rejected(changes):
    with pytest.raises(GeometryContractError):
        replace(request(), **changes)


@pytest.mark.parametrize("path", ["../x.step", "/tmp/x.step", "a/../x.step", "a/%2e%2e/x.step", "C:\\x.step", "https://example/x.step", "a//x.step", "a/./x.step", "x.stl"])
def test_untrusted_artifact_paths_fail_closed(path):
    with pytest.raises(GeometryContractError):
        replace(artifact(), storage_uri=path)


def test_artifact_freshness_is_derived_not_a_mutable_boolean():
    value = artifact()
    assert value.freshness(snapshot().snapshot_id, graph().content_sha256) == "CURRENT"
    assert value.freshness(snapshot(revision="r2").snapshot_id, graph().content_sha256) == "STALE"
    with pytest.raises(TypeError):
        replace(value, stale=False)


def test_named_selection_revision_change_is_unresolved_not_automatic_remapping():
    value = record().named_selections[0]
    updated = value.for_revision("geometry-r2")
    assert updated.mapping_status is MappingStatus.UNRESOLVED and updated.entity_refs == () and updated.remap_confidence is None
    assert value.entity_refs == ("face:1",)
    with pytest.raises(GeometryContractError):
        updated.validate_binding(graph(), artifact())


@pytest.mark.parametrize("status,entities,confidence", [
    (MappingStatus.EXACT, (), 1), (MappingStatus.EXACT, ("face:1",), .5),
    (MappingStatus.UNRESOLVED, ("face:1",), None), (MappingStatus.UNRESOLVED, (), 1),
    (MappingStatus.REMAPPED, ("face:1",), 0), (MappingStatus.REMAPPED, (), .5),
    (MappingStatus.AMBIGUOUS, ("face:1",), .5), (MappingStatus.EXACT, ("face:1",), float("nan")),
])
def test_invalid_selection_mapping_rejected(status, entities, confidence):
    with pytest.raises(GeometryContractError):
        NamedSelection("inlet", "geometry-r1", "chamber", entities, confidence, status)


def test_unknown_feature_selection_rejected():
    value = replace(record().named_selections[0], feature_ref="absent")
    with pytest.raises(GeometryContractError):
        value.validate_binding(graph(), artifact())


def test_accepted_qa_requires_review_evidence_and_consistent_metric():
    value = report()
    for changes in [{"reviewer_id": None}, {"checks": ()}, {"checks": (replace(value.checks[0], passed=False),)}]:
        with pytest.raises(GeometryContractError):
            replace(value, **changes)
    with pytest.raises(GeometryContractError):
        replace(value.checks[0], observed=10, limit=.1, passed=True)
    with pytest.raises(GeometryContractError):
        replace(value.checks[0], evidence_refs=())
    rejected = replace(value, disposition=Disposition.REJECTED, checks=(replace(value.checks[0], passed=False),))
    assert rejected.disposition is Disposition.REJECTED
