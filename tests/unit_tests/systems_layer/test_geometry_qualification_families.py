import math

import pytest

from tests.fixtures.geometry_qualification_families import (
    FAMILIES,
    area_reference,
    family_plan,
    family_policy,
    surface,
)


@pytest.mark.parametrize("kind", FAMILIES)
def test_every_declared_family_has_independent_area_and_source_bound_critical_coverage(
    kind,
):
    plan = family_plan(kind)
    policy = family_policy(plan)
    assert len(policy["parts"]) == len(plan.parts)
    assert all(p["reference_area_m2"] > 0 for p in policy["parts"])
    assert sum(len(p["critical_features"]) for p in policy["parts"]) >= len(plan.parts)


def test_independent_annular_frustum_formula_reduces_to_literal_cylinder():
    expected = 2 * math.pi * (0.0035 + 0.0047) * 0.04 + 2 * math.pi * (
        0.0047**2 - 0.0035**2
    )
    assert area_reference(family_plan("pipe.circular").parts[0]) == pytest.approx(
        expected, rel=1e-14
    )


def test_flange_formula_includes_bore_walls_and_removes_both_planar_openings():
    expected = (
        2 * math.pi * (0.015 + 0.035) * 0.004
        + 2 * math.pi * (0.035**2 - 0.015**2)
        + 6 * (2 * math.pi * 0.002 * 0.004 - 2 * math.pi * 0.002**2)
    )
    assert area_reference(
        family_plan("interface.bolted_flange").parts[0]
    ) == pytest.approx(expected, rel=1e-14)


def test_blind_groove_has_one_retained_floor_not_a_through_hole():
    flange = area_reference(family_plan("interface.bolted_flange").parts[0])
    grooved = area_reference(family_plan("interface.face_groove").parts[0])
    assert grooved - flange == pytest.approx(
        2 * math.pi * (0.018 + 0.021) * 0.001, rel=1e-12
    )


def test_sector_includes_two_radial_plane_faces_and_both_end_caps():
    assert surface(
        ((0.0, 0.01, 0.02), (0.03, 0.01, 0.02)), (0.0, 0.4)
    ) == pytest.approx(
        0.4 * (0.01 + 0.02) * 0.03
        + 2 * (0.02 - 0.01) * 0.03
        + 0.4 * (0.02**2 - 0.01**2),
        rel=1e-14,
    )


def test_rigid_placement_preserves_independent_area_but_changes_world_witnesses():
    before, after = family_plan("pipe.circular"), family_plan("placement.rigid")
    assert area_reference(before.parts[0]) == area_reference(after.parts[0])
    assert (
        family_policy(before)["parts"][0]["critical_features"]
        != family_policy(after)["parts"][0]["critical_features"]
    )
