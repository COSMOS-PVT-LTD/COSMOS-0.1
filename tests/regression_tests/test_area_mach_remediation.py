"""Inverse identities and bounded failure for REMEDIATION-001."""

import math

import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from physics.compressible_flow.area_mach import area_ratio, mach_from_area_ratio


@pytest.mark.parametrize("gamma", [1.10, 1.20, 1.30, 1.40, 1.67])
@pytest.mark.parametrize(
    "ratio", [1.0, 1.000001, 1.1, 2.0, 5.0, 10.0, 50.0, 100.0, 1000.0]
)
@pytest.mark.parametrize("branch", ["subsonic", "supersonic"])
def test_forward_inverse_identity(gamma: float, ratio: float, branch: str) -> None:
    mach = mach_from_area_ratio(ratio, gamma, branch=branch)
    assert math.isfinite(mach)
    assert 0 < mach <= 1 if branch == "subsonic" else mach >= 1
    # Absolute Mach bisection tolerance of 1e-12 gives relative area error
    # below 2e-9 over this grid, including the small subsonic roots.
    assert area_ratio(mach, gamma) == pytest.approx(ratio, rel=2e-9, abs=2e-12)


def test_supersonic_root_beyond_original_mach_cap() -> None:
    mach = mach_from_area_ratio(1e12, 1.67)
    assert mach > 80
    assert area_ratio(mach, 1.67) == pytest.approx(1e12, rel=2e-9)


def test_numerical_search_limit_fails_with_diagnostics() -> None:
    with pytest.raises(SolverConvergenceError, match="limit.*gamma|gamma.*limit"):
        mach_from_area_ratio(1e300, 1.67)


@pytest.mark.parametrize("ratio", [0.9, float("nan"), float("inf")])
def test_invalid_area_ratio(ratio: float) -> None:
    with pytest.raises(InvalidInputError):
        mach_from_area_ratio(ratio, 1.4)


def test_invalid_branch_at_sonic_identity() -> None:
    with pytest.raises(InvalidInputError):
        mach_from_area_ratio(1.0, 1.4, branch="unknown")
