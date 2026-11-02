"""Conservative non-adiabatic divergent quasi-1D frozen perfect-gas nozzle.

Momentum integrates A dp with trapezoidal area. Verify grid convergence;
this is not the old CEA equilibrium/adiabatic nozzle or an exact area-Mach map.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise

from core.dimension import AREA, POWER, PRESSURE, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from physics.exceptions import OutOfRangeError
from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.si import SPECIFIC_HEAT

HEATED_NOZZLE = ModelIdentity(
    model_id="PHYS-NOZZLE.nonadiabatic_frozen_fv.v1",
    model_name="Steady non-adiabatic frozen calorically-perfect divergent nozzle",
    physical_domain="compressible_flow",
    equations=("mdot=rho*u*A", "mdot*(u2-u1)+Abar*(p2-p1)=0", "Cp*T2+u2^2/2=Cp*T1+u1^2/2-Q/mdot", "p=rho*R*T"),
    inputs=("Pc [Pa]", "Tc [K]", "Cp,R [J/kg/K]", "areas [m2]", "cell heat extraction [W]"),
    outputs=("sonic mass flow [kg/s]", "station state", "independent energy/momentum residuals"),
    assumptions=("Adiabatic infinite-area chamber/convergent; frozen perfect gas in nozzle.", "No shocks, wall shear, mass injection or separated flow.", "Trapezoidal integral of area times pressure gradient."),
    validity_range="Strictly increasing divergent areas; positive supersonic stations; heat extraction nonnegative; separately declared gas-property window.",
    source="https://www.grc.nasa.gov/www/k-12/airplane/mflchk.html; quasi-1D mass/momentum/energy conservation, explicit COSMOS finite-volume discretization",
    limitations=("Requires independent grid-refinement verification.", "Not CEA equilibrium expansion or full engine CFD; no physical validation."),
)


@dataclass(frozen=True)
class NozzleStation:
    area_m2: float
    pressure_pa: float
    temperature_k: float
    velocity_m_s: float
    mach: float
    total_enthalpy_j_kg: float


@dataclass(frozen=True)
class NozzleSolution:
    mass_flow_kg_s: float
    stations: tuple[NozzleStation, ...]
    energy_residual_w: float
    momentum_residuals_n: tuple[float, ...]


def nonadiabatic_nozzle(
    pressure: Quantity,
    temperature: Quantity,
    cp: Quantity,
    gas_constant: Quantity,
    areas: tuple[Quantity, ...],
    heat: tuple[Quantity, ...],
) -> NozzleSolution:
    pc, tc, c, r = (
        as_si(value, dimension, name)
        for value, dimension, name in ((pressure, PRESSURE, "Pc"), (temperature, TEMPERATURE, "Tc"), (cp, SPECIFIC_HEAT, "Cp"), (gas_constant, SPECIFIC_HEAT, "R"))
    )
    a = tuple(as_si(v, AREA, "area") for v in areas)
    q = tuple(as_si(v, POWER, "heat extraction") for v in heat)
    if (
        not all(math.isfinite(v) and v > 0 for v in (pc, tc, c, r, *a))
        or c <= r or not 2 <= len(a) <= 257 or len(q) != len(a) - 1
        or any(y <= x for x, y in pairwise(a))
        or any(not math.isfinite(v) or v < 0 for v in q)
    ):
        raise InvalidInputError("Require positive finite states/Cp>R, 2-257 increasing areas and nonnegative cell heat extraction.")
    gamma = c / (c - r)
    t = tc * 2 / (gamma + 1)
    p = pc * (2 / (gamma + 1)) ** (gamma / (gamma - 1))
    u = math.sqrt(gamma * r * t)
    mass = p * a[0] * u / (r * t)
    rows = [NozzleStation(a[0], p, t, u, 1.0, c * t + u * u / 2)]
    momentum = []
    for area, extraction in zip(a[1:], q, strict=True):
        previous = rows[-1]
        h = previous.total_enthalpy_j_kg - extraction / mass
        abar = (previous.area_m2 + area) / 2
        factor = abar * r / (area * c)
        # (1-factor/2)u^2 - (u1+Abar*p1/mdot)u + factor*h = 0.
        aa = 1 - factor / 2
        bb = previous.velocity_m_s + abar * previous.pressure_pa / mass
        discriminant = bb * bb - 4 * aa * factor * h
        if h <= 0 or aa <= 0 or discriminant < 0:
            raise OutOfRangeError("No admissible supersonic heat-extracting nozzle root.")
        u = (bb + math.sqrt(discriminant)) / (2 * aa)
        t = (h - u * u / 2) / c
        if t <= 0:
            raise OutOfRangeError("Nonpositive gas temperature after nozzle heat extraction.")
        p = mass * r * t / (area * u)
        mach = u / math.sqrt(gamma * r * t)
        if mach <= 1 or not all(math.isfinite(v) and v > 0 for v in (p, t, u)):
            raise OutOfRangeError("Supersonic nozzle state is inadmissible.")
        rows.append(NozzleStation(area, p, t, u, mach, c * t + u * u / 2))
        momentum.append(mass * (u - previous.velocity_m_s) + abar * (p - previous.pressure_pa))
    energy = mass * (rows[0].total_enthalpy_j_kg - rows[-1].total_enthalpy_j_kg) - math.fsum(q)
    return NozzleSolution(mass, tuple(rows), energy, tuple(momentum))
