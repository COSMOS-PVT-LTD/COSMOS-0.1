"""Engineering unit compatibility for GUI quantity payloads."""

from __future__ import annotations

import pytest

from core.quantity import Quantity
from core.unit import SI


def test_bar_kpa_mpa_convert_to_si() -> None:
    assert Quantity(70.0, SI.get("bar")).to_si() == pytest.approx(7.0e6)
    assert Quantity(7000.0, SI.get("kPa")).to_si() == pytest.approx(7.0e6)
    assert Quantity(7.0, SI.get("MPa")).to_si() == pytest.approx(7.0e6)


def test_kn_converts_to_newtons() -> None:
    assert Quantity(10.0, SI.get("kN")).to_si() == pytest.approx(10000.0)
