from copy import deepcopy

import numpy as np
import pytest

from systems.geometry.qualification_policy import validate
from systems.geometry.surface_discrepancy import (
    TriangleTree,
    closest_triangle,
    sample_surface,
    statistics,
)
from tests.fixtures.component_geometry import plan
from tests.fixtures.geometry_qualification import pipe_policy


def test_policy_is_explicit_and_source_bound():
    p = pipe_policy()
    assert validate(p, plan("pipe.circular")) == p


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "part",
        "nan",
        "bool",
        "unit",
        "unknown",
        "zero",
        "resolutions",
        "duplicate-resolution",
        "order",
        "point",
        "off-surface",
        "span",
        "no-critical",
        "region",
        "boundary",
        "mesh",
        "sampling",
        "source",
        "use-list",
        "kind-list",
        "region-list",
        "boundary-scope-list",
    ],
)
def test_policy_rejects_missing_unbounded_or_unmatched_evidence(case):
    p = deepcopy(pipe_policy())
    part = p["parts"][0]
    if case == "missing":
        p.pop("reference_source")
    elif case == "part":
        part["part_id"] = "another-body"
    elif case == "nan":
        part["relative_volume"] = float("nan")
    elif case == "bool":
        part["centroid_m"] = True
    elif case == "unit":
        p["unit_system"] = "mm"
    elif case == "unknown":
        p["manufacturing_acceptance"] = True
    elif case == "zero":
        part["bounds_m"] = 0
    elif case == "resolutions":
        p["refinement_resolutions_m"] = [0.0005, 0.00025]
    elif case == "duplicate-resolution":
        p["refinement_resolutions_m"] = [0.0005, 0.00025, 0.00025]
    elif case == "order":
        p["refinement_resolutions_m"].reverse()
    elif case == "point":
        part["critical_features"][0]["points_m"][0] = [True, 0, 0]
    elif case == "off-surface":
        part["critical_features"][0]["points_m"][0] = [0.02, 0.004, 0]
    elif case == "span":
        part["critical_features"][0]["maximum_m"] = 0.0001
    elif case == "no-critical":
        part["critical_features"] = []
    elif case == "region":
        p["regions"][0]["role"] = "fluid"
    elif case == "boundary":
        p["boundaries"][0]["part_id"] = "missing"
    elif case == "mesh":
        p["mesh_intent"]["minimum_feature_m"] = 0.001
    elif case == "sampling":
        p["sampling"]["samples_per_part"] = 2049
    elif case == "use-list":
        p["intended_use"] = []
    elif case == "kind-list":
        part["critical_features"][0]["kind"] = []
    elif case == "region-list":
        p["regions"][0]["part_id"] = []
    elif case == "boundary-scope-list":
        p["boundaries"][0]["scope"] = []
    else:
        p["applicability"] = ""
    with pytest.raises(ValueError):
        validate(p, plan("pipe.circular"))


def sheet():
    return np.array(
        [[[0.0, 0, 0], [1, 0, 0], [0, 1, 0]], [[1, 1, 0], [0, 1, 0], [1, 0, 0]]]
    )


@pytest.mark.parametrize(
    "point,expected",
    [
        ([0.25, 0.25, 1], 1),
        ([0.5, 0.5, 0], 0),
        ([2, 0, 0], 1),
        ([-1, -1, 0], 2**0.5),
        ([1, 1, -0.25], 0.25),
    ],
)
def test_direct_nearest_triangle_not_vertex_proxy(point, expected):
    tree = TriangleTree(sheet())
    d, q, index = tree.nearest(point)
    assert d == pytest.approx(expected) and index in {0, 1}
    assert np.linalg.norm(np.asarray(point) - q) == pytest.approx(expected)


def test_tree_matches_brute_force_on_rotated_disjoint_triangles():
    rng = np.random.default_rng(182)
    t = rng.normal(size=(250, 3, 3))
    tree = TriangleTree(t)
    for p in rng.normal(size=(25, 3)):
        assert tree.nearest(p)[0] == pytest.approx(closest_triangle(p, t)[0], abs=1e-12)


def test_sampling_repeatability_outliers_and_full_maximum():
    points, ids = sample_surface(sheet() + [0, 0, 0.02], 32)
    assert np.array_equal(ids, sample_surface(sheet() + [0, 0, 0.02], 32)[1])
    summary = statistics(TriangleTree(sheet()), points, 0.001, 3)
    assert (
        not summary["pass"]
        and summary["outlier_count"] == 32
        and len(summary["outliers"]) == 3
    )
    assert summary["maximum_m"] == pytest.approx(0.02) and summary[
        "p95_m"
    ] == pytest.approx(0.02)


def test_direct_comparison_detects_different_meshes_not_common_reference_proxy():
    p, _ = sample_surface(sheet(), 32)
    assert statistics(TriangleTree(sheet() + [0, 0, 0.03]), p, 0.001, 3)[
        "maximum_m"
    ] == pytest.approx(0.03)


@pytest.mark.parametrize("bad", [np.zeros((1, 3, 3)), sheet() * float("nan")])
def test_bad_triangles_cannot_pass(bad):
    with pytest.raises(ValueError):
        TriangleTree(bad).nearest([0, 0, 0])


@pytest.mark.parametrize("action", ["start", "retry", "cancel"])
def test_readonly_writes_denied_before_loading_artifacts_or_runtime(action):
    from systems.geometry.qualification import GeometryQualification
    from systems.projects.authority import AccessDenied, Principal

    service = GeometryQualification.__new__(GeometryQualification)
    actor = Principal("synthetic-viewer", "VIEWER")
    arguments = {
        "start": (actor, "project", {}, "hash"),
        "retry": (actor, "project", "job", "op", "hash"),
        "cancel": (actor, "project", "job", None, "op", "hash"),
    }
    with pytest.raises(AccessDenied):
        getattr(service, action)(*arguments[action])
