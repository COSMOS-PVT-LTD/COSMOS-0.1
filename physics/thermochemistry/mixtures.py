"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.mixtures
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Mixture composition, normalization policy, and mean molar mass.

Description:
    Invalid compositions are rejected. Silent normalization is forbidden
    unless ``normalize=True`` is passed and the transformation is reported.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.exceptions import InvalidInputError
from core.quantity import Quantity

from physics.exceptions import InvalidCompositionError
from physics.quantities import quantity
from physics.si import UNIT_MOLAR_MASS
from physics.thermochemistry.species import Species, get_species

__all__ = (
    "Mixture",
    "from_mass_fractions",
    "from_mole_fractions",
    "elemental_moles",
)

_FRACTION_TOLERANCE = 1.0e-9


def _validate_fraction_map(values: dict[str, float], name: str) -> dict[str, float]:
    if not values:
        raise InvalidCompositionError(f"{name} is empty.")
    cleaned: dict[str, float] = {}
    for key, raw in values.items():
        if not isinstance(raw, (int, float)) or isinstance(raw, bool):
            raise InvalidInputError(f"{name}[{key!r}] must be a real number.")
        value = float(raw)
        if value < 0.0:
            raise InvalidCompositionError(
                f"{name}[{key!r}] is negative ({value})."
            )
        if value > 0.0:
            cleaned[key.strip().upper()] = value
    if not cleaned:
        raise InvalidCompositionError(f"{name} contains only zeros.")
    return cleaned


def _maybe_normalize(
    values: dict[str, float],
    *,
    normalize: bool,
    name: str,
) -> tuple[dict[str, float], bool]:
    total = sum(values.values())
    if abs(total - 1.0) <= _FRACTION_TOLERANCE:
        return values, False
    if not normalize:
        raise InvalidCompositionError(
            f"{name} must sum to 1. Received {total}."
        )
    return {key: value / total for key, value in values.items()}, True


@dataclass(frozen=True, slots=True)
class Mixture:
    """Gas mixture defined by mole fractions (canonical)."""

    mole_fractions: dict[str, float]
    mass_fractions: dict[str, float]
    mean_molar_mass: Quantity
    species: tuple[Species, ...]
    was_normalized: bool

    def mole_fraction(self, species_id: str) -> float:
        """Return the mole fraction of ``species_id`` (zero if absent)."""

        return self.mole_fractions.get(species_id.strip().upper(), 0.0)


def from_mole_fractions(
    mole_fractions: dict[str, float],
    *,
    normalize: bool = False,
) -> Mixture:
    """Construct a mixture from mole fractions."""

    cleaned = _validate_fraction_map(mole_fractions, "mole_fractions")
    fractions, was_normalized = _maybe_normalize(
        cleaned,
        normalize=normalize,
        name="mole_fractions",
    )
    species = tuple(get_species(name) for name in sorted(fractions))
    mean_m = 0.0
    mass_raw: dict[str, float] = {}
    for spec in species:
        x = fractions[spec.species_id]
        m = spec.molar_mass.to_si()
        mean_m += x * m
        mass_raw[spec.species_id] = x * m
    mass_fractions = {key: value / mean_m for key, value in mass_raw.items()}
    return Mixture(
        mole_fractions=fractions,
        mass_fractions=mass_fractions,
        mean_molar_mass=quantity(mean_m, UNIT_MOLAR_MASS),
        species=species,
        was_normalized=was_normalized,
    )


def from_mass_fractions(
    mass_fractions: dict[str, float],
    *,
    normalize: bool = False,
) -> Mixture:
    """Construct a mixture from mass fractions."""

    cleaned = _validate_fraction_map(mass_fractions, "mass_fractions")
    fractions, was_normalized = _maybe_normalize(
        cleaned,
        normalize=normalize,
        name="mass_fractions",
    )
    species = tuple(get_species(name) for name in sorted(fractions))
    moles_raw: dict[str, float] = {}
    for spec in species:
        y = fractions[spec.species_id]
        moles_raw[spec.species_id] = y / spec.molar_mass.to_si()
    total_moles = sum(moles_raw.values())
    mole_fractions = {key: value / total_moles for key, value in moles_raw.items()}
    mean_m = 1.0 / total_moles
    return Mixture(
        mole_fractions=mole_fractions,
        mass_fractions=fractions,
        mean_molar_mass=quantity(mean_m, UNIT_MOLAR_MASS),
        species=species,
        was_normalized=was_normalized,
    )


def elemental_moles(mixture: Mixture, mixture_moles: float = 1.0) -> dict[str, float]:
    """Return elemental mole counts for ``mixture_moles`` moles of mixture."""

    if mixture_moles <= 0.0:
        raise InvalidInputError("mixture_moles must be positive.")
    counts: dict[str, float] = {}
    for spec in mixture.species:
        x = mixture.mole_fractions[spec.species_id]
        for element, number in spec.elements.items():
            counts[element] = counts.get(element, 0.0) + mixture_moles * x * float(number)
    return counts
