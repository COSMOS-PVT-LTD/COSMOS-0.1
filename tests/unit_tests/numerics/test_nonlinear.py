import numpy as np
import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.nonlinear_solver.nonlinear_system import solve
from numerics.nonlinear_solver.numerical_jacobian import jacobian
from numerics.nonlinear_solver.trust_region import bounded_step
from numerics.utilities.tolerances import Tolerances


def residual(x):
    return np.array([x[0] ** 2 + x[1] ** 2 - 5, x[0] - x[1] - 1])


def analytic(x):
    return np.array([[2 * x[0], 2 * x[1]], [1.0, -1.0]])


@pytest.mark.parametrize("mode", ["analytic", "numerical", "bounded"])
def test_known_system(mode):
    options = (
        {"numerical_step": 1e-5} if mode == "numerical" else {"jacobian": analytic}
    )
    if mode == "bounded":
        options["trust_radius"] = 0.2
    result = solve(residual, [3.0, 1.5], **options)
    np.testing.assert_allclose(result.value, [2, 1], atol=1e-10)
    assert np.linalg.norm(residual(result.value)) <= 1e-10
    assert all(
        a >= b for a, b in zip(result.residual_history, result.residual_history[1:])
    )
    assert (
        result.residual_history
        == solve(residual, [3.0, 1.5], **options).residual_history
    )


def test_jacobian_and_cap():
    np.testing.assert_allclose(
        jacobian(residual, [2.0, 1.0], step=1e-5), analytic([2.0, 1.0]), atol=1e-9
    )
    np.testing.assert_allclose(bounded_step([3, 4], 2), [1.2, 1.6])
    with pytest.raises(InvalidInputError):
        bounded_step([1], 0)
    with pytest.raises(InvalidInputError):
        solve(residual, [2, 1])


def test_fail_closed():
    with pytest.raises(SolverConvergenceError):
        solve(lambda x: np.ones(2), [1, 1], jacobian=lambda x: np.zeros((2, 2)))
    with pytest.raises(SolverConvergenceError):
        solve(
            residual,
            [3.0, 1.5],
            jacobian=analytic,
            tolerances=Tolerances(max_iterations=1),
        )
    with pytest.raises(SolverConvergenceError):
        solve(lambda x: np.array([np.nan]), [1.0], numerical_step=1e-5)
    with pytest.raises(SolverConvergenceError):
        solve(
            lambda x: np.array([x[0] ** 2 + 1]),
            [1.0],
            jacobian=lambda x: np.array([[2 * x[0]]]),
        )
