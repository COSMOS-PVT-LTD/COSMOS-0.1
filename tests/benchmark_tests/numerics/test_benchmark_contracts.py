"""Timings have no pass/fail threshold; benchmark problems must remain real/qualified."""

import math

import numpy as np
import pytest

from tools.benchmark_numerics_foundation import benchmark_cases, benchmarks


def test_benchmark_case_correctness():
    cases = benchmark_cases()
    assert cases["root-sqrt2"]() == pytest.approx(math.sqrt(2), abs=2e-12)
    linear = cases["linear-16"]()
    np.testing.assert_allclose(linear.value, 1, atol=1e-14)
    ode = cases["ode-exp-rk4-200"]()
    assert ode.states[-1, 0] == pytest.approx(math.e, abs=2e-11)
    assert np.isfinite(cases["fd-sin-1001"]()).all()
    fv = cases["fv-diffusion-32"]()
    assert abs(fv.global_balance) < 1e-11
    result = benchmarks(2)
    assert set(result) == set(cases)
    for row in result.values():
        assert (
            0
            <= row["minimum_seconds"]
            <= row["median_seconds"]
            <= row["maximum_seconds"]
        )
