import numpy as np
import pytest

from core.exceptions import InvalidInputError
from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_element import assembly, gauss_quadrature, shape_functions
from numerics.finite_element.boundary_conditions import impose_dirichlet
from numerics.finite_element.elements import LinearElement
from numerics.finite_element.fem_solver import solve
from numerics.finite_element.stiffness_matrix import stiffness
from numerics.utilities.convergence import observed_order


def test_element_exact_and_partition():
    element = LinearElement(2, 4)
    np.testing.assert_allclose(
        stiffness(element, 3), 1.5 * np.array([[1, -1], [-1, 1]])
    )
    for xi in (-1, -0.3, 0, 0.8, 1):
        assert sum(shape_functions.values(xi)) == pytest.approx(1)
        assert element.map(xi) == pytest.approx(3 + xi)
    x, w = gauss_quadrature.points(element, order=3)
    assert np.dot(w, x**4) == pytest.approx((4**5 - 2**5) / 5, abs=1e-12)
    np.testing.assert_allclose(shape_functions.derivatives(), [-0.5, 0.5])


def test_assembly_bc_and_linear_solution():
    x = np.array([0.0, 0.1, 0.3, 0.7, 1.0])
    a, b = assembly.assemble(x, lambda x: 2.0)
    assert b.sum() == pytest.approx(2)
    np.testing.assert_allclose(a, a.T)
    constrained, _ = impose_dirichlet(a, b, DirichletBoundary(1, 3))
    assert np.linalg.eigvalsh(constrained).min() > 0
    result = solve(x, lambda x: 0.0, DirichletBoundary(1, 3))
    np.testing.assert_allclose(result.value, 1 + 2 * x, atol=2e-14)
    assert result.residual_norm < 1e-12


def test_manufactured_piecewise_interpolant_refinement():
    errors = []
    for n in (10, 20, 40):
        x = np.linspace(0, 1, n + 1)
        result = solve(
            x, lambda q: np.pi**2 * np.sin(np.pi * q), DirichletBoundary(0, 0)
        )
        midpoint = (x[:-1] + x[1:]) / 2
        interpolant = (result.value[:-1] + result.value[1:]) / 2
        errors.append(np.max(np.abs(interpolant - np.sin(np.pi * midpoint))))
        assert result.residual_norm < 1e-11
    assert observed_order(errors[0], errors[1]) == pytest.approx(2, abs=0.03)
    assert observed_order(errors[1], errors[2]) == pytest.approx(2, abs=0.03)


def test_bad_element_input():
    with pytest.raises(InvalidInputError):
        LinearElement(1, 0)
    with pytest.raises(InvalidInputError):
        shape_functions.values(2)
    with pytest.raises(InvalidInputError):
        solve([0, 0, 1], lambda x: 0.0, DirichletBoundary(0, 0))
