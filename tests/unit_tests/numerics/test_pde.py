import numpy as np
import pytest

from core.exceptions import InvalidInputError
from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.pde import heat_equation, laplace, poisson, wave_equation
from numerics.utilities.convergence import observed_order


def test_poisson_laplace_residual_refinement():
    errors = []
    for n in (10, 20, 40):
        x = np.linspace(0, 1, n + 1)
        result = poisson.solve(
            x, -(np.pi**2) * np.sin(np.pi * x), DirichletBoundary(0, 0)
        )
        errors.append(np.max(np.abs(result.value - np.sin(np.pi * x))))
        assert result.residual_norm < 1e-10
        linear = laplace.solve(x, DirichletBoundary(1, 3))
        np.testing.assert_allclose(linear.value, 1 + 2 * x, atol=2e-13)
    assert observed_order(errors[0], errors[1]) == pytest.approx(2, abs=0.02)
    assert observed_order(errors[1], errors[2]) == pytest.approx(2, abs=0.02)


@pytest.mark.parametrize("method", ["explicit", "implicit"])
def test_heat_manufactured_and_constant(method):
    x = np.linspace(0, 1, 21)
    initial = np.sin(np.pi * x)
    initial[[0, -1]] = 0
    result = heat_equation.solve(
        x,
        initial,
        DirichletBoundary(0, 0),
        diffusivity=1,
        time_step=0.0005,
        steps=20,
        method=method,
    )
    np.testing.assert_allclose(
        result.states[-1], np.exp(-(np.pi**2) * 0.01) * np.sin(np.pi * x), atol=0.0005
    )
    assert max(result.residual_history) < 1e-12
    constant = heat_equation.solve(
        x,
        np.ones(21),
        DirichletBoundary(1, 1),
        diffusivity=1,
        time_step=0.001,
        steps=10,
        method=method,
    )
    np.testing.assert_allclose(constant.states, 1, atol=2e-14)


def test_wave_initial_and_refinement():
    errors = []
    for n in (20, 40, 80):
        x = np.linspace(0, 1, n + 1)
        u = np.sin(np.pi * x)
        u[[0, -1]] = 0
        result = wave_equation.solve(
            x,
            u,
            np.zeros(n + 1),
            DirichletBoundary(0, 0),
            wave_speed=1,
            time_step=0.5 / n,
            steps=n // 2,
        )
        errors.append(
            np.max(np.abs(result.states[-1] - np.cos(np.pi * 0.25) * np.sin(np.pi * x)))
        )
        assert max(result.residual_history) < 1e-12
    assert observed_order(errors[-2], errors[-1]) == pytest.approx(2, abs=0.02)


def test_pde_fail_closed():
    x = np.linspace(0, 1, 11)
    with pytest.raises(InvalidInputError):
        heat_equation.solve(
            x,
            np.zeros(11),
            DirichletBoundary(0, 0),
            diffusivity=1,
            time_step=0.1,
            steps=2,
        )
    with pytest.raises(InvalidInputError):
        wave_equation.solve(
            x,
            np.zeros(11),
            np.zeros(11),
            DirichletBoundary(0, 0),
            wave_speed=1,
            time_step=0.2,
            steps=2,
        )
    with pytest.raises(InvalidInputError):
        heat_equation.solve(
            x,
            np.ones(11),
            DirichletBoundary(0, 0),
            diffusivity=1,
            time_step=0.001,
            steps=2,
        )
