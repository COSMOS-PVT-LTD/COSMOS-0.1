"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.transport_properties
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Wilke mixture viscosity from sourced species viscosities.

Description:
    Wilke mixing rule (Wilke, 1950):

        μ_mix = Σ_i  x_i μ_i / Σ_j  x_j Φ_ij

        Φ_ij = (1/sqrt(8)) (1 + M_i/M_j)^(-1/2)
                * (1 + (μ_i/μ_j)^(1/2) * (M_j/M_i)^(1/4))^2

    Thermal conductivity mixing without sourced species k_i is not invented.

Sources
-------
    Wilke, C. R., "A Viscosity Equation for Gas Mixtures,"
    Journal of Chemical Physics, 18, 517 (1950).
"""

from __future__ import annotations

import math

from core.exceptions import InvalidInputError
from core.quantity import Quantity

from physics.exceptions import InsufficientDataError
from physics.model import ModelIdentity
from physics.quantities import quantity
from physics.si import UNIT_DYNAMIC_VISCOSITY
from physics.thermochemistry.mixtures import Mixture

__all__ = ("WILKE", "wilke_mixture_viscosity")

WILKE = ModelIdentity(
    model_id="PHYS-003.transport.wilke_viscosity",
    model_name="Wilke mixture viscosity",
    physical_domain="thermochemistry",
    equations=(
        "mu_mix = sum_i x_i mu_i / sum_j x_j Phi_ij",
        "Phi_ij = (1/sqrt(8)) * (1+Mi/Mj)^(-1/2) * (1 + (mui/muj)^(1/2)*(Mj/Mi)^(1/4))^2",
    ),
    inputs=("mole fractions", "species viscosities [Pa s]", "molar masses [kg/mol]"),
    outputs=("mu_mix [Pa s]",),
    assumptions=("Ideal mixing of dilute gases; Newtonian species viscosities.",),
    validity_range="x_i >= 0, sum x_i = 1; mu_i > 0",
    source="Wilke, J. Chem. Phys. 18, 517 (1950).",
    verification_status="analytical_verification: single-species μ_mix = μ_i",
    limitations=(
        "Not a high-pressure dense-gas mixing rule.",
        "Thermal conductivity mixing is OPEN SCIENTIFIC ISSUE without sourced k_i.",
    ),
)


def wilke_mixture_viscosity(
    mixture: Mixture,
    species_viscosity: dict[str, Quantity],
) -> Quantity:
    """Return mixture dynamic viscosity from Wilke's rule."""

    viscosities: dict[str, float] = {}
    for spec in mixture.species:
        if spec.species_id not in species_viscosity:
            raise InsufficientDataError(
                f"Missing viscosity for species {spec.species_id}."
            )
        mu = species_viscosity[spec.species_id].to_si()
        if mu <= 0.0:
            raise InvalidInputError(
                f"viscosity for {spec.species_id} must be positive."
            )
        viscosities[spec.species_id] = mu

    mix = 0.0
    for spec_i in mixture.species:
        xi = mixture.mole_fractions[spec_i.species_id]
        mi = spec_i.molar_mass.to_si()
        mui = viscosities[spec_i.species_id]
        denom = 0.0
        for spec_j in mixture.species:
            xj = mixture.mole_fractions[spec_j.species_id]
            mj = spec_j.molar_mass.to_si()
            muj = viscosities[spec_j.species_id]
            phi = (
                (1.0 / math.sqrt(8.0))
                * (1.0 + mi / mj) ** -0.5
                * (1.0 + math.sqrt(mui / muj) * (mj / mi) ** 0.25) ** 2
            )
            denom += xj * phi
        mix += xi * mui / denom
    return quantity(mix, UNIT_DYNAMIC_VISCOSITY)
