"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.shells
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Thin-shell membrane stresses (cylinder/sphere aliases).
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.solid_mechanics.pressure_vessels import ThinWallCylinder, cylinder, sphere

__all__ = ("cylindrical_membrane", "spherical_membrane")


def cylindrical_membrane(
    pressure: Quantity,
    radius: Quantity,
    thickness: Quantity,
) -> ThinWallCylinder:
    """Thin cylindrical shell membrane stresses."""

    return cylinder(pressure, radius, thickness)


def spherical_membrane(
    pressure: Quantity,
    radius: Quantity,
    thickness: Quantity,
) -> Quantity:
    """Thin spherical shell membrane stress."""

    return sphere(pressure, radius, thickness)
