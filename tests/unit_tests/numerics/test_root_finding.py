"""NUM-002 independent scalar equations and adversarial contract regressions."""

import math

import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.root_finding import (
    bisection,
    brent,
    fixed_point,
    newton_raphson,
    regula_falsi,
    secant,
)
from numerics.utilities.tolerances import Tolerances

CASES = [
    (lambda x: x*x - 2, lambda x: 2*x, 0., 2., math.sqrt(2)),
    (math.sin, math.cos, 3., 4., math.pi),
    (lambda x: math.cos(x)-x, lambda x: -math.sin(x)-1, 0., 1., .7390851332151607),
    (lambda x: x**3-x-2, lambda x: 3*x*x-1, 1., 2., 1.5213797068045676),
    (lambda x: math.exp(x)-3, math.exp, 0., 2., math.log(3)),
]


@pytest.mark.parametrize("function,derivative,a,b,expected", CASES)
@pytest.mark.parametrize("method", [bisection, brent, regula_falsi, secant, newton_raphson])
def test_analytic_roots(function, derivative, a, b, expected, method):
    kwargs = {"derivative": derivative} if method is newton_raphson else {}
    args = ((a + b)/2,) if method is newton_raphson else (a, b)
    result = method.solve(function, *args, **kwargs)
    assert result.converged
    assert result.value == pytest.approx(expected, abs=2e-11)
    assert abs(function(result.value)) < 2e-10
    assert result.iterations <= 80
    assert result.residual_history
    assert result == method.solve(function, *args, **kwargs)


@pytest.mark.parametrize("method", [bisection, brent, regula_falsi])
@pytest.mark.parametrize("root", [0., 1.])
def test_endpoint_and_invalid_bracket(method, root):
    assert method.solve(lambda x: x-root, 0, 1).value == root
    with pytest.raises(InvalidInputError, match="change sign"):
        method.solve(lambda x: x*x+1, 0, 1)
    with pytest.raises(InvalidInputError):
        method.solve(lambda x: x, 1, 0)


@pytest.mark.parametrize("method", [bisection, brent, regula_falsi])
def test_nonfinite_and_exhaustion(method):
    with pytest.raises(SolverConvergenceError, match="non-finite"):
        method.solve(lambda x: math.nan, 0, 1)
    with pytest.raises(SolverConvergenceError, match="MAX_ITERATIONS"):
        method.solve(lambda x: x*x-2, 0, 2, policy=Tolerances(max_iterations=1))


def test_bisection_compatibility_extreme_scale_and_tiny_residual():
    assert bisection.find_root(lambda x: x, -1e308, 1e308) == 0
    assert bisection.find_root(lambda x: (x-.3)*1e-300, 0, 1) == pytest.approx(.3, abs=1e-12)
    result = bisection.solve(lambda x: x/1e300 - 1, 0, 2e300,
                            policy=Tolerances(absolute=1e-12, relative=1e-12))
    assert result.value/1e300 == pytest.approx(1, rel=1e-12)
    assert bisection.find_root(lambda x: x-1e-15, 0, 2e-15, xtol=1e-20) == pytest.approx(1e-15)
    for kwargs in ({"xtol": 0}, {"xtol": -1}, {"xtol": math.nan}, {"max_iter": 0}):
        with pytest.raises(InvalidInputError):
            bisection.find_root(lambda x: x, -1, 1, **kwargs)


def test_brent_preserves_bracket_and_does_not_accept_jump_as_exact_root():
    sampled = []
    def residual(x):
        sampled.append(x)
        return x*x-2
    result = brent.solve(residual, 0, 2)
    assert all(0 <= x <= 2 for x in sampled)
    assert result.absolute_error_estimate <= 1e-12
    assert result.method == "brent-style"
    assert dict(result.diagnostics)["bracket_lower"]


def test_brent_rejects_bracket_collapse_without_a_small_residual():
    with pytest.raises(SolverConvergenceError):
        brent.solve(lambda x: -1.0 if x < .3 else 1.0, 0, 1)


def test_newton_modes_failures_and_no_hidden_algorithm_switch():
    result = newton_raphson.solve(lambda x: x*x-2, 1., numerical_step=1e-5)
    assert result.value == pytest.approx(math.sqrt(2), abs=1e-11)
    with pytest.raises(InvalidInputError):
        newton_raphson.solve(lambda x: x, 1)
    with pytest.raises(SolverConvergenceError, match="zero"):
        newton_raphson.solve(lambda x: x*x+1, 0, derivative=lambda x: 2*x)
    with pytest.raises(SolverConvergenceError, match="non-finite"):
        newton_raphson.solve(lambda x: x-2, 1, derivative=lambda x: math.nan)
    with pytest.raises(SolverConvergenceError):
        secant.solve(lambda x: 1, 0, 1)


def test_fixed_point_contraction_and_divergence():
    result = fixed_point.solve(math.cos, .5, contraction_bound=.9)
    assert result.value == pytest.approx(.7390851332151607, abs=1e-11)
    assert result.absolute_error_estimate <= 1e-12
    assert result == fixed_point.solve(math.cos, .5, contraction_bound=.9)
    with pytest.raises(SolverConvergenceError, match="contraction"):
        fixed_point.solve(lambda x: 2*x, 1, contraction_bound=.9)
    with pytest.raises(InvalidInputError):
        fixed_point.solve(math.cos, 1, contraction_bound=1)
