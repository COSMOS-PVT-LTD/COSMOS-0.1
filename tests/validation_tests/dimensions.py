"""Validation tests for dimensional analysis."""

from __future__ import annotations

from core.dimension import FORCE, LENGTH, MASS, PRESSURE, TIME, VELOCITY


def test_mass_flow_rate_closure() -> None:
    assert (MASS / TIME).is_compatible_with(MASS / TIME)


def test_kinematic_relation_velocity() -> None:
    assert (LENGTH / TIME).is_compatible_with(VELOCITY)


def test_newton_second_law_dimension() -> None:
    assert (MASS * LENGTH / TIME**2).is_compatible_with(FORCE)


def test_pressure_from_force_over_area() -> None:
    assert (FORCE / LENGTH**2).is_compatible_with(PRESSURE)
