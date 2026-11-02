"""Domain-neutral quadratic Bezier sampling, including first derivatives."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import FloatArray, invalid


def quadratic_bezier(
    control_points: ArrayLike, count: int
) -> tuple[FloatArray, FloatArray]:
    points = np.asarray(control_points, dtype=float)
    if points.shape != (3, 2) or not np.all(np.isfinite(points)):
        invalid("Bezier control_points must be a finite 3 by 2 array.")
    if isinstance(count, bool) or not isinstance(count, int) or not 3 <= count <= 2001:
        invalid("Bezier count must be an integer from 3 to 2001.")
    t = np.linspace(0, 1, count)[:, None]
    curve = (1 - t) ** 2 * points[0] + 2 * t * (1 - t) * points[1] + t**2 * points[2]
    derivative = 2 * ((1 - t) * (points[1] - points[0]) + t * (points[2] - points[1]))
    if not np.all(np.isfinite(curve)) or not np.all(np.isfinite(derivative)):
        invalid("Bezier sampling produced non-finite coordinates.")
    return curve, derivative
