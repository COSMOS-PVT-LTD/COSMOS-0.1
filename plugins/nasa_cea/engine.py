"""
NASA CEA ThermochemistryEngine adapter (PyPI package ``cea`` ≥ 3.3).

Lives outside ``physics/``. COSMOS physics owns the SI contract via
``cea_interface``; this module only implements ``ThermochemistryEngine``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import InsufficientDataError, ThermochemistryError
from physics.quantities import kelvin, quantity
from physics.thermochemistry.cea_interface import CeaRequest, ThermochemicalResult
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol
from physics.validity import ValidityStatus
from plugins.nasa_cea.species_map import reactant_temperature_k, to_cea_species

__all__ = ("NasaCeaEngine", "bind_nasa_cea_engine")

ENGINE_NAME = "nasa/cea"


def _velocity_mps(value: float) -> Quantity:
    return quantity(float(value), SI.get("m/s"))


def _pressure_bar(chamber_pressure: Quantity) -> float:
    pa = float(chamber_pressure.to_si())
    if pa <= 0.0:
        raise ThermochemistryError("Chamber pressure must be positive.")
    return pa / 1.0e5


def _chamber_mole_fractions(solution, index: int = 0) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, series in solution.mole_fractions.items():
        value = float(series[index])
        if value > 0.0:
            out[str(name)] = value
    return out


@dataclass(slots=True)
class NasaCeaEngine:
    """
    Bind the modern NASA CEA Python package as a COSMOS thermochemistry engine.

    Parameters
    ----------
    fuel_temperature_k, oxidizer_temperature_k:
        Optional reactant temperatures for chamber enthalpy. Defaults follow
        cryogenic NBP-style values for ``*(L)`` species (see species_map).
    exit_pressure_pa:
        Used only to form a single ``Pc/Pe`` station so the rocket solve has a
        nozzle path; chamber properties are always taken from station 0.
    """

    fuel_temperature_k: float | None = None
    oxidizer_temperature_k: float | None = None
    exit_pressure_pa: float = 101325.0

    def evaluate(self, request: CeaRequest) -> ThermochemicalResult:
        try:
            import cea
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise InsufficientDataError(
                "Package 'cea' is not installed. Install with: "
                "pip install -r requirements-cea.txt"
            ) from exc

        fuel = to_cea_species(request.fuel_id)
        oxidizer = to_cea_species(request.oxidizer_id)
        if request.mixture_ratio <= 0.0:
            raise ThermochemistryError("mixture_ratio (O/F by mass) must be positive.")

        pc_bar = _pressure_bar(request.chamber_pressure)
        pe_bar = max(float(self.exit_pressure_pa) / 1.0e5, 1.0e-6)
        pi_p = [pc_bar / pe_bar]

        t_fuel = reactant_temperature_k(fuel, self.fuel_temperature_k)
        t_ox = reactant_temperature_k(oxidizer, self.oxidizer_temperature_k)

        reac_names = [fuel, oxidizer]
        t_reactant = np.array([t_fuel, t_ox], dtype=float)
        fuel_weights = np.array([1.0, 0.0], dtype=float)
        oxidant_weights = np.array([0.0, 1.0], dtype=float)

        try:
            reac = cea.Mixture(reac_names)
            prod = cea.Mixture(reac_names, products_from_reactants=True)
            solver = cea.RocketSolver(prod, reactants=reac)
            solution = cea.RocketSolution(solver)
            weights = reac.of_ratio_to_weights(
                oxidant_weights, fuel_weights, float(request.mixture_ratio)
            )
            hc = reac.calc_property(cea.ENTHALPY, weights, t_reactant) / cea.R
            n_frz = None if request.equilibrium else 1
            solver.solve(
                solution,
                weights,
                pc_bar,
                pi_p,
                iac=True,
                hc=hc,
                n_frz=n_frz,
            )
        except Exception as exc:
            raise ThermochemistryError(
                f"nasa/cea failed for {fuel}/{oxidizer} at O/F="
                f"{request.mixture_ratio}: {exc}"
            ) from exc

        if solution.num_pts < 1:
            raise ThermochemistryError("nasa/cea returned no solution stations.")

        tc = float(solution.T[0])
        gamma = float(solution.gamma_s[0])
        mw_g_per_mol = float(solution.MW[0])
        cstar = float(solution.c_star[0])
        mole_fractions = _chamber_mole_fractions(solution, 0)

        if not np.isfinite(tc) or tc <= 0.0:
            raise ThermochemistryError("nasa/cea returned invalid chamber temperature.")
        if not np.isfinite(gamma):
            raise ThermochemistryError("nasa/cea returned invalid gamma.")
        if not np.isfinite(mw_g_per_mol) or mw_g_per_mol <= 0.0:
            raise ThermochemistryError("nasa/cea returned invalid molar mass.")

        return ThermochemicalResult(
            chamber_temperature=kelvin(tc),
            gamma=gamma,
            molar_mass=molar_mass_from_kg_per_kmol(mw_g_per_mol),
            characteristic_velocity=_velocity_mps(cstar),
            mole_fractions=mole_fractions,
            validity=ValidityStatus.VALID,
            engine_name=ENGINE_NAME,
        )


def bind_nasa_cea_engine(**kwargs) -> NasaCeaEngine:
    """Factory used by systems / scripts / GUI wiring."""

    return NasaCeaEngine(**kwargs)
