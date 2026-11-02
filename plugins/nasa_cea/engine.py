"""
NASA CEA ThermochemistryEngine adapter (PyPI package ``cea`` ≥ 3.3).

Lives outside ``physics/``. COSMOS physics owns the SI contract via
``cea_interface``; this module only implements ``ThermochemistryEngine``.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from threading import RLock

import numpy as np

from core.dimension import PRESSURE
from core.quantity import Quantity
from core.unit import SI
from physics.exceptions import (
    InsufficientDataError,
    OutOfRangeError,
    ThermochemistryError,
)
from physics.quantities import as_si, kelvin, quantity
from physics.thermochemistry.cea_interface import CeaRequest, ThermochemicalResult
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol
from physics.validity import ValidityStatus
from plugins.nasa_cea.species_map import reactant_temperature_k, to_cea_species

__all__ = ("NasaCeaEngine", "bind_nasa_cea_engine")

ENGINE_NAME = "nasa/cea"
SUPPORTED_VERSION = "3.3.4"
# The native package has shared database/logging state. Serialize native calls.
_NATIVE_LOCK = RLock()


def _velocity_mps(value: float) -> Quantity:
    return quantity(float(value), SI.get("m/s"))


def _pressure_bar(chamber_pressure: Quantity) -> float:
    pa = as_si(chamber_pressure, PRESSURE, "chamber_pressure")
    if not math.isfinite(pa) or pa <= 0.0:
        raise ThermochemistryError("Chamber pressure must be positive.")
    return pa / 1.0e5


def _chamber_mole_fractions(solution, index: int = 0) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, series in solution.mole_fractions.items():
        value = float(series[index])
        if value != 0.0:
            out[str(name)] = value
    return out


def _check_frozen_reference(reference, solution) -> dict[str, object]:
    """Reject any active-domain adaptation that changes the full frozen solution.

    Only exact zero chamber species may be excluded. Positive trace species are
    retained, with full-domain station composition/performance cross-checks.
    """
    if not reference.converged or reference.num_pts != 3:
        raise ThermochemistryError("Full-product frozen reference did not converge; no fallback is permitted.")
    if not solution.converged or solution.num_pts != 3:
        raise ThermochemistryError("Active-product frozen transport solve did not converge; no fallback is permitted.")
    maximum_relative = 0.0
    for key in ("T", "P", "MW", "gamma_s", "Mach", "Isp", "ae_at", "c_star", "Isp_vacuum"):
        for wanted, actual in zip(getattr(reference, key), getattr(solution, key), strict=True):
            wanted, actual = float(wanted), float(actual)
            if not math.isfinite(wanted) or not math.isfinite(actual) or not math.isclose(wanted, actual, rel_tol=1e-5, abs_tol=1e-7):
                raise ThermochemistryError(f"Frozen transport adaptation changed full-product {key}; result rejected.")
            maximum_relative = max(maximum_relative, abs(actual-wanted)/max(abs(wanted), 1e-7))
    full, active = reference.mole_fractions, solution.mole_fractions
    if set(active) - set(full):
        raise ThermochemistryError("Frozen transport introduced an unreferenced species.")
    if any(float(full[name][0]) == 0 for name in active):
        raise ThermochemistryError("Frozen transport retained an excluded exact-zero species.")
    maximum_fraction_error = 0.0
    for name, wanted in full.items():
        if float(wanted[0]) > 0 and name not in active:
            raise ThermochemistryError("Frozen transport omitted a positive trace species.")
        actual = active.get(name, [0., 0., 0.])
        for i in range(3):
            value, expected = float(actual[i]), float(wanted[i])
            if not all(math.isfinite(x) and x >= 0 for x in (value, expected)):
                raise ThermochemistryError("Frozen transport has an invalid species amount.")
            error = max(abs(value-expected), abs(value-float(actual[0])), abs(expected-float(wanted[0])))
            if error > 1e-10:
                raise ThermochemistryError("Frozen transport changed composition; result rejected.")
            maximum_fraction_error = max(maximum_fraction_error, error)
    for fractions in (full, active):
        if any(not math.isclose(sum(float(values[i]) for values in fractions.values()), 1., abs_tol=5e-9, rel_tol=0) for i in range(3)):
            raise ThermochemistryError("Frozen composition normalization failed.")
    return {"strategy": "EXACT_ZERO_SPECIES_EXCLUDED_WITH_FULL_PRODUCT_REFERENCE",
            "full_product_species_count": len(full), "active_product_species_count": len(active),
            "excluded_exact_zero_species_count": len(full)-len(active),
            "maximum_relative_station_discrepancy": maximum_relative,
            "maximum_absolute_mole_fraction_discrepancy": maximum_fraction_error,
            "reference": "Same pinned full-product frozen-chamber CEA, transport OFF; numerical cross-check only"}


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
    require_explicit_temperatures: bool = False

    def evaluate(self, request: CeaRequest) -> ThermochemicalResult:
        with _NATIVE_LOCK:
            return self._evaluate(request)

    def _evaluate(self, request: CeaRequest) -> ThermochemicalResult:
        if self.require_explicit_temperatures and (self.fuel_temperature_k is None or self.oxidizer_temperature_k is None):
            raise InsufficientDataError("CEA requires explicit fuel and oxidizer inlet temperatures [K].")
        try:
            frozen_reference = None
            frozen_strategy = None
            # v3.3.4 ships malformed .pyi signatures. Keep this optional native
            # dependency dynamic at the adapter boundary, not in typed Physics.
            cea = import_module("cea")
        except (ImportError, OSError) as exc:  # pragma: no cover - environment dependent
            raise InsufficientDataError(
                "Package 'cea' is not installed. Install with: "
                "pip install -r requirements-cea.txt"
            ) from exc
        if cea.__version__ != SUPPORTED_VERSION:
            raise InsufficientDataError(f"COSMOS requires verified cea=={SUPPORTED_VERSION}; found {cea.__version__}.")
        if cea.__file__ is None:
            raise InsufficientDataError("CEA package data location is unavailable.")
        package_dir = Path(cea.__file__).parent

        fuel = to_cea_species(request.fuel_id)
        oxidizer = to_cea_species(request.oxidizer_id)
        if not math.isfinite(request.mixture_ratio) or request.mixture_ratio <= 0.0:
            raise ThermochemistryError("mixture_ratio (O/F by mass) must be positive.")

        pc_bar = _pressure_bar(request.chamber_pressure)
        eps = request.expansion_ratio
        if eps is not None and (not math.isfinite(eps) or eps <= 1):
            raise ThermochemistryError("Supersonic CEA requires Ae/At > 1.")
        if eps is None and (not math.isfinite(self.exit_pressure_pa) or not 0 < self.exit_pressure_pa < pc_bar * 1e5):
            raise ThermochemistryError("Reference exit pressure must be finite and between zero and Pc.")
        pi_p = None if eps is not None else [pc_bar * 1e5 / self.exit_pressure_pa]

        t_fuel = reactant_temperature_k(fuel, self.fuel_temperature_k)
        t_ox = reactant_temperature_k(oxidizer, self.oxidizer_temperature_k)
        if not all(math.isfinite(t) and t > 0 for t in (t_fuel, t_ox)):
            raise ThermochemistryError("Reactant temperatures must be finite and positive.")

        reac_names = [fuel, oxidizer]
        t_reactant = np.array([t_fuel, t_ox], dtype=float)
        fuel_weights = np.array([1.0, 0.0], dtype=float)
        oxidant_weights = np.array([0.0, 1.0], dtype=float)

        try:
            temperature_ranges = {}
            for name, temperature in ((fuel, t_fuel), (oxidizer, t_ox)):
                low, high = cea.Reactant(name).get_valid_temperature_range()
                temperature_ranges[name] = [float(low), float(high)]
                if not low <= temperature <= high:
                    raise OutOfRangeError(f"{name} inlet temperature {temperature} K is outside NASA database range [{low}, {high}] K. Heated/subcooled feed states require qualified enthalpy data.")
            reac = cea.Mixture(reac_names)
            prod = cea.Mixture(reac_names, products_from_reactants=True)
            weights = reac.of_ratio_to_weights(
                oxidant_weights, fuel_weights, float(request.mixture_ratio)
            )
            hc = reac.calc_property(cea.ENTHALPY, weights, t_reactant) / cea.R
            n_frz = None if request.equilibrium else 1
            if not request.equilibrium:
                # Pinned native transport can restore exact-zero species from
                # log amounts: consistent with the reproduced frozen failure.
                # The mechanical cause is an inference, not an upstream fix.
                # Never patch the vendor,
                # accept its partial solve, or substitute equilibrium expansion.
                reference_solver = cea.RocketSolver(prod, reactants=reac, transport=False)
                frozen_reference = cea.RocketSolution(reference_solver)
                reference_solver.solve(frozen_reference, weights, pc_bar, pi_p, iac=True, hc=hc,
                                       n_frz=1, supar=None if eps is None else [eps])
                if not frozen_reference.converged or frozen_reference.num_pts != 3:
                    raise ThermochemistryError("Full-product frozen reference did not converge; no fallback is permitted.")
                active_names = [name for name, series in frozen_reference.mole_fractions.items() if float(series[0]) > 0]
                if not active_names:
                    raise ThermochemistryError("Full-product frozen reference has no positive species.")
                prod = cea.Mixture(active_names)
            solver = cea.RocketSolver(prod, reactants=reac, transport=True)
            solution = cea.RocketSolution(solver)
            solver.solve(
                solution,
                weights,
                pc_bar,
                pi_p,
                iac=True,
                hc=hc,
                n_frz=n_frz,
                supar=None if eps is None else [eps],
            )
        except OutOfRangeError:
            raise
        except Exception as exc:
            raise ThermochemistryError(
                f"nasa/cea failed for {fuel}/{oxidizer} at O/F="
                f"{request.mixture_ratio}: {exc}"
            ) from exc

        if not solution.converged or solution.num_pts != 3:
            raise ThermochemistryError("nasa/cea did not converge to chamber, throat and exit; no fallback is permitted.")
        if frozen_reference is not None:
            frozen_strategy = _check_frozen_reference(frozen_reference, solution)
        if eps is not None and not math.isclose(float(solution.ae_at[2]), eps, rel_tol=5e-4):
            raise ThermochemistryError("CEA exit area ratio did not meet the requested tolerance.")
        stations = {}
        for index, name in enumerate(("chamber", "throat", "exit")):
            stations[name] = {
                "pressure_pa": float(solution.P[index]) * 1e5,
                "temperature_k": float(solution.T[index]),
                "molar_mass_kg_mol": float(solution.MW[index]) / 1000,
                "gamma": float(solution.gamma_s[index]),
                "mach": float(solution.Mach[index]),
                "velocity_m_s": float(solution.Isp[index]),
                "area_ratio": float(solution.ae_at[index]),
                "cp_frozen_j_kg_k": float(solution.cp_fr[index]) * 1000,
                "cp_equilibrium_j_kg_k": float(solution.cp_eq[index]) * 1000,
                "viscosity_pa_s": float(solution.viscosity[index]) * 1e-4,
                # Native v3.3.4 values obey Pr=mu[mP]*cp[kJ/kg/K]/k.
                # Thus k is mW/cm/K (x0.1 SI), despite the API doc's muW typo.
                "conductivity_frozen_w_m_k": float(solution.conductivity_fr[index]) * 0.1,
                "conductivity_equilibrium_w_m_k": float(solution.conductivity_eq[index]) * 0.1,
                "prandtl_frozen": float(solution.Pr_fr[index]),
                "prandtl_equilibrium": float(solution.Pr_eq[index]),
                "vacuum_isp_s": float(solution.Isp_vacuum[index]) / 9.80665,
            }
            row = stations[name]
            if not all(math.isfinite(value) for value in row.values()):
                raise ThermochemistryError(f"CEA returned non-finite {name} data.")
            for key in ("pressure_pa", "temperature_k", "molar_mass_kg_mol", "cp_frozen_j_kg_k", "viscosity_pa_s", "conductivity_frozen_w_m_k"):
                if row[key] <= 0:
                    raise ThermochemistryError(f"CEA returned non-positive {name} {key}.")
            if not math.isclose(row["cp_frozen_j_kg_k"] * row["viscosity_pa_s"] / row["conductivity_frozen_w_m_k"], row["prandtl_frozen"], rel_tol=1e-6):
                raise ThermochemistryError("CEA transport units failed the Prandtl identity check.")
        if stations["exit"]["mach"] <= 1:
            raise ThermochemistryError("CEA exit is not supersonic; unsupported nozzle state.")

        tc = float(solution.T[0])
        gamma = float(solution.gamma_s[0])
        mw_g_per_mol = float(solution.MW[0])
        cstar = float(solution.c_star[0])
        if not math.isfinite(cstar) or cstar <= 0:
            raise ThermochemistryError("CEA returned invalid cstar.")
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
            engine_version=cea.__version__,
            rocket_stations=stations,
            provenance={
                "source": "https://github.com/nasa/cea/tree/v3.3.4",
                "license": "Apache-2.0",
                "database_sha256": {
                    name: hashlib.sha256((package_dir / "data" / name).read_bytes()).hexdigest()
                    for name in ("thermo.lib", "trans.lib")
                },
                "fuel_species": fuel, "oxidizer_species": oxidizer,
                "fuel_temperature_k": t_fuel, "oxidizer_temperature_k": t_ox,
                "reactant_temperature_defaults_used": self.fuel_temperature_k is None or self.oxidizer_temperature_k is None,
                "chemistry_mode": "equilibrium" if request.equilibrium else "frozen_chamber",
                "frozen_transport_qualification": frozen_strategy,
                "transport_interpretation": "Fixed-composition heat transfer must use frozen Cp/conductivity/Pr. Native equilibrium-named transport fields are diagnostics, not a reacting-flow closure.",
                "combustor": "infinite_area", "converged": True,
                "requested_expansion_ratio": eps,
                "reactant_temperature_ranges_k": temperature_ranges,
                "reactant_enthalpy_limitation": "Liquid/reactant-only database entries use tabulated reference enthalpy, not a heated-liquid EOS model. Temperature-range acceptance does not establish liquid phase or pressure validity.",
            },
        )


def bind_nasa_cea_engine(**kwargs) -> NasaCeaEngine:
    """Factory used by systems / scripts / GUI wiring."""

    return NasaCeaEngine(**kwargs)
