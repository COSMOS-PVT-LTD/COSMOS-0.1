"""Continuum manufactured/analytic V&V separate from implementation unit tests."""

import pytest

from tools.benchmark_numerics_foundation import studies


@pytest.fixture(scope="module")
def packet():
    return studies()


@pytest.mark.parametrize(
    "name,expected",
    [
        ("trapezoid", 2),
        ("simpson", 4),
        ("euler", 1),
        ("rk4", 4),
        ("fd-central-first", 2),
        ("fd-central-second", 2),
        ("fd-fourth-first", 4),
        ("linear-interpolation", 2),
        ("clamped-cubic", 4),
        ("poisson", 2),
        ("heat", 2),
        ("wave", 2),
        ("fv-diffusion", 2),
        ("fem-interpolant", 2),
    ],
)
def test_three_resolution_study(packet, name, expected):
    rows = packet[name]
    assert len(rows) == 3
    assert all(row.error > 0 for row in rows)
    assert rows[0].error > rows[1].error > rows[2].error
    for row in rows[1:]:
        assert row.order == pytest.approx(expected, abs=0.15)
