"""Calculated nonfinite diagnostics must not be delivered as successful estimates."""

import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.integration import monte_carlo, simpson, trapezoidal


def test_monte_carlo_variance_overflow_is_not_success():
    with pytest.raises(SolverConvergenceError):
        monte_carlo.integrate(lambda x: 1e308 * x, 0, 1, samples=100, seed=42)


@pytest.mark.parametrize("method", [trapezoidal.integrate, simpson.integrate])
def test_quadrature_arithmetic_overflow_is_typed(method):
    with pytest.raises(SolverConvergenceError):
        method(lambda x: 1e308, 0, 1)


def test_ad_gradient_callback_failure_is_typed():
    import math

    from numerics.automatic_differentiation.gradients import gradient

    with pytest.raises(SolverConvergenceError):
        gradient(lambda x: math.sin(x[0]), [1.0])


def test_malformed_spline_slopes_are_input_error():
    from numerics.interpolation.cubic_spline import CubicSpline

    with pytest.raises(InvalidInputError):
        CubicSpline.build([0, 1], [0, 1], boundary="clamped", endpoint_slopes=(1,))
