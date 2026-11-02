"""Domain-neutral Bezier sampling identities and failure boundaries."""

import numpy as np
import pytest

from core.exceptions import InvalidInputError
from numerics.mesh.parametric_curve import quadratic_bezier


def test_bezier_endpoints_midpoint_and_tangents():
    controls = np.array([[0, 1], [2, 4], [5, 6]], dtype=float)
    curve, tangents = quadratic_bezier(controls, 5)
    np.testing.assert_allclose(curve[[0, -1]], controls[[0, -1]])
    np.testing.assert_allclose(
        curve[2], (controls[0] + 2 * controls[1] + controls[2]) / 4
    )
    np.testing.assert_allclose(tangents[0], 2 * (controls[1] - controls[0]))
    np.testing.assert_allclose(tangents[-1], 2 * (controls[2] - controls[1]))


@pytest.mark.parametrize("count", [True, 2, 2002, 5.5])
def test_bezier_rejects_bad_counts(count):
    with pytest.raises(InvalidInputError):
        quadratic_bezier([[0, 0], [1, 1], [2, 2]], count)


@pytest.mark.parametrize("points", [[[0, 0], [1, 1]], [[0, 0], [1, np.nan], [2, 2]]])
def test_bezier_rejects_bad_controls(points):
    with pytest.raises(InvalidInputError):
        quadratic_bezier(points, 5)
