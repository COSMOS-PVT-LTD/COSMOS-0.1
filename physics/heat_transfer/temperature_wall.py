"""Additive temperature-dependent planar ligament heat balance, not cooled-wall FEA."""
from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise

from core.dimension import AREA, LENGTH, POWER, TEMPERATURE
from core.exceptions import InvalidInputError, SolverConvergenceError
from core.quantity import Quantity
from core.validation import validate_positive
from numerics.integration.trapezoidal import integrate
from numerics.interpolation.linear import interpolate
from numerics.root_finding.bisection import solve
from numerics.utilities.tolerances import Tolerances
from physics.exceptions import OutOfRangeError
from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.si import HEAT_TRANSFER_COEFFICIENT

TEMPERATURE_WALL = ModelIdentity(
    model_id="PHYS-COOL.temperature_dependent_planar_ligament",
    model_name="Temperature-dependent gas/ligament/coolant heat balance",
    physical_domain="heat_transfer",
    equations=("Q=hg Ag (Taw-Th)=hc Ac (Tc-Tbulk)", "Q L/Acond=integral(Tc,Th,k(T)dT)"),
    inputs=("gas/coolant temperatures [K]", "gas/coolant coefficients [W/m2/K] and areas [m2]",
            "ligament length [m] and conduction area [m2]", "bounded sourced material-condition k(T) curve"),
    outputs=("heat [W]", "hot/cold wall temperatures [K]", "independent balance residuals [W]"),
    assumptions=("Steady 1D planar wall; no internal generation; positive continuous piecewise-linear k(T).",
                 "Isothermal fluid nodes; prescribed local coefficients/areas; no rib/fin enhancement implicitly credited."),
    validity_range="Both wall surfaces inside exact supplied material-condition temperature interval; no extrapolation",
    source="Fourier differential law integrated across a wall, Newton convection and steady energy balance (DOE-HDBK-1012/2-92).",
    verification_status="independent constant/linear-k solutions, separate flux balances and domain tests",
    limitations=("Not 2D rib/roof/sidewall conduction, bimetal contact, thermal stress, creep, fatigue or a material allowable.",
                 "Does not infer a GRCop-42 or IN718 property curve from the alloy name or a room-temperature point.",
                 "Prescribed convection needs independently applicable correlations; not boiling or full engine cooling closure."),
)


@dataclass(frozen=True, slots=True)
class ConductivityCurve:
    material_id: str
    condition: str
    temperatures_k: tuple[float,...]
    conductivities_w_m_k: tuple[float,...]
    source: str
    source_sha256: str

    def __post_init__(self):
        if (type(self.temperatures_k) is not tuple or type(self.conductivities_w_m_k) is not tuple
            or not 2<=len(self.temperatures_k)<=129 or len(self.conductivities_w_m_k)!=len(self.temperatures_k)
            or any(type(v) not in {int,float} or not math.isfinite(v) or v<=0 for v in self.temperatures_k+self.conductivities_w_m_k)
            or any(b<=a for a,b in pairwise(self.temperatures_k))):
            raise InvalidInputError("Complete immutable bounded positive k(T) curve required; one point is not a material window")
        if any(type(v) is not str or not v.strip() for v in (self.material_id,self.condition,self.source)):
            raise InvalidInputError("Material, manufacturing/heat-treatment condition and property source required")
        if type(self.source_sha256) is not str or len(self.source_sha256)!=64 or set(self.source_sha256)-set("0123456789abcdef"):
            raise InvalidInputError("Retained property source SHA256 required")

    def value(self,t):
        if not self.temperatures_k[0]<=t<=self.temperatures_k[-1]:
            raise OutOfRangeError("Wall temperature outside the sourced material-condition k(T) domain")
        return interpolate(self.temperatures_k,self.conductivities_w_m_k,t)

    def integral(self,cold,hot):
        self.value(cold);self.value(hot)
        if hot<cold:raise OutOfRangeError("Only gas-to-coolant wall heating is supported")
        nodes=[cold,*[t for t in self.temperatures_k if cold<t<hot],hot]
        return math.fsum(integrate(self.value,a,b,intervals=1) for a,b in pairwise(nodes) if b>a)


@dataclass(frozen=True, slots=True)
class WallBalance:
    heat_w: float
    hot_wall_temperature_k: float
    cold_wall_temperature_k: float
    conduction_residual_w: float
    gas_residual_w: float
    coolant_residual_w: float
    iterations: int


def temperature_dependent_wall(*, gas_temperature: Quantity, coolant_temperature: Quantity,
    gas_coefficient: Quantity, coolant_coefficient: Quantity, gas_area: Quantity,
    coolant_area: Quantity, conduction_area: Quantity, thickness: Quantity,
    conductivity: ConductivityCurve, heat_tolerance: Quantity, max_iterations: int) -> WallBalance:
    def positive(q,dim,name):return validate_positive(as_si(q,dim,name),name)
    tg=positive(gas_temperature,TEMPERATURE,"gas temperature");tb=positive(coolant_temperature,TEMPERATURE,"coolant temperature")
    hg=positive(gas_coefficient,HEAT_TRANSFER_COEFFICIENT,"gas coefficient")*positive(gas_area,AREA,"gas area")
    hc=positive(coolant_coefficient,HEAT_TRANSFER_COEFFICIENT,"coolant coefficient")*positive(coolant_area,AREA,"coolant area")
    conductance=positive(conduction_area,AREA,"conduction area")/positive(thickness,LENGTH,"ligament thickness")
    tolerance=positive(heat_tolerance,POWER,"heat balance tolerance")
    if not all(math.isfinite(v) and v>0 for v in (hg,hc,conductance)):
        raise InvalidInputError("Finite representable convection and geometric conductances required")
    if type(max_iterations) is not int or not 1<=max_iterations<=1000:raise InvalidInputError("Explicit numerical iteration limit1..1000 required")
    if tb>tg:raise OutOfRangeError("Coolant hotter than gas: heating model is inapplicable")
    tmin,tmax=conductivity.temperatures_k[0],conductivity.temperatures_k[-1]
    lower=max(0.,hg*(tg-tmax),hc*(tmin-tb))
    upper=min(hg*(tg-tmin),hc*(tmax-tb),(tg-tb)/(1/hg+1/hc))
    if lower>upper:raise OutOfRangeError("No heat balance can keep both wall surfaces in the sourced k(T) domain")
    def walls(heat):return tg-heat/hg,tb+heat/hc
    def residual(heat):
        th,tc=walls(heat)
        # Only floating-point endpoint clamp, never curve extrapolation.
        th=min(tmax,max(tmin,th));tc=min(th,max(tmin,tc))
        return conductance*conductivity.integral(tc,th)-heat
    if residual(lower)<0 or residual(upper)>0:
        raise OutOfRangeError("Wall heat-balance root lies outside the supplied material-condition domain")
    if lower==upper:heat=lower;iterations=0
    else:
        solution=solve(residual,lower,upper,policy=Tolerances(absolute=tolerance*min(.1,1/(4+4*conductance*max(conductivity.conductivities_w_m_k)*(1/hg+1/hc))),relative=0,residual=tolerance,max_iterations=max_iterations))
        heat=solution.value;iterations=solution.iterations
    th,tc=walls(heat);error=residual(heat)
    if not all(math.isfinite(v) for v in (heat,th,tc,error)) or abs(error)>tolerance:
        raise SolverConvergenceError("Temperature-dependent wall energy residual exceeds explicit tolerance; no accepted wall state")
    return WallBalance(heat,th,tc,error,hg*(tg-th)-heat,hc*(tc-tb)-heat,iterations)
