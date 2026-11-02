"""Single-phase, constant-area circular feed segment with sourced h(T,P).

Additive steady finite-volume cell, not a complete engine or coolant correlation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import (
    DIMENSIONLESS,
    LENGTH,
    MASS_FLOW_RATE,
    POWER,
    PRESSURE,
    TEMPERATURE,
)
from core.exceptions import InvalidInputError, SolverConvergenceError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_non_negative, validate_positive
from numerics.root_finding.bisection import solve
from numerics.utilities.tolerances import Tolerances
from physics.exceptions import OutOfRangeError
from physics.fluids.liquid_table import LiquidState, LiquidTable
from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.si import SPECIFIC_ENERGY

HEATED_LIQUID_SEGMENT = ModelIdentity(
    model_id="PHYS-FEED.sourced_enthalpy_circular_segment",
    model_name="Bounded liquid feed segment with heat, friction and acceleration",
    physical_domain="feed",
    equations=("h_out+u_out²/2=h_in+u_in²/2+Q/mdot; u=mdot/(rho A)",
               "P_in-P_out=(f_D L/D+K)*G²/(2 rho_mid)+G²*(1/rho_out-1/rho_in)",
               "f_D=64/Re for Re<=2300; Colebrook for4000<=Re<=1e8"),
    inputs=("flow, inlet T/P and explicit outlet-P bracket", "circular bore, length, roughness, supplied minor-loss coefficient/source",
            "prescribed heat [W]", "same-fluid bounded source h,rho,mu(T,P) table", "explicit numerical energy/pressure tolerances"),
    outputs=("outlet T/P,h,rho,velocity", "viscous and acceleration pressure drops", "energy/momentum residuals"),
    assumptions=("Steady horizontal straight constant-area cell; no shaft work; cell-midpoint friction; equal inlet/outlet flow.",
                 "Positive subcooled single-phase table throughout explicit solve bracket; caller refines cells to establish discretization convergence."),
    validity_range="L/D>=10; relative roughness<=.05; no2300<Re<4000; Re<=1e8; source table only",
    source="Steady mass/first-law/momentum balances; NASA TM-1998-206313 printedpp17-18 eq14-16 (viscous plus momentum loss); Colebrook circular-pipe correlation.",
    verification_status="Poiseuille/constant-density exact balances, Colebrook residual, heated property/phase/pressure bounds and refinement tests",
    limitations=("No boiling/cavitation inception, elevation, unsteady water hammer, curvature, sudden-area changes or inferred fitting coefficients.",
                 "Heat is explicitly supplied, not computed from gas/wall; not a matching noncircular cooling-passage correlation.",
                 "Not installed into the legacy operating-point solver, not a solved engine or physical qualification."),
)


def darcy_factor(reynolds: float, relative_roughness: float) -> float:
    if (type(reynolds) not in {int,float} or type(relative_roughness) not in {int,float}
        or not math.isfinite(reynolds) or not 0<reynolds<=1e8
        or not math.isfinite(relative_roughness) or not 0<=relative_roughness<=.05):
        raise OutOfRangeError("Circular-pipe Reynolds/relative-roughness envelope exceeded")
    if reynolds<=2300:return 64/reynolds
    if reynolds<4000:raise OutOfRangeError("Transitional pipe flow is not a supported friction model")
    def residual(inverse_root):
        return inverse_root+2*math.log10(relative_roughness/3.7+2.51*inverse_root/reynolds)
    root=solve(residual,1.,100.,policy=Tolerances(absolute=1e-12,relative=0,residual=1e-11,max_iterations=80)).value
    return 1/(root*root)


@dataclass(frozen=True, slots=True)
class HeatedLiquidSegment:
    outlet_temperature_k: float
    outlet_pressure_pa: float
    outlet_state: LiquidState
    inlet_velocity_m_s: float
    outlet_velocity_m_s: float
    reynolds: float
    darcy_friction_factor: float
    friction_pressure_loss_pa: float
    acceleration_pressure_loss_pa: float
    energy_residual_j_kg: float
    momentum_residual_pa: float


def heated_liquid_segment(*, table: LiquidTable, mass_flow: Quantity,
    inlet_temperature: Quantity, inlet_pressure: Quantity, outlet_pressure_min: Quantity,
    length: Quantity, diameter: Quantity, roughness: Quantity, minor_loss: Quantity,
    heat: Quantity, pressure_tolerance: Quantity, specific_energy_tolerance: Quantity,
    max_iterations: int, loss_source: str) -> HeatedLiquidSegment:
    def value(q,dim,name,zero=False):
        v=as_si(q,dim,name)
        return (validate_non_negative if zero else validate_positive)(v,name)
    mass=value(mass_flow,MASS_FLOW_RATE,"mass flow");tin=value(inlet_temperature,TEMPERATURE,"inlet temperature")
    pin=value(inlet_pressure,PRESSURE,"inlet pressure");lower=value(outlet_pressure_min,PRESSURE,"outlet pressure lower bound")
    distance=value(length,LENGTH,"straight length");bore=value(diameter,LENGTH,"circular diameter")
    epsilon=value(roughness,LENGTH,"roughness",True);k=value(minor_loss,DIMENSIONLESS,"minor loss",True)
    heat_w=value(heat,POWER,"prescribed heat",True);ptol=value(pressure_tolerance,PRESSURE,"pressure tolerance")
    etol=value(specific_energy_tolerance,SPECIFIC_ENERGY,"energy tolerance")
    if type(max_iterations) is not int or not 1<=max_iterations<=1000 or type(loss_source) is not str or not loss_source.strip():
        raise InvalidInputError("Explicit numerical iteration limit and minor-loss geometry/characteristic source required")
    if not table.pressures_pa[0]<=lower<pin<=table.pressures_pa[-1] or distance/bore<10 or epsilon/bore>.05:
        raise OutOfRangeError("Explicit P bracket inside source table, L/D>=10 and roughness/D<=.05 required")
    area=math.pi*bore*bore/4;flux=mass/area
    incoming=table.evaluate(Quantity(tin,SI.get("K")),Quantity(pin,SI.get("Pa")))
    velocity=flux/incoming.density_kg_m3
    total_energy=incoming.enthalpy_j_kg+velocity*velocity/2+heat_w/mass
    if not all(math.isfinite(v) for v in (flux,total_energy,area)) or area<=0:
        raise InvalidInputError("Feed cell exceeds finite representable flow/energy bounds")
    def candidate(pressure):
        p=Quantity(pressure,SI.get("Pa"))
        def energy(t):
            s=table.evaluate(Quantity(t,SI.get("K")),p)
            return s.enthalpy_j_kg+(flux/s.density_kg_m3)**2/2-total_energy
        tlo,thi=table.temperatures_k[0],table.temperatures_k[-1]
        if energy(tlo)>0 or energy(thi)<0:
            raise OutOfRangeError("Heated feed energy requires a temperature/phase outside the retained table; no cold-state fallback")
        solution=solve(energy,tlo,thi,policy=Tolerances(absolute=1e-12,relative=0,residual=etol,max_iterations=max_iterations))
        temperature=solution.value;state=table.evaluate(Quantity(temperature,SI.get("K")),p)
        middle=table.evaluate(Quantity((tin+temperature)/2,SI.get("K")),Quantity((pin+pressure)/2,SI.get("Pa")))
        reynolds=flux*bore/middle.viscosity_pa_s;factor=darcy_factor(reynolds,epsilon/bore)
        friction=(factor*distance/bore+k)*flux*flux/(2*middle.density_kg_m3)
        acceleration=flux*flux*(1/state.density_kg_m3-1/incoming.density_kg_m3)
        residual=pin-pressure-friction-acceleration
        return temperature,state,reynolds,factor,friction,acceleration,energy(temperature),residual
    if candidate(lower)[-1]<0 or candidate(pin)[-1]>0:
        raise OutOfRangeError("Available pressure bracket cannot carry this flow/heat/geometry; no fitted surplus-pressure loss")
    solved=solve(lambda p:candidate(p)[-1],lower,pin,policy=Tolerances(absolute=ptol*.01,relative=0,residual=ptol,max_iterations=max_iterations))
    t,state,re,factor,friction,acceleration,energy_error,momentum_error=candidate(solved.value)
    if abs(energy_error)>etol or abs(momentum_error)>ptol:
        raise SolverConvergenceError("Heated feed cell failed declared energy/momentum tolerances; no accepted state")
    return HeatedLiquidSegment(t,solved.value,state,velocity,flux/state.density_kg_m3,re,factor,friction,acceleration,energy_error,momentum_error)
