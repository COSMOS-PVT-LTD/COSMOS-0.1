"""Matched hot-wall/liquid/injector branch at explicit chamber pressure.

Additive isolated analysis. No surrogate rectangle/circle for native sectors,
prescribed heat, balancing resistance or owner-workflow promotion.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from core.dimension import AREA, DIMENSIONLESS, MASS_FLOW_RATE, PRESSURE
from core.exceptions import InvalidInputError, SolverConvergenceError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive
from numerics.root_finding.bisection import solve
from numerics.utilities.tolerances import Tolerances
from physics.exceptions import OutOfRangeError
from physics.feed.matched_liquid_cell import (
    MatchedLiquidCell,
    PassageGeometry,
    TransferLaw,
    matched_liquid_cell,
)
from physics.fluids.liquid_table import LiquidTable
from physics.heat_transfer.temperature_wall import ConductivityCurve
from physics.quantities import as_si


@dataclass(frozen=True, slots=True)
class MatchedFeedCell:
    cell_id: str
    upstream_interface: str
    downstream_interface: str
    geometry: PassageGeometry
    transfer: TransferLaw
    conductivity: ConductivityCurve
    gas_temperature: Quantity
    gas_coefficient: Quantity
    outlet_temperature_lower: Quantity
    outlet_temperature_upper: Quantity


@dataclass(frozen=True, slots=True)
class MatchedFeedBranch:
    mass_flow_kg_s: float
    injector_capacity_kg_s: float
    injector_residual_kg_s: float
    manifold_pressure_pa: float
    manifold_temperature_k: float
    manifold_enthalpy_j_kg: float
    total_heat_w: float
    energy_residual_w: float
    cells: tuple[MatchedLiquidCell,...]
    scope: str = "GIVEN_CHAMBER_PRESSURE_MATCHED_WALL_LIQUID_INJECTOR_BRANCH"
    gas_feedback: str = "SUPPLIED_GAS_BOUNDARIES_NOT_RECOMPUTED_COMBUSTION"
    engine_operating_point_complete: bool = False
    physical_validation: str = "NOT_PERFORMED"


def solve_matched_feed_branch(*, table: LiquidTable, cells: tuple[MatchedFeedCell,...],
    source_interface: str, injector_interface: str, source_temperature: Quantity,
    source_pressure: Quantity, chamber_pressure: Quantity, minimum_manifold_pressure: Quantity,
    injector_total_area: Quantity, discharge_coefficient: Quantity, flow_lower: Quantity,
    flow_upper: Quantity, mass_tolerance: Quantity, power_tolerance: Quantity,
    pressure_tolerance: Quantity, max_iterations: int) -> MatchedFeedBranch:
    if (type(cells) is not tuple or not 1<=len(cells)<=128 or any(type(c) is not MatchedFeedCell for c in cells)
        or len({c.cell_id for c in cells})!=len(cells)):
        raise InvalidInputError("Immutable ordered series of1..128 uniquely named matched feed cells required")
    labels=[source_interface,injector_interface,*[v for c in cells for v in (c.cell_id,c.upstream_interface,c.downstream_interface)]]
    if any(type(v) is not str or not v.strip() for v in labels):
        raise InvalidInputError("Explicit nonempty physical-interface references required")
    current=source_interface;visited={current}
    for cell in cells:
        if cell.upstream_interface!=current or cell.downstream_interface in visited:
            raise InvalidInputError("Matched cells must form an explicit connected acyclic source-to-injector route")
        current=cell.downstream_interface;visited.add(current)
    if current!=injector_interface:raise InvalidInputError("Matched route must terminate at the selected actual injector inlet")
    def positive(q,dimension,name):
        if not isinstance(q,Quantity) or isinstance(q.magnitude,bool):raise InvalidInputError(name+" requires a non-Boolean Core Quantity")
        return validate_positive(as_si(q,dimension,name),name)
    pc=positive(chamber_pressure,PRESSURE,"chamber pressure")
    minimum=positive(minimum_manifold_pressure,PRESSURE,"minimum manifold pressure")
    area=positive(injector_total_area,AREA,"exact injector total bore area")
    cd=positive(discharge_coefficient,DIMENSIONLESS,"injector discharge coefficient")
    lo=positive(flow_lower,MASS_FLOW_RATE,"lower flow bound");hi=positive(flow_upper,MASS_FLOW_RATE,"upper flow bound")
    tol=positive(mass_tolerance,MASS_FLOW_RATE,"mass closure tolerance")
    if minimum<=pc or cd>1 or lo>=hi:raise OutOfRangeError("Positive injector pressure head, Cd<=1 and increasing flow bracket required")
    @lru_cache(maxsize=512)
    def evaluate(mass):
        t,p=source_temperature,source_pressure;rows=[]
        for cell in cells:
            result=matched_liquid_cell(table=table,geometry=cell.geometry,transfer=cell.transfer,
                conductivity=cell.conductivity,mass_flow=Quantity(mass,SI.get("kg/s")),
                inlet_temperature=t,inlet_pressure=p,outlet_pressure_min=minimum_manifold_pressure,
                outlet_temperature_lower=cell.outlet_temperature_lower,outlet_temperature_upper=cell.outlet_temperature_upper,
                gas_temperature=cell.gas_temperature,gas_coefficient=cell.gas_coefficient,
                power_tolerance=power_tolerance,pressure_tolerance=pressure_tolerance,max_iterations=max_iterations)
            rows.append(result);t=Quantity(result.outlet_temperature_k,SI.get("K"));p=Quantity(result.outlet_pressure_pa,SI.get("Pa"))
        last=rows[-1]
        capacity=cd*area*math.sqrt(2*last.outlet_state.density_kg_m3*(last.outlet_pressure_pa-pc))
        return capacity,tuple(rows)
    if (lo-evaluate(lo)[0])*(hi-evaluate(hi)[0])>0:
        raise OutOfRangeError("Supplied heated branch/injector does not close inside the explicit flow bracket; no resizing or fitted loss")
    root=solve(lambda mass:mass-evaluate(mass)[0],lo,hi,
        policy=Tolerances(absolute=tol*.01,relative=0,residual=tol,max_iterations=max_iterations))
    capacity,rows=evaluate(root.value);last=rows[-1];error=root.value-capacity
    if not math.isfinite(error) or abs(error)>tol:raise SolverConvergenceError("Matched feed/injector mass closure failed")
    return MatchedFeedBranch(root.value,capacity,error,last.outlet_pressure_pa,last.outlet_temperature_k,
        last.outlet_state.enthalpy_j_kg,math.fsum(row.heat_w for row in rows),math.fsum(row.energy_residual_w for row in rows),rows)
