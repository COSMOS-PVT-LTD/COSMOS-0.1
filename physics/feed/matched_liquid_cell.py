"""Matched hot-wall / liquid control volume with explicit transfer response.

Constant-area flow-normal passage only; noncircular shape is permitted ONLY
with its own sourced response, not by treating 4A/P as a circular pipe.
No storage, network access, coefficient defaults or engine promotion.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from core.dimension import AREA, LENGTH, MASS_FLOW_RATE, POWER, PRESSURE, TEMPERATURE
from core.exceptions import InvalidInputError, SolverConvergenceError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive
from numerics.root_finding.bisection import solve
from numerics.utilities.tolerances import Tolerances
from physics.exceptions import OutOfRangeError
from physics.fluids.liquid_table import LiquidState, LiquidTable
from physics.heat_transfer.temperature_wall import (
    ConductivityCurve,
    WallBalance,
    temperature_dependent_wall,
)
from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.si import HEAT_TRANSFER_COEFFICIENT

MATCHED_LIQUID_CELL = ModelIdentity(
    model_id="PHYS-FEED.matched_wall_liquid_cell",
    model_name="Source-bound matched wall and liquid control volume",
    physical_domain="feed",
    equations=("Q=N*Q_wall=mdot*(h_out-h_in+(u_out²-u_in²)/2)",
        "P_in-P_out=f_D*(L/Dh)*G²/(2*rho_mid)+G²*(1/rho_out-1/rho_in)",
        "Q_wall=hg*Ag*(Tgas-Th)=hc*Ac*(Tc-Tbulk)=Acond/Lwall*integral(k(T)dT)"),
    inputs=("Exact constant-area flow-normal geometry and identical passage count",
        "Sourced geometry-matched local Darcy/heat-transfer response", "Bounded liquid h/rho/transport table and condition-specific k(T)",
        "Explicit gas boundary, inlet state, flow, outlet brackets and numerical tolerances"),
    outputs=("Matched heat, wall and outlet liquid states", "Independent energy and momentum residuals"),
    assumptions=("Steady horizontal constant-area finite volume; midpoint transport and bulk temperature.",
        "Identical parallel channels; prescribed gas boundary; 1D planar ligament; no implicit rib enhancement."),
    validity_range="Supplied geometry/transfer/material/property domains; coolant-contact wall below conservative sourced saturation bound",
    source="Steady first-law/momentum balances; integrated Fourier and Newton laws via PHYS-COOL.temperature_dependent_planar_ligament; transfer source supplied per response.",
    verification_status="Independent analytic incompressible heat/pressure solution, parallel scaling and strict source/domain tests",
    limitations=("No circular correlation is inferred from hydraulic diameter. Native sloping sectors, bends, plenums and flow splits require applicable models.",
        "No boiling, coupled combustion/nozzle, bimetal/rib conduction, thermal stress, fatigue or physical validation."),
)


@dataclass(frozen=True, slots=True)
class PassageGeometry:
    """Per-passage areas; identical parallel passages, no inferred flow split."""
    flow_area: Quantity
    hydraulic_diameter: Quantity
    length: Quantity
    gas_area: Quantity
    coolant_area: Quantity
    conduction_area: Quantity
    ligament: Quantity
    parallel_count: int
    source_graph_id: str
    section_basis: str


@dataclass(frozen=True, slots=True)
class PassageTransfer:
    """Local response already evaluated at the requested liquid state.

    An adapter must check its own fluid/shape/roughness/entry/curvature and
    Reynolds/Prandtl domains. This record cannot grant physical qualification.
    """
    darcy_factor: float
    coolant_coefficient: Quantity
    source: str
    source_sha256: str
    geometry_graph_id: str


TransferLaw = Callable[[PassageGeometry, LiquidState, float, float, float, float], PassageTransfer]


@dataclass(frozen=True, slots=True)
class MatchedLiquidCell:
    outlet_temperature_k: float
    outlet_pressure_pa: float
    outlet_state: LiquidState
    mass_flow_kg_s: float
    heat_w: float
    energy_residual_w: float
    momentum_residual_pa: float
    wall: WallBalance
    reynolds: float
    prandtl: float
    transfer_source: str
    transfer_source_sha256: str
    source_graph_id: str
    fluid_id: str
    fluid_raw_sha256: tuple[str,...]
    material_id: str
    material_condition: str
    conductivity_source_sha256: str
    scope: str = "MATCHED_CONSTANT_AREA_IDENTICAL_PARALLEL_PASSAGES_PLANAR_LIGAMENT"
    physical_validation: str = "NOT_PERFORMED"


def matched_liquid_cell(*, table: LiquidTable, geometry: PassageGeometry,
    transfer: TransferLaw, conductivity: ConductivityCurve, mass_flow: Quantity,
    inlet_temperature: Quantity, inlet_pressure: Quantity, outlet_pressure_min: Quantity,
    outlet_temperature_lower: Quantity, outlet_temperature_upper: Quantity,
    gas_temperature: Quantity, gas_coefficient: Quantity,
    power_tolerance: Quantity, pressure_tolerance: Quantity, max_iterations: int) -> MatchedLiquidCell:
    """Solve T_out/P_out and Q_wall=mdot*(h_out-h_in+delta(u²/2)).

    Mid-cell transport and convection, integrated k(T), viscous plus acceleration
    momentum. Caller establishes cell refinement; no boiling, varying area,
    bends/headers, rib enhancement, contact resistance or stress is inferred.
    Gas boundary is explicit, not a recomputed combustion/nozzle solution.
    """
    def positive(q,dim,name):
        if not isinstance(q,Quantity) or isinstance(q.magnitude,bool):
            raise InvalidInputError(name+" requires a non-Boolean Core Quantity")
        return validate_positive(as_si(q,dim,name),name)
    if type(geometry) is not PassageGeometry or geometry.section_basis!="CONSTANT_AREA_FLOW_NORMAL":
        raise InvalidInputError("Exact constant-area flow-normal geometry required; axial CAD slices are not equivalent")
    if (type(geometry.parallel_count) is not int or not 1<=geometry.parallel_count<=10000
        or type(geometry.source_graph_id) is not str or not geometry.source_graph_id.strip()
        or not callable(transfer) or type(max_iterations) is not int or not 1<=max_iterations<=300):
        raise InvalidInputError("Explicit graph, identical passage count, transfer adapter and bounded iteration policy required")
    area=positive(geometry.flow_area,AREA,"per-passage area")
    diameter=positive(geometry.hydraulic_diameter,LENGTH,"flow-normal hydraulic diameter")
    length=positive(geometry.length,LENGTH,"passage length")
    for name in ("gas_area","coolant_area","conduction_area"):
        positive(getattr(geometry,name),AREA,name)
    positive(geometry.ligament,LENGTH,"ligament")
    mass=positive(mass_flow,MASS_FLOW_RATE,"total coolant flow")
    tin=positive(inlet_temperature,TEMPERATURE,"inlet temperature")
    pin=positive(inlet_pressure,PRESSURE,"inlet pressure")
    pmin=positive(outlet_pressure_min,PRESSURE,"outlet pressure lower bound")
    tlo=positive(outlet_temperature_lower,TEMPERATURE,"outlet temperature lower bound")
    thi=positive(outlet_temperature_upper,TEMPERATURE,"outlet temperature upper bound")
    positive(gas_temperature,TEMPERATURE,"gas temperature")
    positive(gas_coefficient,HEAT_TRANSFER_COEFFICIENT,"gas coefficient")
    wtol=positive(power_tolerance,POWER,"power tolerance")
    ptol=positive(pressure_tolerance,PRESSURE,"pressure tolerance")
    if not table.pressures_pa[0]<=pmin<pin<=table.pressures_pa[-1] or not table.temperatures_k[0]<=tlo<thi<=table.temperatures_k[-1]:
        raise OutOfRangeError("Explicit increasing temperature/pressure brackets inside the retained liquid surface required")
    flux=mass/(geometry.parallel_count*area)
    incoming=table.evaluate(inlet_temperature,inlet_pressure)
    flux_squared=flux*flux
    if not math.isfinite(flux_squared) or flux<=0:raise InvalidInputError("Finite representable positive mass flux required")
    def at(tout,pout):
        state=table.evaluate(Quantity(tout,SI.get("K")),Quantity(pout,SI.get("Pa")))
        tm=(tin+tout)/2;pm=(pin+pout)/2
        mid=table.evaluate(Quantity(tm,SI.get("K")),Quantity(pm,SI.get("Pa")))
        re=flux*diameter/mid.viscosity_pa_s;pr=mid.cp_j_kg_k*mid.viscosity_pa_s/mid.conductivity_w_m_k
        if not all(math.isfinite(v) and v>0 for v in (re,pr)):
            raise InvalidInputError("Finite representable positive Reynolds/Prandtl state required")
        response=transfer(geometry,mid,re,pr,tm,pm)
        if (type(response) is not PassageTransfer or response.geometry_graph_id!=geometry.source_graph_id
            or type(response.darcy_factor) not in {int,float} or not math.isfinite(response.darcy_factor) or response.darcy_factor<=0
            or type(response.source) is not str or not response.source.strip()
            or type(response.source_sha256) is not str or len(response.source_sha256)!=64
            or set(response.source_sha256)-set("0123456789abcdef")):
            raise InvalidInputError("Source-bound finite positive passage response for the exact geometry graph required")
        positive(response.coolant_coefficient,HEAT_TRANSFER_COEFFICIENT,"coolant coefficient")
        friction=response.darcy_factor*length/diameter*flux_squared/(2*mid.density_kg_m3)
        acceleration=flux_squared*(1/state.density_kg_m3-1/incoming.density_kg_m3)
        return state,mid,response,re,pr,pin-pout-friction-acceleration
    def candidate(tout):
        if at(tout,pmin)[-1]<0 or at(tout,pin)[-1]>0:
            raise OutOfRangeError("Available pressure bracket cannot carry the matched flow and heated density")
        pressure=solve(lambda p:at(tout,p)[-1],pmin,pin,
            policy=Tolerances(absolute=ptol*.01,relative=0,residual=ptol,max_iterations=max_iterations)).value
        state,_mid,response,re,pr,momentum=at(tout,pressure)
        wall=temperature_dependent_wall(gas_temperature=gas_temperature,
            coolant_temperature=Quantity((tin+tout)/2,SI.get("K")),gas_coefficient=gas_coefficient,
            coolant_coefficient=response.coolant_coefficient,gas_area=geometry.gas_area,
            coolant_area=geometry.coolant_area,conduction_area=geometry.conduction_area,
            thickness=geometry.ligament,conductivity=conductivity,
            heat_tolerance=Quantity(wtol/(10*geometry.parallel_count),SI.get("W")),max_iterations=max_iterations)
        if wall.cold_wall_temperature_k>=table.lowest_saturation_temperature_k:
            raise OutOfRangeError("Coolant-contact wall reaches the conservative sourced saturation bound; local boiling is unsupported")
        heat=geometry.parallel_count*wall.heat_w
        uout=flux/state.density_kg_m3;uin=flux/incoming.density_kg_m3
        energy=mass*(state.enthalpy_j_kg-incoming.enthalpy_j_kg+.5*(uout*uout-uin*uin))-heat
        return energy,pressure,state,wall,heat,re,pr,response,momentum
    if candidate(tlo)[0]>0 or candidate(thi)[0]<0:
        raise OutOfRangeError("Matched wall/liquid root outside explicit temperature or material/phase domain; no prescribed-heat fallback")
    root=solve(lambda t:candidate(t)[0],tlo,thi,
        policy=Tolerances(absolute=1e-12,relative=0,residual=wtol,max_iterations=max_iterations))
    energy,pressure,state,wall,heat,re,pr,response,momentum=candidate(root.value)
    if not all(math.isfinite(v) for v in (energy,momentum,heat)) or abs(energy)>wtol or abs(momentum)>ptol:
        raise SolverConvergenceError("Matched hot-wall/feed residuals exceed declared tolerances; no accepted cell")
    return MatchedLiquidCell(root.value,pressure,state,mass,heat,energy,momentum,wall,re,pr,
        response.source,response.source_sha256,geometry.source_graph_id,table.fluid_id,table.raw_sha256,
        conductivity.material_id,conductivity.condition,conductivity.source_sha256)
