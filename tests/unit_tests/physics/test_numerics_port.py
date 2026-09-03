"""Contract tests for PHYS-004 numerics port (waiver scope verification)."""

from __future__ import annotations

import math

import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from physics.compressible_flow.area_mach import area_ratio, mach_from_area_ratio
from physics.compressible_flow.expansion_fan import mach_from_prandtl_meyer, prandtl_meyer
from physics.compressible_flow.oblique_shock import evaluate_oblique_shock, wave_angle
from physics.contracts import numerics_port

GAMMA = 1.4


def test_bracketed_root_uses_documented_fallback() -> None:
    assert numerics_port.bracketed_root is numerics_port._fallback_bisection


def test_fallback_invalid_bracket_raises() -> None:
    with pytest.raises(InvalidInputError, match="lower < upper"):
        numerics_port._fallback_bisection(lambda x: x, 1.0, 0.5)


def test_fallback_no_sign_change_raises() -> None:
    with pytest.raises(
        SolverConvergenceError,
        match="does not change sign",
    ):
        numerics_port._fallback_bisection(lambda x: x * x + 1.0, 0.0, 1.0)


def test_fallback_non_finite_residual_raises() -> None:
    with pytest.raises(SolverConvergenceError, match="non-finite"):
        numerics_port._fallback_bisection(lambda x: float("nan"), 0.0, 1.0)


def test_fallback_is_deterministic() -> None:
    residual = lambda x: x * x - 2.0
    first = numerics_port._fallback_bisection(residual, 0.0, 2.0)
    second = numerics_port._fallback_bisection(residual, 0.0, 2.0)
    assert first == second


def test_area_mach_inverse_round_trip() -> None:
    for mach, branch in ((0.5, "subsonic"), (2.0, "supersonic"), (4.0, "supersonic")):
        ar = area_ratio(mach, GAMMA)
        recovered = mach_from_area_ratio(ar, GAMMA, branch=branch)
        assert recovered == pytest.approx(mach, rel=1.0e-8)


def test_prandtl_meyer_inverse_round_trip() -> None:
    for mach in (1.5, 2.0, 3.0):
        nu = prandtl_meyer(mach, GAMMA)
        recovered = mach_from_prandtl_meyer(nu, GAMMA)
        assert recovered == pytest.approx(mach, rel=1.0e-8)


def test_oblique_shock_inverse_matches_evaluate() -> None:
    theta = math.radians(20.0)
    mach = 3.0
    state = evaluate_oblique_shock(mach, theta, GAMMA)
    beta = wave_angle(mach, theta, GAMMA, branch="weak")
    assert beta == pytest.approx(state.wave_angle_rad, rel=1.0e-8)
