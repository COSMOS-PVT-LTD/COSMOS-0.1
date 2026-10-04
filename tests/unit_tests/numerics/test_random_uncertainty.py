import numpy as np
import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.random import distributions, sampling, seeds
from numerics.sensitivity.local import gradient
from numerics.sensitivity.parameter_scan import scan
from numerics.uncertainty.confidence_interval import mean_interval
from numerics.uncertainty.latin_hypercube import sample
from numerics.uncertainty.monte_carlo import sample_and_propagate
from numerics.uncertainty.statistics import summarize


def test_rng_replay_and_distribution_moments():
    a=distributions.normal(2,3,40000,seed=51)
    np.testing.assert_array_equal(a,distributions.normal(2,3,40000,seed=51))
    assert a.mean()==pytest.approx(2,abs=.06)
    assert a.var()==pytest.approx(9,abs=.2)
    u=distributions.uniform(-1,1,10000,seed=2)
    assert np.min(u)>=-1 and np.max(u)<1
    assert abs(u.mean())<.02
    children=seeds.child_seeds(42,10)
    assert len(set(children))==10 and children==seeds.child_seeds(42,10)
    np.testing.assert_array_equal(sampling.sample([1,2,3],3,seed=1,replace=False),
                                  sampling.sample([1,2,3],3,seed=1,replace=False))

def test_lhs_strata_replay():
    data=sample(20,3,seed=52)
    np.testing.assert_array_equal(data,sample(20,3,seed=52))
    for j in range(3):
        np.testing.assert_array_equal(np.sort(np.floor(20*data[:,j])),np.arange(20))

def test_propagation_analytic_moments():
    result=sample_and_propagate(lambda x:x[0]+2*x[1],[0,0],[1,1],samples=30000,seed=11)
    stats=result.statistics
    assert abs(stats.mean-1.5)<4*stats.standard_error
    assert stats.variance==pytest.approx(5/12,abs=.01)
    replay=sample_and_propagate(lambda x:x[0]+2*x[1],[0,0],[1,1],samples=30000,seed=11)
    np.testing.assert_array_equal(result.outputs,replay.outputs)
    ci=mean_interval(result.outputs)
    assert ci.lower<stats.mean<ci.upper
    assert ci.method=="large-sample-normal-approximation-IID"
    known=mean_interval([1,2,3],known_normal_sigma=2)
    assert known.upper-2==pytest.approx(1.959963984540054*2/np.sqrt(3))
    assert summarize([1,2,3]).variance==1

def test_local_scan_and_failures():
    np.testing.assert_allclose(gradient(lambda x:x[0]**2+3*x[1],[2,1],step=1e-5),[4,3],atol=1e-9)
    np.testing.assert_array_equal(scan(lambda x:x[0]**2,[[1],[2],[3]]).outputs,[1,4,9])
    with pytest.raises(InvalidInputError):
        distributions.normal(0,0,10,seed=1)
    with pytest.raises(InvalidInputError):
        seeds.validate(-1)
    with pytest.raises(InvalidInputError):
        mean_interval([1,2,3])
    with pytest.raises(SolverConvergenceError):
        sample_and_propagate(lambda x:float("nan"),[0],[1],samples=10,seed=1)
