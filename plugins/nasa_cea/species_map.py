"""Map COSMOS propellant IDs / aliases to NASA CEA species names."""

from __future__ import annotations

from typing import Final

# Canonical CEA library names used by nasa/cea Mixture.
_ALIASES: Final[dict[str, str]] = {
    # Methane
    "ch4": "CH4(L)",
    "ch4(l)": "CH4(L)",
    "ch4(g)": "CH4",
    "lch4": "CH4(L)",
    "methane": "CH4(L)",
    "liquid methane": "CH4(L)",
    # Oxygen
    "o2": "O2(L)",
    "o2(l)": "O2(L)",
    "o2(g)": "O2",
    "lox": "O2(L)",
    "oxygen": "O2(L)",
    "liquid oxygen": "O2(L)",
    # Hydrogen
    "h2": "H2(L)",
    "h2(l)": "H2(L)",
    "h2(g)": "H2",
    "lh2": "H2(L)",
    "hydrogen": "H2(L)",
    # Hydrocarbons
    "rp-1": "RP-1",
    "rp1": "RP-1",
    "kerosene": "RP-1",
    # Common storable (optional)
    "n2o4": "N2O4(L)",
    "mmh": "CH6N2(L)",
    "udmh": "C2H8N2(L)",
}

# Default cryogenic / ambient reactant temperatures [K] for enthalpy.
DEFAULT_REACTANT_TEMPERATURE_K: Final[dict[str, float]] = {
    "CH4(L)": 111.67,
    "CH4": 298.15,
    "O2(L)": 90.17,
    "O2": 298.15,
    "H2(L)": 20.27,
    "H2": 298.15,
    "RP-1": 298.15,
    "N2O4(L)": 298.15,
    "CH6N2(L)": 298.15,
    "C2H8N2(L)": 298.15,
}


def normalize_key(name: str) -> str:
    return " ".join(name.strip().lower().split())


def to_cea_species(name: str) -> str:
    """
    Resolve a COSMOS fuel/oxidizer id to a CEA species string.

    Accepts already-canonical CEA names (including parentheses) unchanged
    when they are not in the alias table under a different form.
    """

    raw = name.strip()
    if not raw:
        raise ValueError("Species name must be non-empty.")
    key = normalize_key(raw)
    if key in _ALIASES:
        return _ALIASES[key]
    # Preserve intentional CEA spellings such as CH4(L).
    return raw


def reactant_temperature_k(cea_species: str, override: float | None = None) -> float:
    if override is not None:
        return float(override)
    return float(DEFAULT_REACTANT_TEMPERATURE_K.get(cea_species, 298.15))
