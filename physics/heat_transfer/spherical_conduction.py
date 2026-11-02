"""Isolated steady conduction benchmark, not a rocket cooling design model."""
from __future__ import annotations

from numerics.utilities.numerical_checks import finite, invalid, positive


def reference_temperature(radius_m: float, position_m: float, conductivity_w_m_k: float,
                          generation_w_m3: float, surface_k: float) -> float:
    """Independent solution: T=Ts+q(R²-r²)/(6k); regular center, fixed Ts.

    Substitution into -k/r² d/dr(r² dT/dr)=q establishes the reference.
    Constant positive k/q, isotropic solid, spherical symmetry only. No data
    from a numerical run enters this expression. See P09 BENCHMARK.md.
    """
    radius, position, k, q, surface = positive(radius_m), finite(position_m), positive(conductivity_w_m_k), positive(generation_w_m3), positive(surface_k)
    if not 0 <= position <= radius:
        invalid("Reference position must be inside the spherical solid.")
    return surface + q * (radius**2 - position**2) / (6 * k)
