"""Pinned NASA HP chamber with explicitly supplied additional reactant enthalpy.

The existing RocketSolver/adiabatic nozzle is deliberately not reused as a
heat-losing nozzle. Liquid sensible/pressure enthalpy comes from the declared
separate liquid model; never extrapolate database reference temperatures.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np

from core.dimension import PRESSURE
from core.quantity import Quantity
from physics.exceptions import (
    InsufficientDataError,
    OutOfRangeError,
    ThermochemistryError,
)
from physics.quantities import as_si
from physics.si import SPECIFIC_ENERGY
from plugins.nasa_cea.engine import _NATIVE_LOCK, SUPPORTED_VERSION
from plugins.nasa_cea.species_map import to_cea_species


@dataclass(frozen=True)
class ChamberState:
    temperature_k: float
    cp_j_kg_k: float
    gas_constant_j_kg_k: float
    viscosity_pa_s: float
    conductivity_w_m_k: float
    reference_enthalpy_j_kg: float
    product_enthalpy_j_kg: float
    enthalpy_residual_j_kg: float
    provenance: dict[str, Any]


class NasaHPChamber:
    def __init__(self, fuel_id: str, oxidizer_id: str, fuel_reference_k: float, oxidizer_reference_k: float):
        try:
            cea = import_module("cea")
        except (ImportError, OSError) as error:
            raise InsufficientDataError("Pinned cea==3.3.4 is required; no assumed-state fallback.") from error
        if cea.__version__ != SUPPORTED_VERSION or cea.__file__ is None:
            raise InsufficientDataError("Require pinned NASA CEA3.3.4 and its package data.")
        self.cea = cea
        names = [to_cea_species(fuel_id), to_cea_species(oxidizer_id)]
        temperatures = [fuel_reference_k, oxidizer_reference_k]
        with _NATIVE_LOCK:
            for name, temperature in zip(names, temperatures, strict=True):
                low, high = cea.Reactant(name).get_valid_temperature_range()
                if type(temperature) not in {int, float} or not math.isfinite(temperature) or not low <= temperature <= high:
                    raise OutOfRangeError(f"Reference {name} temperature outside NASA database range; no extrapolation.")
            self.reactants = cea.Mixture(names)
            products = cea.Mixture(names, products_from_reactants=True)
            self.solver = cea.EqSolver(products, reactants=self.reactants, transport=True)
        self.temperatures = np.array(temperatures)
        self.provenance = {
            "engine": "NASA_CEA_HP", "version": cea.__version__,
            "source": "https://github.com/nasa/cea/tree/v3.3.4",
            "species": names, "reference_temperatures_k": temperatures,
            "database_sha256": {
                name: hashlib.sha256((Path(cea.__file__).parent / "data" / name).read_bytes()).hexdigest()
                for name in ("thermo.lib", "trans.lib")
            },
            "nozzle_model": "Separate frozen nonadiabatic quasi-1D model, not CEA RocketSolver",
        }

    def solve(self, pressure: Quantity, mixture_ratio: float, added_enthalpy: Quantity) -> ChamberState:
        pc = as_si(pressure, PRESSURE, "Pc")
        delta = as_si(added_enthalpy, SPECIFIC_ENERGY, "additional reactant enthalpy")
        if type(mixture_ratio) not in {float, int} or not all(math.isfinite(v) for v in (pc, mixture_ratio, delta)) or pc <= 0 or mixture_ratio <= 0:
            raise ThermochemistryError("Require positive pressure/O:F and finite added specific enthalpy.")
        if pc > 1e10 or abs(delta) > 1e8 or not 1e-4 <= mixture_ratio <= 1e4:
            raise OutOfRangeError("NASA HP adapter numerical safety envelope exceeded (not a physical validity guarantee).")
        cea = self.cea
        with _NATIVE_LOCK:
            try:
                weights = self.reactants.of_ratio_to_weights(np.array([0., 1.]), np.array([1., 0.]), mixture_ratio)
                reference = float(self.reactants.calc_property(cea.ENTHALPY, weights, self.temperatures))
                solution = cea.EqSolution(self.solver)
                self.solver.solve(solution, cea.HP, (reference + delta) / cea.R, pc / 1e5, weights)
                if not solution.converged:
                    raise ThermochemistryError("NASA HP did not converge; no nozzle state published.")
                if not math.isclose(float(solution.M), float(solution.MW), rel_tol=1e-7):
                    raise OutOfRangeError("Condensed products are unsupported by the frozen gas nozzle.")
                cp = float(solution.cp_fr) * 1000
                gas_constant = float(cea.R) / float(solution.MW)
                values = [float(solution.T), cp, gas_constant, float(solution.viscosity) * 1e-4, float(solution.conductivity_fr) * .1]
                if not all(math.isfinite(v) and v > 0 for v in values) or cp <= gas_constant:
                    raise ThermochemistryError("Invalid frozen gas/transport properties from NASA HP.")
                product_h = float(solution.enthalpy) * 1000
                return ChamberState(values[0], values[1], values[2], values[3], values[4], reference, product_h, product_h - reference - delta, {
                    **self.provenance,
                    "mole_fractions": {str(k): float(v) for k, v in solution.mole_fractions.items() if v != 0},
                    "added_reactant_enthalpy_j_kg": delta,
                    "frozen_gamma": cp / (cp - gas_constant),
                    "equilibrium_gamma_not_used_for_nozzle": float(solution.gamma_s),
                })
            except (ThermochemistryError, OutOfRangeError):
                raise
            except Exception as error:
                raise ThermochemistryError(f"NASA HP failed: {error}") from error
