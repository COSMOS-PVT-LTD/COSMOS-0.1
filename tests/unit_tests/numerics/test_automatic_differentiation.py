import math

import numpy as np
import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.automatic_differentiation.forward_mode import (
    Dual,
    cos,
    derivative,
    exp,
    log,
    sin,
    sqrt,
)
from numerics.automatic_differentiation.gradients import gradient
from numerics.automatic_differentiation.jacobians import jacobian


@pytest.mark.parametrize("f,exact",[(lambda x:x**3,12),(lambda x:sin(x),math.cos(2)),
                                    (lambda x:cos(x),-math.sin(2)),(lambda x:exp(x),math.exp(2)),
                                    (lambda x:log(x),.5),(lambda x:sqrt(x),1/(2*math.sqrt(2))),
                                    (lambda x:3/x,-.75),(lambda x:7.,0.)])
def test_scalar_chain_rules(f,exact):
    assert derivative(f,2)==pytest.approx(exact,abs=2e-14)

def test_multivariable_gradient_and_jacobian():
    point=[2.,3.]
    np.testing.assert_allclose(gradient(lambda x:x[0]**2*x[1]+sin(x[1]),point),[12,4+math.cos(3)],atol=1e-14)
    np.testing.assert_allclose(jacobian(lambda x:[x[0]*x[1],exp(x[0])+x[1]**2,4.],point),
                               [[3,2],[math.exp(2),6],[0,0]],atol=1e-14)
    np.testing.assert_array_equal(gradient(lambda x:1.,point),[0,0])
    # A tiny increment is never sampled: derivative remains exactly chain-rule.
    assert derivative(lambda x:x**2,1e-20)==2e-20

def test_ad_domains_and_no_silent_fd():
    with pytest.raises(InvalidInputError):
        log(Dual(-1,np.ones(1)))
    with pytest.raises(InvalidInputError):
        Dual(1,np.ones(2))+Dual(2,np.ones(3))
    with pytest.raises(InvalidInputError):
        derivative(lambda x:x/0,1)
    with pytest.raises(SolverConvergenceError):
        derivative(lambda x:math.sin(x),1)
    with pytest.raises(SolverConvergenceError):
        exp(Dual(1000,np.ones(1)))
