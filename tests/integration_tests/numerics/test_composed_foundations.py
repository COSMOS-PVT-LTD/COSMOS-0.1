"""Real cross-package compositions; no engineering application model."""

import numpy as np

from numerics.automatic_differentiation.gradients import gradient
from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_volume.fv_solver import solve
from numerics.mesh.grid_generation import uniform_1d
from numerics.mesh.refinement import refine
from numerics.nonlinear_solver.nonlinear_system import solve as solve_nonlinear
from numerics.ode.implicit import step
from numerics.optimization.bfgs import minimize
from numerics.utilities.tolerances import Tolerances


def test_ad_gradient_drives_real_optimizer():
    def model(x):
        return (x[0] - 2) ** 2 + 3 * (x[1] + 1) ** 2

    result = minimize(
        lambda x: float(model(x)),
        lambda x: gradient(model, x),
        [5.0, 4.0],
        tolerances=Tolerances(residual=1e-8, max_iterations=200),
    )
    np.testing.assert_allclose(result.solution.value, [2, -1], atol=1e-8)
    assert result.objective < 1e-14


def test_refined_mesh_drives_conservative_fv():
    mesh = refine(uniform_1d(0, 1, 6))
    result = solve(mesh.x, np.zeros(len(mesh.cells)), DirichletBoundary(1, 3))
    centers = (mesh.x[:-1] + mesh.x[1:]) / 2
    np.testing.assert_allclose(result.solution.value, 1 + 2 * centers, atol=3e-14)
    np.testing.assert_allclose(result.face_fluxes, -2, atol=2e-13)
    assert abs(result.global_balance) < 1e-12


def test_implicit_system_uses_nonlinear_and_linear_foundations():
    a = np.array([[-3.0, 1.0], [1.0, -2.0]])
    value = step(lambda t, y: a @ y, 0, [1.0, 2.0], 0.2, numerical_step=1e-5)
    expected = np.linalg.solve(np.eye(2) - 0.2 * a, [1.0, 2.0])
    np.testing.assert_allclose(value, expected, atol=1e-11)
    solved = solve_nonlinear(
        lambda x: (np.eye(2) - 0.2 * a) @ x - np.array([1.0, 2.0]),
        [1.0, 2.0],
        jacobian=lambda x: np.eye(2) - 0.2 * a,
    )
    np.testing.assert_allclose(solved.value, value, atol=1e-11)
