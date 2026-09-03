"""Unit tests for compressible-flow application adapter (GUI boundary)."""

from __future__ import annotations

import pytest

from api.physics_compressible import (
    evaluate_area_mach,
    evaluate_bartz_htc,
    evaluate_isentropic_stagnation,
    evaluate_thin_wall_stress,
    map_engineering_error,
)
from core.exceptions import InvalidInputError


def test_isentropic_anderson_mach_two() -> None:
    result = evaluate_isentropic_stagnation(2.0, 1.4)
    assert result["ok"] is True
    assert result["model"]["model_id"] == "PHYS-004.isentropic.stagnation"
    assert result["model"]["validation_status"] == "NOT_CLAIMED"
    assert result["outputs"]["T0_over_T"]["value"] == pytest.approx(1.8)
    assert result["outputs"]["p0_over_p"]["value"] == pytest.approx(7.824449066867263)
    assert result["outputs"]["rho0_over_rho"]["value"] == pytest.approx(4.3469161482595915)
    assert result["inputs"]["mach"]["unit"] == "1"


def test_area_mach_forward_and_inverse_round_trip() -> None:
    forward = evaluate_area_mach(mode="forward", gamma=1.4, mach=2.0)
    assert forward["ok"] is True
    ratio = forward["outputs"]["A_over_Astar"]["value"]
    assert ratio == pytest.approx(1.6875)
    inverse = evaluate_area_mach(
        mode="inverse",
        gamma=1.4,
        area_ratio_value=ratio,
        branch="supersonic",
    )
    assert inverse["outputs"]["mach"]["value"] == pytest.approx(2.0, rel=1.0e-10)
    assert any("PATH A" in w for w in inverse["warnings"])


def test_bartz_adapter_returns_htc() -> None:
    result = evaluate_bartz_htc(
        {
            "diameter_m": 0.05,
            "viscosity_pa_s": 1.0e-4,
            "conductivity_w_m_k": 0.25,
            "cp_j_kg_k": 2000.0,
            "chamber_pressure_pa": 7.0e6,
            "cstar_m_s": 1500.0,
            "mach": 1.0,
            "gamma": 1.2,
            "wall_temperature_k": 800.0,
            "adiabatic_wall_temperature_k": 3000.0,
        }
    )
    assert result["ok"] is True
    assert result["operation"] == "bartz_htc"
    assert result["outputs"]["h"]["unit"] == "W/(m2 K)"
    assert result["outputs"]["h"]["value"] > 0.0
    assert result["validation"]["status"] == "NOT_CLAIMED"


def test_thin_wall_adapter_returns_stresses() -> None:
    result = evaluate_thin_wall_stress(
        {
            "pressure_pa": 5.0e6,
            "radius_m": 0.1,
            "thickness_m": 0.008,
            "temperature_k": 300.0,
        }
    )
    assert result["ok"] is True
    assert result["outputs"]["hoop_stress"]["value"] == pytest.approx(6.25e7)
    assert result["validation"]["status"] == "NOT_CLAIMED"


def test_invalid_gamma_maps_to_typed_error_payload() -> None:
    with pytest.raises(InvalidInputError):
        evaluate_isentropic_stagnation(2.0, 1.0)
    status, payload = map_engineering_error(InvalidInputError("gamma must satisfy 1 < gamma <= 3."))
    assert status == 400
    assert payload["ok"] is False
    assert payload["error"]["code"] == "InvalidInputError"


def test_gui_static_slice_has_no_physics_equations() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for name in ("physics-compressible.js", "propulsion-suite.js"):
        js = (root / "gui" / "static" / name).read_text(encoding="utf-8")
        forbidden = ("stagnation_temperature_ratio", "((gamma-1)/2)", "area_ratio(", "T0/T")
        for token in forbidden:
            assert token not in js, f"{name} embeds {token}"
