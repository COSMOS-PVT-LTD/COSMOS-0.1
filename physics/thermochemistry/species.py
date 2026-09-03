"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.species
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Species identity, composition, molar mass, and NASA7 registry.

Authority
---------
``physics.thermochemistry.species`` is the **authoritative computational**
thermochemistry registry for NASA7 species data used by new physics code.

``physics.thermochemistry.propellants`` is a legacy compatibility layer for
propellant database records and CEA naming — not a competing solver API.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import UNIVERSAL_GAS_CONSTANT
from core.exceptions import InvalidInputError
from core.quantity import Quantity

from physics.exceptions import InvalidCompositionError, ThermochemistryError
from physics.quantities import quantity
from physics.si import UNIT_MOLAR_MASS
from physics.thermochemistry.nasa_polynomials import NASA7

__all__ = (
    "ATOMIC_MASS_KG_PER_MOL",
    "Species",
    "get_species",
    "list_species",
    "molar_mass_from_elements",
)

# IUPAC/NIST standard atomic weights (kg/mol), truncated to engineering use.
ATOMIC_MASS_KG_PER_MOL: dict[str, float] = {
    "H": 1.00794e-3,
    "C": 12.0107e-3,
    "N": 14.0067e-3,
    "O": 15.9994e-3,
    "AR": 39.948e-3,
    "HE": 4.002602e-3,
    "AL": 26.981538e-3,
    "CL": 35.453e-3,
    "F": 18.998403e-3,
}


def molar_mass_from_elements(elements: dict[str, int]) -> Quantity:
    """Return molar mass from integer elemental composition."""

    if not elements:
        raise InvalidCompositionError("Elemental composition is empty.")
    mass = 0.0
    for symbol, count in elements.items():
        key = symbol.upper()
        if key not in ATOMIC_MASS_KG_PER_MOL:
            raise InvalidCompositionError(f"Unknown element symbol: {symbol!r}.")
        if count <= 0:
            raise InvalidCompositionError(
                f"Element count for {symbol} must be a positive integer."
            )
        mass += ATOMIC_MASS_KG_PER_MOL[key] * float(count)
    return quantity(mass, UNIT_MOLAR_MASS)


@dataclass(frozen=True, slots=True)
class Species:
    """Gas-phase species with sourced NASA7 coefficients."""

    species_id: str
    formula: str
    elements: dict[str, int]
    molar_mass: Quantity
    polynomial: NASA7
    phase: str = "G"

    def __post_init__(self) -> None:
        computed = molar_mass_from_elements(self.elements)
        relative = abs(computed.to_si() - self.molar_mass.to_si()) / computed.to_si()
        if relative > 1.0e-3:
            raise InvalidCompositionError(
                f"{self.species_id} molar mass is inconsistent with elements "
                f"(relative error {relative:.3e})."
            )


def _nasa7(
    species_id: str,
    t_min: float,
    t_mid: float,
    t_max: float,
    low: tuple[float, float, float, float, float, float, float],
    high: tuple[float, float, float, float, float, float, float],
    source: str,
) -> NASA7:
    return NASA7(
        species_id=species_id,
        t_min_k=t_min,
        t_mid_k=t_mid,
        t_max_k=t_max,
        low=low,
        high=high,
        source=source,
    )


_GRI = (
    "GRI-Mech 3.0 thermodynamic database (Smith, Golden, Frenklach et al.), "
    "NASA 7-coefficient Chemkin format."
)

# GRI-Mech 3.0 NASA7: high-T first in the file, stored here as high= / low=.
_REGISTRY: dict[str, Species] = {}


def _register(species: Species) -> None:
    _REGISTRY[species.species_id] = species


def _species(
    species_id: str,
    formula: str,
    elements: dict[str, int],
    polynomial: NASA7,
) -> Species:
    species = Species(
        species_id=species_id,
        formula=formula,
        elements=elements,
        molar_mass=molar_mass_from_elements(elements),
        polynomial=polynomial,
    )
    _register(species)
    return species


