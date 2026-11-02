"""Additive prescribed-heat liquid branch closure; no workflow promotion.

This connects sourced heated pipe states to liquid injector capacity at a given
chamber pressure. Not a whole-engine/choking or matched hot-wall solution.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import AREA, DIMENSIONLESS, MASS_FLOW_RATE, PRESSURE
from core.exceptions import InvalidInputError, SolverConvergenceError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive
from numerics.root_finding.bisection import solve
from numerics.utilities.tolerances import Tolerances
from physics.exceptions import OutOfRangeError
from physics.feed.heated_liquid_segment import (
    HeatedLiquidSegment,
    heated_liquid_segment,
)
from physics.fluids.liquid_table import LiquidTable
from physics.quantities import as_si


@dataclass(frozen=True, slots=True)
class CircularFeedCell:
    cell_id: str
    upstream_interface: str
    downstream_interface: str
    length: Quantity
    diameter: Quantity
    roughness: Quantity
    minor_loss: Quantity
    prescribed_heat: Quantity
    characteristic_source: str


@dataclass(frozen=True, slots=True)
class HeatedFeedBranch:
    mass_flow_kg_s: float
    injector_capacity_kg_s: float
    injector_residual_kg_s: float
    manifold_pressure_pa: float
    manifold_temperature_k: float
    manifold_density_kg_m3: float
    prescribed_heat_w: float
    cells: tuple[HeatedLiquidSegment,...]
    scope: str = "GIVEN_CHAMBER_PRESSURE_PRESCRIBED_HEAT_CIRCULAR_FEED_BRANCH_ONLY"
    physical_validation: str = "NOT_PERFORMED"
    engine_operating_point_complete: bool = False


def solve_heated_feed_branch(*, table: LiquidTable, cells: tuple[CircularFeedCell,...],
    source_interface: str, injector_interface: str, source_temperature: Quantity, source_pressure: Quantity,
    chamber_pressure: Quantity, minimum_manifold_pressure: Quantity, injector_total_area: Quantity,
    discharge_coefficient: Quantity, flow_lower: Quantity, flow_upper: Quantity,
    mass_tolerance: Quantity, pressure_tolerance: Quantity, specific_energy_tolerance: Quantity,
    max_iterations: int) -> HeatedFeedBranch:
    """Solve actual heated upstream density and pressure vs injector capacity.

    Interface names enforce explicit series order, not geometric/seal proof.
    This model cannot consume the native sector passages as circular pipes.
    Every cell's heat/characteristic is explicit. No balancing valve or loss is
    invented to consume excess pressure or hit the desired thrust.
    """
    if type(cells) is not tuple or not 1<=len(cells)<=128 or any(type(c) is not CircularFeedCell for c in cells):
        raise InvalidInputError("An immutable explicit series of1..128 circular feed cells required")
    labels=[source_interface,injector_interface,*[v for c in cells for v in (c.cell_id,c.upstream_interface,c.downstream_interface,c.characteristic_source)]]
    if any(type(v) is not str or not v.strip() for v in labels) or len({c.cell_id for c in cells})!=len(cells):
        raise InvalidInputError("Unique cell identities, explicit physical-interface references and characteristic sources required")
    current=source_interface;visited={current}
    for cell in cells:
        if cell.upstream_interface!=current or cell.downstream_interface in visited:
            raise InvalidInputError("Feed cells must form one explicit acyclic ordered route; no disconnected/repeated interface")
        current=cell.downstream_interface;visited.add(current)
    if current!=injector_interface:raise InvalidInputError("Last feed cell must terminate at the selected injector inlet")
    def positive(q,dim,name):return validate_positive(as_si(q,dim,name),name)
    chamber=positive(chamber_pressure,PRESSURE,"chamber pressure")
    minimum=positive(minimum_manifold_pressure,PRESSURE,"minimum liquid manifold pressure")
    area=positive(injector_total_area,AREA,"exact total liquid injector bore area")
    cd=positive(discharge_coefficient,DIMENSIONLESS,"liquid injector Cd")
    lo=positive(flow_lower,MASS_FLOW_RATE,"flow lower bound");hi=positive(flow_upper,MASS_FLOW_RATE,"flow upper bound")
    tol=positive(mass_tolerance,MASS_FLOW_RATE,"mass closure tolerance")
    if minimum<=chamber or cd>1 or lo>=hi:raise OutOfRangeError("Positive injector pressure head, Cd<=1 and increasing flow bounds required")
    def evaluate(flow):
        temperature,pressure=source_temperature,source_pressure;rows=[]
        for cell in cells:
            result=heated_liquid_segment(table=table,mass_flow=Quantity(flow,SI.get("kg/s")),
                inlet_temperature=temperature,inlet_pressure=pressure,outlet_pressure_min=minimum_manifold_pressure,
                length=cell.length,diameter=cell.diameter,roughness=cell.roughness,minor_loss=cell.minor_loss,
                heat=cell.prescribed_heat,pressure_tolerance=pressure_tolerance,specific_energy_tolerance=specific_energy_tolerance,
                max_iterations=max_iterations,loss_source=cell.characteristic_source)
            rows.append(result);temperature=Quantity(result.outlet_temperature_k,SI.get("K"));pressure=Quantity(result.outlet_pressure_pa,SI.get("Pa"))
        last=rows[-1]
        capacity=cd*area*math.sqrt(2*last.outlet_state.density_kg_m3*(last.outlet_pressure_pa-chamber))
        return capacity,tuple(rows)
    if (lo-evaluate(lo)[0])*(hi-evaluate(hi)[0])>0:
        raise OutOfRangeError("Flow bracket does not close supplied feed/injector geometry; no target-forcing rescale")
    root=solve(lambda flow:flow-evaluate(flow)[0],lo,hi,
        policy=Tolerances(absolute=tol*.01,relative=0,residual=tol,max_iterations=max_iterations))
    capacity,rows=evaluate(root.value);last=rows[-1];error=root.value-capacity
    if not math.isfinite(error) or abs(error)>tol:
        raise SolverConvergenceError("Heated feed/injector mass residual exceeds tolerance; no accepted branch")
    return HeatedFeedBranch(root.value,capacity,error,last.outlet_pressure_pa,last.outlet_temperature_k,last.outlet_state.density_kg_m3,
        math.fsum(cell.prescribed_heat.to_si() for cell in cells),rows)
