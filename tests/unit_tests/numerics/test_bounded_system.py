"""Domain-neutral bounded nonlinear termination/refusal fixtures."""
import numpy as np
import pytest

from core.exceptions import InvalidInputError
from numerics.nonlinear_solver.bounded import solve


def run(function, *, initial=(1.,), lower=(.1,), upper=(4.,), **policy):
    return solve(function, np.array(initial), np.array(lower), np.array(upper), step=1e-5, tolerance=1e-9, max_iterations=policy.get("iterations", 30), max_evaluations=policy.get("evaluations", 200), max_seconds=10.)


def test_independent_square_root_and_history():
    value = run(lambda x: x**2 - 2)
    assert value.converged and value.value[0] == pytest.approx(2**.5)
    assert value.history[0]["state"] == [1.]
    assert value.history[-1]["infinity_norm"] <= 1e-9


def test_root_outside_bounds_is_not_clipped_success():
    value = run(lambda x: x - 8)
    assert not value.converged and value.termination == "LINE_SEARCH_FAILED"


def test_domain_rejection_during_line_search():
    def residual(x):
        if x[0] <= .5:
            raise ValueError("invalid domain")
        return np.log(x)
    value = run(residual, initial=(3.,))
    assert value.converged and value.value[0] == pytest.approx(1.)
    assert any(row["rejected_trials"] for row in value.history)


@pytest.mark.parametrize("policy,termination", [({"iterations": 1}, "MAX_ITERATIONS"), ({"evaluations": 1}, "MAX_EVALUATIONS")])
def test_budgets_are_not_convergence(policy, termination):
    value = run(lambda x: x**2 - 2, **policy)
    assert not value.converged and value.termination == termination


def test_singular_and_invalid_initial():
    assert run(lambda x: np.ones(1)).termination == "SINGULAR_JACOBIAN"
    with pytest.raises(InvalidInputError):
        run(lambda x: x, initial=(.1,))
