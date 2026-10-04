import numpy as np
import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.optimization import bfgs, conjugate_gradient, gradient_descent
from numerics.utilities.tolerances import Tolerances


@pytest.mark.parametrize(
    "method", [gradient_descent.minimize, conjugate_gradient.minimize, bfgs.minimize]
)
def test_quadratic_stationarity_determinism(method):
    a = np.array([[3.0, 1.0], [1.0, 2.0]])
    objective = lambda x: float(0.5 * x @ a @ x - np.array([1.0, 2.0]) @ x)
    gradient = lambda x: a @ x - np.array([1.0, 2.0])
    result = method(
        objective,
        gradient,
        [3.0, -2.0],
        tolerances=Tolerances(residual=1e-7, max_iterations=1000),
    )
    np.testing.assert_allclose(
        result.solution.value, np.linalg.solve(a, [1, 2]), atol=1e-7
    )
    assert np.linalg.norm(gradient(result.solution.value)) < 1e-7
    assert all(
        a >= b for a, b in zip(result.objective_history, result.objective_history[1:])
    )
    assert (
        result.objective_history
        == method(
            objective,
            gradient,
            [3.0, -2.0],
            tolerances=Tolerances(residual=1e-7, max_iterations=1000),
        ).objective_history
    )


def test_bfgs_rosenbrock():
    def objective(x):
        return float(100 * (x[1] - x[0] ** 2) ** 2 + (1 - x[0]) ** 2)

    def gradient(x):
        return np.array(
            [
                -400 * x[0] * (x[1] - x[0] ** 2) - 2 * (1 - x[0]),
                200 * (x[1] - x[0] ** 2),
            ]
        )

    result = bfgs.minimize(
        objective,
        gradient,
        [-1.2, 1],
        tolerances=Tolerances(residual=1e-7, max_iterations=300),
    )
    np.testing.assert_allclose(result.solution.value, [1, 1], atol=1e-7)
    assert result.objective < 1e-14
    assert result.solution.residual_norm < 1e-7


def test_negative_and_budget():
    with pytest.raises(InvalidInputError):
        gradient_descent.minimize(lambda x: 1.0, lambda x: x, [1], step_size=0)
    with pytest.raises(SolverConvergenceError):
        bfgs.minimize(lambda x: float("nan"), lambda x: x, [1])
    with pytest.raises(SolverConvergenceError):
        bfgs.minimize(lambda x: float(x @ x), lambda x: np.array([1, 2]), [1])
    with pytest.raises(SolverConvergenceError):
        gradient_descent.minimize(
            lambda x: float(x @ x),
            lambda x: 2 * x,
            [1],
            step_size=0.01,
            tolerances=Tolerances(max_iterations=1),
        )
