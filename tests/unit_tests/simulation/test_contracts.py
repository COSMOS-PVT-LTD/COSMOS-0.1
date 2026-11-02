"""Synthetic immutable DTO tests, not real geometry handoff acceptance."""
from dataclasses import FrozenInstanceError, replace

import pytest

from simulation.contracts import FixtureHandoff, StudySettings, StudySnapshot
from simulation.workbench import mesh
from systems.contracts.geometry import MappingStatus, NamedSelection, Representation
from systems.contracts.geometry._wire import GeometryContractError
from tests.fixtures.geometry_contracts import artifact


def fixture():
    value = replace(artifact(), backend_id="occt")
    selection = NamedSelection("outer-surface", value.geometry_revision_id, "body", ("radial-outer-shell",), 1., MappingStatus.EXACT)
    return FixtureHandoff(value, selection, "a" * 64, .01, "world", value.snapshot_id)


def test_nested_study_immutable_lossless_and_reproducible():
    study = StudySnapshot(fixture(), StudySettings())
    assert StudySnapshot.from_json(study.to_json()) == study
    assert StudySnapshot(fixture(), StudySettings()).content_sha256 == study.content_sha256
    with pytest.raises(FrozenInstanceError):
        study.settings.cells = 32
    changed = replace(study, settings=replace(study.settings, cells=32))
    assert changed.content_sha256 != study.content_sha256 and mesh(changed)["mesh_sha256"] != mesh(study)["mesh_sha256"]
    assert mesh(study)["geometry_sha256"] == study.handoff.artifact.sha256
    assert mesh(study)["production_handoff"] is False


@pytest.mark.parametrize("changes", [{"cells": True}, {"cells": 1000}, {"max_iterations": 0}, {"max_iterations": 50001},
    {"relative_residual": 0}, {"relative_residual": float("nan")}, {"surface_k": 0}, {"surface_k": float("inf")},
    {"generation_w_m3": -1}, {"conductivity_w_m_k": "10"}])
def test_invalid_si_and_counts(changes):
    with pytest.raises(GeometryContractError):
        replace(StudySettings(), **changes)


@pytest.mark.parametrize("changes", [{"radius_m": .02}, {"frame_id": "foreign"}, {"scope": "engineering"}, {"geometry_snapshot_id": "b" * 64}])
def test_unqualified_handoff_refused(changes):
    with pytest.raises(GeometryContractError):
        replace(fixture(), **changes)


def test_unresolved_or_stale_named_selection_refused():
    h = fixture()
    with pytest.raises(GeometryContractError):
        replace(h, selection=h.selection.for_revision("other-geometry"))
    with pytest.raises(GeometryContractError):
        replace(h, artifact=replace(h.artifact, representation=Representation.FACETED_BREP, approximation_profile="planar_facets"))


def test_unknown_models_and_tampered_wire_hash_refused():
    study = StudySnapshot(fixture(), StudySettings())
    with pytest.raises(GeometryContractError):
        replace(study, model="engine-CFD")
    with pytest.raises(GeometryContractError):
        StudySnapshot.from_json(study.to_json().replace('"cells":16', '"cells":32'))
