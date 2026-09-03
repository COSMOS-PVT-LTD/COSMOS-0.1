"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.reactions
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Reaction stoichiometry and elemental conservation checks.
"""

from __future__ import annotations

from dataclasses import dataclass

from physics.exceptions import InvalidCompositionError
from physics.thermochemistry.species import get_species

__all__ = ("Reaction", "check_elemental_balance")

_BALANCE_TOLERANCE = 1.0e-12


@dataclass(frozen=True, slots=True)
class Reaction:
    """
    Irreversible or reversible stoichiometric reaction.

    Coefficients are molar. Positive = product, negative = reactant,
    as in ``nu`` vectors. Convenience constructor uses two maps.
    """

    reaction_id: str
    reactants: dict[str, float]
    products: dict[str, float]
    reversible: bool = True
    source: str = ""


def check_elemental_balance(reaction: Reaction) -> None:
    """
    Reject reactions that do not conserve elements.

    Raises
    ------
    InvalidCompositionError
    """

    counts: dict[str, float] = {}
    for name, coeff in reaction.reactants.items():
        if coeff <= 0.0:
            raise InvalidCompositionError(
                f"Reactant coefficient for {name} must be positive."
            )
        spec = get_species(name)
        for element, number in spec.elements.items():
            counts[element] = counts.get(element, 0.0) - coeff * float(number)
    for name, coeff in reaction.products.items():
        if coeff <= 0.0:
            raise InvalidCompositionError(
                f"Product coefficient for {name} must be positive."
            )
        spec = get_species(name)
        for element, number in spec.elements.items():
            counts[element] = counts.get(element, 0.0) + coeff * float(number)
    unbalanced = {
        element: value
        for element, value in counts.items()
        if abs(value) > _BALANCE_TOLERANCE
    }
    if unbalanced:
        raise InvalidCompositionError(
            f"Reaction {reaction.reaction_id} does not conserve elements: "
            f"{unbalanced}."
        )
