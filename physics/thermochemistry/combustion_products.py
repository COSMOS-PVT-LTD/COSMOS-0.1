"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.combustion_products
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Normalize combustion-product mole fractions as a COSMOS mixture.
"""

from __future__ import annotations

from physics.thermochemistry.cea_interface import ThermochemicalResult
from physics.thermochemistry.mixtures import Mixture, from_mole_fractions

__all__ = ("mixture_from_result",)


def mixture_from_result(
    result: ThermochemicalResult,
    *,
    normalize: bool = False,
) -> Mixture:
    """
    Convert a normalized engine result into a ``Mixture``.

    Elemental conservation of the result against the original propellants
    is an engine responsibility; this helper only enforces mixture axioms.
    """

    return from_mole_fractions(result.mole_fractions, normalize=normalize)
