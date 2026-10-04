"""Contract tests for PHYS-004 numerics port (canonical Numerics integration verification)."""

from __future__ import annotations

import math

import pytest

from core.exceptions import InvalidInputError, SolverConvergenceError
from physics.compressible_flow.area_mach import area_ratio, mach_from_area_ratio
from physics.compressible_flow.expansion_fan import (
    mach_from_prandtl_meyer,
    prandtl_meyer,
)
from physics.compressible_flow.oblique_shock import evaluate_oblique_shock, wave_angle
from physics.contracts import numerics_port

GAMMA = 1.4


def test_bracketed_root_uses_canonical_numerics_when_present() -> None:
    from numerics.root_finding.bisection import find_root

    assert numerics_port.bracketed_root is find_root


def test_canonical_invalid_bracket_raises() -> None:
    with pytest.raises(InvalidInputError, match="lower < upper"):
        numerics_port.bracketed_root(lambda x: x, 1.0, 0.5)


def test_canonical_no_sign_change_raises() -> None:
    with pytest.raises(
        InvalidInputError,
        match="does not change sign",
    ):
        numerics_port.bracketed_root(lambda x: x * x + 1.0, 0.0, 1.0)


def test_canonical_non_finite_residual_raises() -> None:
    with pytest.raises(SolverConvergenceError, match="non-finite"):
        numerics_port.bracketed_root(lambda x: float("nan"), 0.0, 1.0)


def test_canonical_is_deterministic() -> None:
    residual = lambda x: x * x - 2.0
    first = numerics_port.bracketed_root(residual, 0.0, 2.0)
    second = numerics_port.bracketed_root(residual, 0.0, 2.0)
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


def test_actual_numerics_solver_invoked_with_physics_residuals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from numerics.root_finding import bisection
    from physics.compressible_flow.oblique_shock import deflection_from_wave_angle

    actual = bisection.solve
    calls: list[str] = []

    def observed(residual, lower, upper, *, policy):
        calls.append(residual.__module__)
        return actual(residual, lower, upper, policy=policy)

    monkeypatch.setattr(bisection, "solve", observed)
    target_area = area_ratio(2.0, GAMMA)
    recovered = mach_from_area_ratio(target_area, GAMMA, branch="supersonic")
    assert abs(area_ratio(recovered, GAMMA) - target_area) < 1e-10
    target_nu = prandtl_meyer(2.5, GAMMA)
    recovered = mach_from_prandtl_meyer(target_nu, GAMMA)
    assert abs(prandtl_meyer(recovered, GAMMA) - target_nu) < 1e-10
    theta = math.radians(15)
    beta = wave_angle(3.0, theta, GAMMA, branch="weak")
    assert abs(deflection_from_wave_angle(3.0, beta, GAMMA) - theta) < 1e-10
    assert len(calls) == 3
    assert all(module.startswith("physics.compressible_flow.") for module in calls)


def test_no_solver_fallback_or_optional_provider() -> None:
    import inspect

    source = inspect.getsource(numerics_port)
    assert "_fallback_bisection" not in source
    assert "except ImportError" not in source
