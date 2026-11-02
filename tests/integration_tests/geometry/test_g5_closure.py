"""Real mismatched analytic geometry must still fail after the reader-scale fix."""
import json
from dataclasses import replace

import pytest

from infrastructure.geometry import WorkerSupervisor
from plugins.geometry.adapters import OCCTAdapter
from systems.contracts.geometry import BuildState, OutputFormat
from systems.geometry.qa import FixtureReference
from systems.geometry.service import GeometryBuildService
from tests.fixtures.ngg_cases import case

from .conftest import command


@pytest.mark.parametrize("formats", [(OutputFormat.STEP,), (OutputFormat.STEP, OutputFormat.STL)])
def test_genuine_wrong_radius_is_rejected_not_hidden_by_sampling_or_encoding(native_config, tmp_path, formats):
    snapshot, graph, request = case("sphere", backend="occt", formats=formats)
    snapshot = replace(snapshot, parameters_si=tuple(replace(p, value_si=.011) if p.name.endswith("radius") else p for p in snapshot.parameters_si))
    graph = replace(graph, snapshot_id=snapshot.snapshot_id)
    request = replace(request, snapshot_id=snapshot.snapshot_id, feature_graph_sha256=graph.content_sha256)
    with WorkerSupervisor() as supervisor:
        service = GeometryBuildService(OCCTAdapter(command(native_config, "occt"), supervisor, enabled=True), tmp_path,
                                       step_reader=command(native_config, "step_reader"))
        _, future = service.submit(request, snapshot, graph, FixtureReference("sphere"))
        candidate = future.result(timeout=60)
        qa = json.loads(candidate.evidence_json)
        assert candidate.record.state is BuildState.REJECTED and not candidate.record.artifacts
        assert not candidate.record.published_artifacts
        assert not qa["qa-step"]["dimensions_pass"] and qa["qa-step"]["relative_volume_error"] > .1
        service.close()
