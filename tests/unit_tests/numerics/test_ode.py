import math

import numpy as np
import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.ode.implicit import step as backward
from numerics.ode.ode_solver import adaptive, fixed
from numerics.utilities.convergence import observed_order
from numerics.utilities.tolerances import Tolerances


@pytest.mark.parametrize(
    "method,order", [("euler", 1), ("heun", 2), ("midpoint", 2), ("rk2", 2), ("rk4", 4)]
)
def test_orders(method, order):
    errors = [
        abs(
            fixed(lambda t, y: y, [1], 0, 1, step_size=h, method=method).states[-1, 0]
            - math.e
        )
        for h in (0.05, 0.025, 0.0125)
    ]
    for i in (0, 1):
        assert observed_order(errors[i], errors[i + 1]) == pytest.approx(
            order, abs=0.08
        )


def test_decay_and_oscillator():
    decay = fixed(lambda t, y: -2 * y, [1], 0, 1, step_size=0.01)
    assert decay.states[-1, 0] == pytest.approx(math.exp(-2), abs=5e-10)
    oscillator = fixed(
        lambda t, y: np.array([y[1], -y[0]]), [1, 0], 0, 2 * math.pi, step_size=0.01
    )
    np.testing.assert_allclose(oscillator.states[-1], [1, 0], atol=1e-8)
    assert np.max(np.abs(np.sum(oscillator.states**2, axis=1) - 1)) < 1e-9
    assert oscillator.times[-1] == 2 * math.pi


def test_adaptive_rejection_tolerance_replay():
    result = adaptive(lambda t, y: y, [1], 0, 1, first_step=1)
    assert result.rejected_steps > 0
    assert result.states[-1, 0] == pytest.approx(math.e, abs=4e-10)
    assert (
        result.local_error_ratios
        == adaptive(lambda t, y: y, [1], 0, 1, first_step=1).local_error_ratios
    )
    assert (
        len(result.local_error_ratios) == result.accepted_steps + result.rejected_steps
    )
    looser = adaptive(
        lambda t, y: y,
        [1],
        0,
        1,
        first_step=1,
        tolerances=Tolerances(absolute=1e-5, relative=1e-5),
    )
    assert looser.accepted_steps < result.accepted_steps


def test_backward_euler_real_residual():
    value = backward(lambda t, y: -20 * y, 0, [1], 0.1, numerical_step=1e-5)
    assert value[0] == pytest.approx(1 / 3, abs=1e-10)
    assert abs(value[0] - 1 + 0.1 * 20 * value[0]) < 1e-10
    errors = []
    for h in (0.05, 0.025, 0.0125):
        y = np.array([1.0])
        for i in range(round(1 / h)):
            y = backward(lambda t, y: -y, i * h, y, h, numerical_step=1e-5)
        errors.append(abs(y[0] - math.exp(-1)))
    assert observed_order(errors[-2], errors[-1]) == pytest.approx(1, abs=0.04)


def test_ode_failure_paths():
    with pytest.raises(InvalidInputError):
        fixed(lambda t, y: y, [1], 1, 0, step_size=0.1)
    with pytest.raises(SolverConvergenceError):
        fixed(lambda t, y: y, [1], 0, 1, step_size=0.1, max_steps=2)
    with pytest.raises(SolverConvergenceError):
        adaptive(lambda t, y: y, [1], 0, 1, first_step=1, min_step=1, max_step=1)
    with pytest.raises(SolverConvergenceError):
        adaptive(lambda t, y: y, [1], 0, 1, first_step=1, max_steps=1)
    with pytest.raises(SolverConvergenceError):
        fixed(lambda t, y: np.array([np.nan]), [1], 0, 1, step_size=0.1)
    with pytest.raises(SolverConvergenceError):
        fixed(lambda t, y: np.array([1, 2]), [1], 0, 1, step_size=0.1)
