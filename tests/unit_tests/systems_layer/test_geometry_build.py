from dataclasses import FrozenInstanceError, replace

import pytest

from systems.contracts.geometry import (
    BuildState,
    GeometryBuildRecord,
    GeometryContractError,
    GeometryFeatureGraph,
)
from tests.fixtures.geometry_contracts import (
    artifact,
    events,
    graph,
    next_revision,
    record,
)


def test_synthetic_complete_record_roundtrip_and_no_actual_publication():
    value = record()
    assert value.state is BuildState.PUBLISHED
    assert value == GeometryBuildRecord.from_json(value.to_json())
    assert value.published_artifacts == value.artifacts
    assert value.export_eligibility(value.snapshot, value.feature_graph) == (True, ())
    # Fixture path intentionally never exists. A contract fixture is not G5 QA.
    from pathlib import Path
    assert not Path(value.artifacts[0].storage_uri).exists()
    with pytest.raises(FrozenInstanceError):
        value.events = ()


@pytest.mark.parametrize("states", [
    (BuildState.DRAFT, BuildState.VALIDATING, BuildState.REJECTED),
    (BuildState.DRAFT, BuildState.VALIDATING, BuildState.QUEUED, BuildState.CANCELLED),
    (BuildState.DRAFT, BuildState.VALIDATING, BuildState.QUEUED, BuildState.RUNNING, BuildState.FAILED),
    (BuildState.DRAFT, BuildState.VALIDATING, BuildState.QUEUED, BuildState.RUNNING, BuildState.CANCEL_REQUESTED, BuildState.CANCELLED),
    (BuildState.DRAFT, BuildState.VALIDATING, BuildState.QUEUED, BuildState.RUNNING, BuildState.CANCEL_REQUESTED, BuildState.FAILED),
])
def test_rejection_crash_timeout_and_cancellation_have_no_published_artifact(states):
    value = record(states)
    assert value.published_artifacts == ()
    assert not value.export_eligibility(value.snapshot, value.feature_graph)[0]
    assert value == GeometryBuildRecord.from_json(value.to_json())
    with pytest.raises(GeometryContractError):
        replace(value, artifacts=(artifact(),))


def test_actual_crash_and_timeout_codes_are_preserved_not_claimed_as_process_execution():
    value = record((BuildState.DRAFT, BuildState.VALIDATING, BuildState.QUEUED, BuildState.RUNNING, BuildState.FAILED))
    for code in ("WORKER_CRASH", "TIMEOUT"):
        updated = replace(value, events=(*value.events[:-1], replace(value.events[-1], code=code)))
        assert GeometryBuildRecord.from_json(updated.to_json()).events[-1].code == code


@pytest.mark.parametrize("mutation", ["sequence_duplicate", "sequence_gap", "foreign_job", "foreign_correlation", "backward_time", "skip_qa", "terminal_restart", "empty"])
def test_invalid_transcript_rejected(mutation):
    value = record()
    log = list(value.events)
    if mutation == "sequence_duplicate":
        log[3] = replace(log[3], seq=2)
    elif mutation == "sequence_gap":
        log[3] = replace(log[3], seq=4)
    elif mutation == "foreign_job":
        log[3] = replace(log[3], job_id="foreign")
    elif mutation == "foreign_correlation":
        log[3] = replace(log[3], correlation_id="foreign")
    elif mutation == "backward_time":
        log[3] = replace(log[3], timestamp="2026-10-08T00:00:00Z")
    elif mutation == "skip_qa":
        log[4] = replace(log[4], state=BuildState.ACCEPTED)
    elif mutation == "terminal_restart":
        log.append(replace(log[0], seq=len(log)))
    else:
        log = []
    with pytest.raises(GeometryContractError):
        replace(value, events=log)


@pytest.mark.parametrize("changes", [{"progress_fraction": -1}, {"progress_fraction": 1.01}, {"progress_fraction": True}, {"seq": True}, {"seq": -1}, {"message": ""}, {"state": "faked-success"}, {"artifact_ids": ("early-artifact",)}])
def test_invalid_worker_event_shape_rejected(changes):
    with pytest.raises(GeometryContractError):
        replace(events()[3], **changes)


def test_progress_unknown_is_none_and_same_stage_cannot_move_backward():
    value = record((BuildState.DRAFT, BuildState.VALIDATING, BuildState.QUEUED, BuildState.RUNNING))
    assert value.events[-1].progress_fraction is None
    first = replace(value.events[-1], progress_fraction=.8)
    second = replace(first, seq=4, progress_fraction=.5)
    with pytest.raises(GeometryContractError):
        replace(value, events=(*value.events[:-1], first, second))


def test_publication_requires_independent_qa_and_all_requested_outputs():
    value = record()
    for changes in [{"reports": ()}, {"artifacts": ()}, {"reports": (replace(value.reports[0], report_id="other"),)},
                    {"reports": (replace(value.reports[0], checks=value.reports[0].checks[:1]),)},
                    {"events": (*value.events[:-1], replace(value.events[-1], evidence_refs=()))}]:
        with pytest.raises(GeometryContractError):
            replace(value, **changes)


@pytest.mark.parametrize("changes", [{"backend_version": "changed"}, {"snapshot_id": "c" * 64}, {"source_tolerance_m": .01}, {"export_tolerance_m": .01}, {"frame_id": "foreign"}, {"job_id": "foreign"}])
def test_worker_cannot_silently_change_artifact_request_or_lineage(changes):
    value = record()
    with pytest.raises(GeometryContractError):
        replace(value, artifacts=(replace(value.artifacts[0], **changes),))


def test_old_snapshot_is_not_current_even_if_no_feature_numeric_changed():
    value = record()
    active = next_revision(value.snapshot)
    active_graph = replace(value.feature_graph, snapshot_id=active.snapshot_id)
    assert isinstance(active_graph, GeometryFeatureGraph)
    assert value.feature_graph.impact(value.snapshot, active).stale_features == ()
    assert value.export_eligibility(active, active_graph) == (False, ("STALE_DEPENDENCY",))


def test_request_cannot_bind_different_graph_or_representation():
    value = record()
    with pytest.raises(GeometryContractError):
        replace(value, request=replace(value.request, feature_graph_sha256="c" * 64))
    with pytest.raises(GeometryContractError):
        replace(value, feature_graph=replace(graph(), graph_id="different"))


def test_accepted_state_requires_real_recorded_qa_not_only_transition_name():
    value = record()
    accepted = replace(value, events=value.events[:-1])
    assert accepted.state is BuildState.ACCEPTED and accepted.published_artifacts == ()
    for changes in [{"reports": ()}, {"artifacts": ()}]:
        with pytest.raises(GeometryContractError):
            replace(accepted, **changes)
