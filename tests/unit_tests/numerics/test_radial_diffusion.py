"""Independent analytic checks; no experimental-validation claims."""
import math
from itertools import pairwise

import pytest

from core.exceptions import InvalidInputError
from numerics.finite_volume.radial_diffusion import DiffusionCancelled, solve
from physics.heat_transfer.spherical_conduction import reference_temperature


@pytest.mark.parametrize("cells", [8, 16, 32, 64])
def test_independent_analytic_temperature_and_actual_conservation(cells):
    result = solve(.01, cells, 10, 1e6, 300, tolerance=1e-10, max_iterations=50_000)
    errors = [abs(v - reference_temperature(.01, r, 10, 1e6, 300)) for r, v in zip(result.centers, result.values)]
    assert result.converged and result.termination == "residual_tolerance"
    assert max(errors) < 1e6 * .01**2 / (6 * 10 * cells**2)
    assert sum(result.volumes) == pytest.approx(4 * math.pi * .01**3 / 3, rel=1e-14)
    assert result.generated == pytest.approx(4.188790204786391, rel=1e-14)
    assert abs(result.outward - result.generated) / result.generated < 2 * math.sqrt(cells) * 1e-10
    assert result.residual_history[0] == 1 and result.residual_history[-1] <= 1e-10
    assert len(result.residual_history) <= 502 and all(b > a for a, b in zip(result.iterations[:-1], result.iterations[1:]))


def test_second_order_refinement_not_merely_solver_success():
    errors = []
    for cells in (8, 16, 32, 64):
        value = solve(.01, cells, 10, 1e6, 300, tolerance=1e-10, max_iterations=50_000)
        errors.append(max(abs(v - reference_temperature(.01, r, 10, 1e6, 300)) for r, v in zip(value.centers, value.values)))
    assert all(3.9 < a / b < 4.1 for a, b in pairwise(errors))


def test_genuine_iteration_limit_has_no_numerical_success():
    value = solve(.01, 16, 10, 1e6, 300, tolerance=1e-8, max_iterations=1)
    assert not value.converged and value.termination == "iteration_limit"
    assert value.residual_history[-1] > 1e-8
    assert abs(value.outward - value.generated) / value.generated > 1e-2


def test_cancel_produces_no_solution():
    with pytest.raises(DiffusionCancelled):
        solve(.01, 64, 10, 1e6, 300, tolerance=1e-10, max_iterations=50_000, cancelled=lambda: True)


@pytest.mark.parametrize("change", [{"radius": -1}, {"diffusivity": 0}, {"source": float("nan")}, {"boundary": float("inf")},
                                    {"cells": True}, {"cells": 10000}, {"tolerance": 0}, {"max_iterations": 0}])
def test_invalid_data_refused(change):
    args = {"radius": .01, "cells": 16, "diffusivity": 10, "source": 1e6, "boundary": 300, "tolerance": 1e-8, "max_iterations": 10000}
    with pytest.raises(InvalidInputError):
        solve(**{**args, **change})


@pytest.mark.parametrize("radius,k,q,surface", [(.02, 20, 2e6, 500), (.005, 1, 1000, 100), (.01, 10, 1e6, 300)])
def test_no_hidden_material_or_boundary_defaults(radius, k, q, surface):
    result = solve(radius, 16, k, q, surface, tolerance=1e-10, max_iterations=10000)
    assert result.converged
    assert max(abs(v - reference_temperature(radius, r, k, q, surface)) for r, v in zip(result.centers, result.values)) < q * radius**2 / (6 * k * 16**2)
