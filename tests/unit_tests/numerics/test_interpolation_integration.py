import math

import numpy as np
import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.integration import (
    adaptive,
    gaussian,
    monte_carlo,
    romberg,
    simpson,
    trapezoidal,
)
from numerics.interpolation import (
    barycentric,
    hermite,
    lagrange,
    linear,
    polynomial,
    spline,
)
from numerics.utilities.convergence import observed_order
from numerics.utilities.tolerances import Tolerances


@pytest.mark.parametrize("method",[polynomial.interpolate,lagrange.interpolate,barycentric.interpolate])
def test_polynomial_exact_and_nodes(method):
    x = np.linspace(0,1,6)
    y = x**4-2*x+1
    for q in np.linspace(0,1,21):
        assert method(x,y,float(q)) == pytest.approx(q**4-2*q+1,abs=2e-14)
    with pytest.raises(InvalidInputError):
        method(x,y,2)
    with pytest.raises(InvalidInputError):
        method([0,0,1],[1,2,3],0.2)

def test_piecewise_and_cubic():
    assert linear.interpolate([0,1],[1,3],0.25) == 1.5
    assert linear.interpolate([0,1],[1,3],2,extrapolate=True) == 5
    with pytest.raises(InvalidInputError):
        linear.interpolate([1,0],[1,3],0.2)
    x = np.linspace(0,1,8)
    curve = spline.build(x,x**3,boundary="clamped",endpoint_slopes=(0,3))
    for q in np.linspace(0,1,21):
        assert curve(float(q)) == pytest.approx(q**3,abs=3e-14)
        assert hermite.interpolate(x,x**3,3*x*x,float(q)) == pytest.approx(q**3,abs=3e-14)
    natural = spline.build(x,2*x+1)
    assert np.max(np.abs(natural.second_derivatives)) < 1e-12
    assert natural(0.34) == pytest.approx(1.68)
    with pytest.raises(InvalidInputError):
        natural(2)
    with pytest.raises(InvalidInputError):
        spline.build(x,x,boundary="periodic")

@pytest.mark.parametrize("f,a,b,exact",[(lambda x:x,0,1,.5),(lambda x:x*x,0,1,1/3),
                                       (math.sin,0,math.pi,2),(math.exp,0,1,math.e-1)])
def test_analytic_quadrature(f,a,b,exact):
    assert trapezoidal.integrate(f,a,b,intervals=1000) == pytest.approx(exact,abs=2e-6)
    assert simpson.integrate(f,a,b) == pytest.approx(exact,abs=2e-8)
    assert gaussian.integrate(f,a,b) == pytest.approx(exact,abs=1e-12)
    assert romberg.integrate(f,a,b).value == pytest.approx(exact,abs=1e-10)
    assert adaptive.integrate(f,a,b,tolerances=Tolerances(max_iterations=3000)).value == pytest.approx(exact,abs=1e-10)

@pytest.mark.parametrize("method,expected",[(trapezoidal.integrate,2),(simpson.integrate,4)])
def test_quadrature_orders(method,expected):
    errors = [abs(method(math.exp,0,1,intervals=n)-(math.e-1)) for n in (10,20,40)]
    assert observed_order(errors[0],errors[1]) == pytest.approx(expected,abs=.03)
    assert observed_order(errors[1],errors[2]) == pytest.approx(expected,abs=.03)

@pytest.mark.parametrize("n",[1,2,3,8,16])
def test_legendre_independent_and_exact(n):
    x,w = gaussian.legendre_rule(n)
    refx,refw = np.polynomial.legendre.leggauss(n)
    np.testing.assert_allclose(x,refx,atol=2e-15)
    np.testing.assert_allclose(w,refw,atol=2e-14)
    for power in range(2*n):
        assert np.dot(w,x**power) == pytest.approx(0 if power%2 else 2/(power+1),abs=3e-14)

def test_sampling_reproducible():
    a = monte_carlo.integrate(lambda x:x*x,0,1,samples=20000,seed=42)
    assert a == monte_carlo.integrate(lambda x:x*x,0,1,samples=20000,seed=42)
    assert abs(a.value-1/3) < 4*a.standard_error

def test_quadrature_invalid_failure():
    with pytest.raises(InvalidInputError):
        simpson.integrate(math.sin,0,1,intervals=3)
    with pytest.raises(InvalidInputError):
        trapezoidal.integrate(math.sin,1,0)
    for method in (trapezoidal.integrate,simpson.integrate,gaussian.integrate,romberg.integrate,adaptive.integrate):
        with pytest.raises(SolverConvergenceError):
            method(lambda x:float("nan"),0,1)
    with pytest.raises(SolverConvergenceError):
        adaptive.integrate(math.exp,0,1,tolerances=Tolerances(max_iterations=1))
    with pytest.raises(SolverConvergenceError):
        romberg.integrate(math.exp,0,1,tolerances=Tolerances(max_iterations=1))
