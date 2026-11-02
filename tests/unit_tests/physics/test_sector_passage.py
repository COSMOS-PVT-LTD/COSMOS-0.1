"""Independent section geometry checks, not coolant correlation qualification."""
import math

import numpy as np
import pytest

from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from physics.fluids.sector_passage import annular_sector_section


def section(a=.02, b=.023, theta=.14):
    return annular_sector_section(Quantity(a, SI.get("m")), Quantity(b, SI.get("m")), Quantity(theta, SI.get("rad")))


def test_area_perimeter_and_uniform_radial_depth_closed_form():
    a, b, theta = 2., 3., math.pi / 2
    row = section(a, b, theta)
    assert row.area_m2 == pytest.approx(5 * math.pi / 4)
    assert row.wetted_perimeter_m == pytest.approx(5 * math.pi / 2 + 2)
    assert row.hydraulic_diameter_m == pytest.approx(4 * row.area_m2 / row.wetted_perimeter_m)


@pytest.mark.parametrize("theta", [.001, .14, math.pi / 2, math.pi, 5.5])
def test_centroid_and_area_against_independent_polar_quadrature(theta):
    a, b = .02, .027
    radii = np.linspace(a, b, 20001)
    angles = np.linspace(-theta / 2, theta / 2, 20001)
    integral = lambda x, y: np.sum((y[1:] + y[:-1]) * np.diff(x) / 2)
    area = integral(radii, radii) * integral(angles, np.ones(len(angles)))
    moment = integral(radii, radii**2) * integral(angles, np.cos(angles))
    row = section(a, b, theta)
    assert row.area_m2 == pytest.approx(area, rel=1e-12)
    assert row.centroid_radius_m == pytest.approx(moment / area, rel=1e-8)


def test_length_scale_laws_and_thin_limit():
    a, b = section(), section(.2, .23)
    assert b.area_m2 == pytest.approx(100 * a.area_m2)
    for name in ("wetted_perimeter_m", "hydraulic_diameter_m", "centroid_radius_m"):
        assert getattr(b, name) == pytest.approx(10 * getattr(a, name))
    thin = section(1., 1. + 1e-9, .2)
    assert thin.hydraulic_diameter_m == pytest.approx(2e-9, rel=1e-6)
    assert thin.centroid_radius_m == pytest.approx(math.sin(.1) / .1, rel=1e-8)


@pytest.mark.parametrize("args", [(0, 1, 1), (1, 1, 1), (2, 1, 1), (1, 2, 0), (1, 2, 2 * math.pi),
                                  (1, 2, -1), (1, math.inf, 1), (1, 2, math.nan), (1e200, 2e200, 1)])
def test_invalid_or_unrepresentable_geometry_rejects(args):
    with pytest.raises(InvalidInputError):
        section(*args)


def test_core_dimensions_precede_geometry():
    with pytest.raises(DimensionError):
        annular_sector_section(Quantity(2, SI.get("Pa")), Quantity(3, SI.get("m")), Quantity(.2, SI.get("rad")))
