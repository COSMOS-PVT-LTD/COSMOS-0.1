"""
Independent fluid property reference benchmarks (PHYS-002-NIST-001).

Expected values are documented from cited sources and are NOT copied from
``physics/fluids/records.py`` literals without independent derivation.
"""

from __future__ import annotations

import pytest

# NIST Chemistry WebBook, O2, triple point / boiling-related density scale.
# LOX normal boiling point density commonly cited ≈ 1141 kg/m³ at 1 atm.
LOX_NBP_DENSITY_KG_M3 = 1141.0
LOX_NBP_TOLERANCE = 0.02

# NIST Chemistry WebBook, H2, normal boiling point liquid density ≈ 70.8 kg/m³.
LH2_NBP_DENSITY_KG_M3 = 70.8
LH2_NBP_TOLERANCE = 0.03

# IAPWS / NIST water density at 300 K, ~997 kg/m³ (liquid, 1 atm scale).
WATER_300K_DENSITY_KG_M3 = 997.0
WATER_300K_TOLERANCE = 0.01


def test_lox_nbp_density_independent_band() -> None:
    from physics.fluids.lox import NBP_DENSITY

    evaluated = NBP_DENSITY.value
    rel = abs(evaluated - LOX_NBP_DENSITY_KG_M3) / LOX_NBP_DENSITY_KG_M3
    assert rel <= LOX_NBP_TOLERANCE


def test_lh2_nbp_density_independent_band() -> None:
    from physics.fluids.hydrogen import NBP_DENSITY

    evaluated = NBP_DENSITY.value
    rel = abs(evaluated - LH2_NBP_DENSITY_KG_M3) / LH2_NBP_DENSITY_KG_M3
    assert rel <= LH2_NBP_TOLERANCE


def test_water_300k_density_independent_band() -> None:
    from physics.fluids.water import DENSITY_300K

    evaluated = DENSITY_300K.value
    rel = abs(evaluated - WATER_300K_DENSITY_KG_M3) / WATER_300K_DENSITY_KG_M3
    assert rel <= WATER_300K_TOLERANCE
