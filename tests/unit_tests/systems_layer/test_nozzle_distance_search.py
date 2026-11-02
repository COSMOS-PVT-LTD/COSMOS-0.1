import numpy as np
import pytest

from systems.geometry.qa import distances_to_triangles


def test_conservative_explicit_ceiling_pruning_matches_full_triangle_distances():
    triangles = np.array([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]], [[10., 0., 0.], [11., 0., 0.], [10., 1., 0.]]])
    points = np.array([[.1, .1, .01], [.3, .2, .02]])
    full = distances_to_triangles(points, triangles)
    bounded = distances_to_triangles(points, triangles, ceiling_m=.03)
    assert np.array_equal(full, bounded)
    missing = distances_to_triangles(points + [100., 0, 0], triangles, ceiling_m=.03)
    assert np.isinf(missing).all()  # No finite nearest-distance claim for discarded geometry.


def test_triangle_distance_checks_cancellation_or_budget_before_admission():
    def cancelled():
        raise RuntimeError("cancelled")
    with pytest.raises(RuntimeError, match="cancelled"):
        distances_to_triangles(np.zeros((1, 3)), np.ones((1, 3, 3)), ceiling_m=.01, check_budget=cancelled)
