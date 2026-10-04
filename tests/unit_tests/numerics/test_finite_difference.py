import numpy as np
import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.finite_difference import (
    explicit,
    first_order,
    higher_order,
    implicit,
    second_order,
    stability,
)
from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.utilities.convergence import observed_order


@pytest.mark.parametrize(
    "scheme,order", [("forward", 1), ("backward", 1), ("central", 2)]
)
def test_first_derivative_order(scheme, order):
    errors = []
    for n in (20, 40, 80):
        x = np.linspace(0, 1, n + 1)
        d = first_order.differentiate(np.sin(x), 1 / n, scheme=scheme)
        errors.append(np.max(np.abs(d[1:-1] - np.cos(x[1:-1]))))
    assert observed_order(errors[-2], errors[-1]) == pytest.approx(order, abs=0.08)


def test_second_and_fourth_stencils():
    errors2, errors4 = [], []
    for n in (20, 40, 80):
        x = np.linspace(0, 1, n + 1)
        errors2.append(
            np.max(
                np.abs(second_order.differentiate(np.sin(x), 1 / n) + np.sin(x[1:-1]))
            )
        )
        errors4.append(
            np.max(
                np.abs(
                    higher_order.first_derivative(np.sin(x), 1 / n) - np.cos(x[2:-2])
                )
            )
        )
        np.testing.assert_allclose(
            higher_order.second_derivative(x**4, 1 / n), 12 * x[2:-2] ** 2, atol=2e-11
        )
        np.testing.assert_allclose(
            higher_order.first_derivative(x**4, 1 / n), 4 * x[2:-2] ** 3, atol=2e-13
        )
    assert observed_order(errors2[-2], errors2[-1]) == pytest.approx(2, abs=0.08)
    assert observed_order(errors4[-2], errors4[-1]) == pytest.approx(4, abs=0.03)


def test_operators_updates_boundary_and_stability():
    x = np.linspace(0, 1, 6)
    a = second_order.operator(x)
    np.testing.assert_allclose(
        a, np.diag([-50.0] * 4) + np.diag([25.0] * 3, 1) + np.diag([25.0] * 3, -1)
    )
    y = np.sin(np.pi * x[1:-1])
    np.testing.assert_allclose(
        explicit.update(y, a, np.zeros(4), 0.01, stability_limit=0.02),
        y + 0.01 * (a @ y),
    )
    new = implicit.update(y, a, np.zeros(4), 0.1)
    assert np.linalg.norm((np.eye(4) - 0.1 * a) @ new - y) < 1e-12
    assert stability.diffusion_limit(1, 0.2) == pytest.approx(0.02)
    assert stability.cfl(2, 0.1, 0.2) == 1
    assert DirichletBoundary(0, 1).right == 1
    with pytest.raises(InvalidInputError):
        explicit.update(y, a, np.zeros(4), 0.03, stability_limit=0.02)


def test_invalid_stencils():
    with pytest.raises(InvalidInputError):
        second_order.operator([0, 0.2, 1])
    with pytest.raises(InvalidInputError):
        first_order.differentiate([1, 2], 1)
    with pytest.raises(InvalidInputError):
        higher_order.first_derivative([1, 2, 3], 1)
    with pytest.raises(InvalidInputError):
        implicit.update([1], np.eye(2), [0], 0.1)
    with pytest.raises(InvalidInputError):
        DirichletBoundary(float("nan"), 0)


@pytest.mark.parametrize(
    "method",
    [
        second_order.differentiate,
        higher_order.first_derivative,
        higher_order.second_derivative,
    ],
)
def test_nonfinite_derivative_rejected(method):
    with pytest.raises(SolverConvergenceError):
        method([1e308, -1e308, 1e308, -1e308, 1e308], 1)