_species(
    "N2",
    "N2",
    {"N": 2},
    _nasa7(
        "N2",
        300.0,
        1000.0,
        5000.0,
        (
            3.298677e00,
            1.4082404e-03,
            -3.963222e-06,
            5.641515e-09,
            -2.444854e-12,
            -1.0208999e03,
            3.950372e00,
        ),
        (
            2.926640e00,
            1.4879768e-03,
            -5.684760e-07,
            1.0097038e-10,
            -6.753351e-15,
            -9.227977e02,
            5.980528e00,
        ),
        _GRI,
    ),
)
_species(
    "O2",
    "O2",
    {"O": 2},
    _nasa7(
        "O2",
        200.0,
        1000.0,
        3500.0,
        (
            3.78245636e00,
            -2.99673416e-03,
            9.84730201e-06,
            -9.68129509e-09,
            3.24372837e-12,
            -1.06394356e03,
            3.65767573e00,
        ),
        (
            3.28253784e00,
            1.48308754e-03,
            -7.57966669e-07,
            2.09470555e-10,
            -2.16717794e-14,
            -1.08845772e03,
            5.45323129e00,
        ),
        _GRI,
    ),
)
_species(
    "H2",
    "H2",
    {"H": 2},
    _nasa7(
        "H2",
        200.0,
        1000.0,
        3500.0,
        (
            2.34433112e00,
            7.98052075e-03,
            -1.94781510e-05,
            2.01572094e-08,
            -7.37611761e-12,
            -9.17935173e02,
            6.83010238e-01,
        ),
        (
            3.33727920e00,
            -4.94024731e-05,
            4.99456778e-07,
            -1.79566394e-10,
            2.00255376e-14,
            -9.50158922e02,
            -3.20502331e00,
        ),
        _GRI,
    ),
)
_species(
    "H2O",
    "H2O",
    {"H": 2, "O": 1},
    _nasa7(
        "H2O",
        200.0,
        1000.0,
        3500.0,
        (
            4.19864056e00,
            -2.03643410e-03,
            6.52040211e-06,
            -5.48797062e-09,
            1.77197817e-12,
            -3.02937267e04,
            -8.49032208e-01,
        ),
        (
            3.03399249e00,
            2.17691804e-03,
            -1.64072518e-07,
            -9.70419870e-11,
            1.68200992e-14,
            -3.00042971e04,
            4.96677010e00,
        ),
        _GRI,
    ),
)
_species(
    "CO2",
    "CO2",
    {"C": 1, "O": 2},
    _nasa7(
        "CO2",
        200.0,
        1000.0,
        3500.0,
        (
            2.35677352e00,
            8.98459677e-03,
            -7.12356269e-06,
            2.45919022e-09,
            -1.43699548e-13,
            -4.83719697e04,
            9.90105222e00,
        ),
        (
            3.85746029e00,
            4.41437026e-03,
            -2.21481404e-06,
            5.23490188e-10,
            -4.72084164e-14,
            -4.87591660e04,
            2.27163806e00,
        ),
        _GRI,
    ),
)
_species(
    "CO",
    "CO",
    {"C": 1, "O": 1},
    _nasa7(
        "CO",
        200.0,
        1000.0,
        3500.0,
        (
            3.57953347e00,
            -6.10353680e-04,
            1.01681433e-06,
            9.07005884e-10,
            -9.04424499e-13,
            -1.43440860e04,
            3.50840928e00,
        ),
        (
            2.71518561e00,
            2.06252743e-03,
            -9.98825771e-07,
            2.30053008e-10,
            -2.03647716e-14,
            -1.41518724e04,
            7.81868772e00,
        ),
        _GRI,
    ),
)
_species(
    "CH4",
    "CH4",
    {"C": 1, "H": 4},
    _nasa7(
        "CH4",
        200.0,
        1000.0,
        3500.0,
        (
            5.14987613e00,
            -1.36709788e-02,
            4.91800599e-05,
            -4.84743026e-08,
            1.66693956e-11,
            -1.02466476e04,
            -4.64130376e00,
        ),
        (
            7.48514950e-02,
            1.33909467e-02,
            -5.73285809e-06,
            1.22292535e-09,
            -1.01815230e-13,
            -9.46834459e03,
            1.84373180e01,
        ),
        _GRI,
    ),
)
_species(
    "AR",
    "Ar",
    {"AR": 1},
    _nasa7(
        "AR",
        300.0,
        1000.0,
        5000.0,
        (2.5, 0.0, 0.0, 0.0, 0.0, -745.375, 4.366),
        (2.5, 0.0, 0.0, 0.0, 0.0, -745.375, 4.366),
        _GRI,
    ),
)
_species(
    "OH",
    "OH",
    {"O": 1, "H": 1},
    _nasa7(
        "OH",
        200.0,
        1000.0,
        3500.0,
        (
            3.99201543e00,
            -2.40131752e-03,
            4.61793841e-06,
            -3.88113333e-09,
            1.36411470e-12,
            3.61508056e03,
            -1.03925458e-01,
        ),
        (
            3.09288767e00,
            5.48429716e-04,
            1.26505228e-07,
            -8.79461556e-11,
            1.17412376e-14,
            3.85865700e03,
            4.47669610e00,
        ),
        _GRI,
    ),
)
_species(
    "H",
    "H",
    {"H": 1},
    _nasa7(
        "H",
        200.0,
        1000.0,
        3500.0,
        (
            2.5,
            7.05332819e-13,
            -1.99591964e-15,
            2.30081632e-18,
            -9.27732332e-22,
            2.54736599e04,
            -4.46682853e-01,
        ),
        (
            2.50000001e00,
            -2.30842973e-11,
            1.61561948e-14,
            -4.73515235e-18,
            4.98197357e-22,
            2.54736599e04,
            -4.46682914e-01,
        ),
        _GRI,
    ),
)
_species(
    "O",
    "O",
    {"O": 1},
    _nasa7(
        "O",
        200.0,
        1000.0,
        3500.0,
        (
            3.16826710e00,
            -3.27931884e-03,
            6.64306396e-06,
            -6.12806624e-09,
            2.11265971e-12,
            2.91222592e04,
            2.05193346e00,
        ),
        (
            2.56942078e00,
            -8.59741137e-05,
            4.19484589e-08,
            -1.00177799e-11,
            1.22833691e-15,
            2.92175791e04,
            4.78433864e00,
        ),
        _GRI,
    ),
)

# Monatomic helium: Cp/R = 5/2 exactly. a6=a7 chosen so H(298) and S are
# not claimed as a full CEA match — enthalpy datum is kinetic-theory only.
_species(
    "HE",
    "He",
    {"HE": 1},
    _nasa7(
        "HE",
        200.0,
        1000.0,
        5000.0,
        (2.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (2.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        "Monatomic kinetic theory Cp/R = 5/2. Absolute H and S datum not sourced.",
    ),
)


def get_species(species_id: str) -> Species:
    """Return a registered species (case-insensitive)."""

    key = species_id.strip().upper()
    try:
        return _REGISTRY[key]
    except KeyError as exc:
        raise ThermochemistryError(f"Unknown species: {species_id!r}.") from exc


def list_species() -> tuple[str, ...]:
    """Return registered species identifiers in sorted order."""

    return tuple(sorted(_REGISTRY))


def molar_gas_constant() -> float:
    """Universal gas constant [J/(mol K)]."""

    if UNIVERSAL_GAS_CONSTANT <= 0.0:
        raise InvalidInputError("universal gas constant is invalid.")
    return UNIVERSAL_GAS_CONSTANT
