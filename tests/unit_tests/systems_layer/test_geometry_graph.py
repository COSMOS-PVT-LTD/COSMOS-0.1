from dataclasses import replace

import pytest

from systems.contracts.geometry import (
    CoordinateFrame,
    GeometryContractError,
    GeometryFeatureGraph,
)
from tests.fixtures.geometry_contracts import IDENTITY, graph, snapshot


def test_deterministic_topological_order_and_transitive_dependents():
    value = graph()
    assert value.topological_order() == ("chamber", "independent", "interface")
    assert value.transitive_dependents(("chamber",)) == ("chamber", "interface")
    assert value.to_json() == replace(value, features=tuple(reversed(value.features))).to_json()
    assert value == GeometryFeatureGraph.from_json(value.to_json())


def test_parameter_change_invalidates_only_actual_dependents():
    source = snapshot()
    target = snapshot(radius=11, revision="r2")
    value = graph(source)
    impact = value.impact(source, target)
    assert impact.changed_features == ("chamber",)
    assert impact.stale_features == ("chamber", "interface")
    assert impact.snapshot_is_stale
    before, after = dict(value.fingerprints(source)), dict(value.fingerprints(target))
    assert before["independent"] == after["independent"]
    assert before["interface"] != after["interface"]


def test_unrelated_parameter_or_revision_does_not_invent_feature_dependencies():
    source = snapshot()
    target = replace(source, revision_id="r2", parameters_si=tuple(replace(p, value_si=.9) if p.name == "unrelated" else p for p in source.parameters_si))
    impact = graph(source).impact(source, target)
    assert impact.snapshot_is_stale and impact.stale_features == ()
    assert dict(graph(source).fingerprints(source)) == dict(graph(source).fingerprints(target))


def test_removed_parameter_invalidates_root_and_descendants():
    source = snapshot()
    target = replace(source, parameters_si=tuple(p for p in source.parameters_si if p.name != "radius"))
    assert graph(source).impact(source, target).stale_features == ("chamber", "interface")


def test_ancestor_frame_change_invalidates_child_frame_features():
    source = snapshot()
    source = replace(source, frames=(*source.frames, CoordinateFrame("local", "world", (0, 0, .1), IDENTITY)))
    value = graph(source)
    value = replace(value, features=tuple(replace(f, frame_id="local") if f.feature_id == "chamber" else f for f in value.features))
    target = replace(source, frames=tuple(replace(f, origin_m=(.1, 0, 0)) if f.frame_id == "world" else f for f in source.frames))
    assert set(value.impact(source, target).stale_features) == {"chamber", "interface", "independent"}


def test_changed_source_identity_invalidates_consumers():
    source = snapshot()
    target = replace(source, source_refs=(replace(source.source_refs[0], source_sha256="b" * 64),))
    assert set(graph(source).impact(source, target).stale_features) == {"chamber", "interface", "independent"}


@pytest.mark.parametrize("mutation", ["cycle", "unknown_dependency", "duplicate", "missing_output", "unknown_parameter", "unknown_frame"])
def test_invalid_graphs_fail_closed(mutation):
    source = snapshot()
    value = graph(source)
    features = list(value.features)
    with pytest.raises(GeometryContractError):
        if mutation == "cycle":
            features[0] = replace(features[0], dependency_ids=("interface",))
        elif mutation == "unknown_dependency":
            features[0] = replace(features[0], dependency_ids=("absent",))
        elif mutation == "duplicate":
            features.append(features[0])
        elif mutation == "missing_output":
            replace(value, output_feature_ids=("absent",))
        elif mutation == "unknown_parameter":
            features[0] = replace(features[0], parameter_refs=("absent",))
        elif mutation == "unknown_frame":
            features[0] = replace(features[0], frame_id="absent")
        result = replace(value, features=features)
        result.validate_snapshot(source)


def test_stale_or_foreign_snapshot_cannot_validate_graph():
    value = graph()
    with pytest.raises(GeometryContractError):
        value.validate_snapshot(snapshot(revision="r2"))
    with pytest.raises(GeometryContractError):
        value.impact(snapshot(), replace(snapshot(), project_id="other"))


def test_large_graph_rejected_and_unknown_invalidation_does_not_silently_noop():
    value = graph()
    with pytest.raises(GeometryContractError):
        replace(value, features=tuple(replace(value.features[0], feature_id="feature"+str(i)) for i in range(513)))
    with pytest.raises(GeometryContractError):
        value.transitive_dependents(("not-real",))


def test_local_binding_reuse_preserves_original_fingerprint_definition():
    from systems.contracts.geometry._wire import digest
    source = snapshot()
    value = graph(source)
    by_id = {f.feature_id: f for f in value.features}
    expected = {}
    for name in value.topological_order():
        feature = by_id[name]
        expected[name] = digest({"feature": feature.to_canonical_dict(),
                                 "parameters": {p: source.parameter_hash(p) for p in feature.parameter_refs},
                                 "frame": source.frame_hash(feature.frame_id),
                                 "dependencies": {d: expected[d] for d in feature.dependency_ids}})
    assert value.fingerprints(source) == tuple(expected.items())
