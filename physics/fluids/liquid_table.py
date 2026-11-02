"""Immutable, source-bounded single-phase liquid property/enthalpy surface.

No network/storage, extrapolation, invented property window or phase-change EOS.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields
from itertools import pairwise

from core.dimension import PRESSURE, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from numerics.interpolation.linear import interpolate
from physics.exceptions import OutOfRangeError
from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.si import SPECIFIC_ENERGY

LIQUID_TABLE = ModelIdentity(
    model_id="PHYS-FLUID.bounded_liquid_property_surface",
    model_name="Source-bounded bilinear liquid property/enthalpy table",
    physical_domain="fluids",
    equations=("Property(T,P)=piecewise bilinear interpolation of an explicitly sourced liquid grid",
               "T(h,P)=inverse piecewise-linear monotone enthalpy at fixed pressure"),
    inputs=("T [K], P [Pa] or common-reference h [J/kg]", "immutable sourced subcooled liquid property grid"),
    outputs=("rho [kg/m3]", "h [J/kg]", "Cp [J/kg/K]", "mu [Pa*s]", "k [W/m/K]"),
    assumptions=("Single pure-fluid, common-reference, wholly liquid rectangular T/P domain below its declared lowest saturation temperature.",),
    validity_range="Only inside supplied axes; 2..129 temperature nodes,2..25 pressure nodes; no phase boundary crossing/extrapolation",
    required_properties=("rho,h,Cp,mu,k at every T/P node", "same-fluid/reference source", "declared liquid saturation bound"),
    source="Per-table explicit source/reference and retained raw-response SHA256; numerical interpolation is not an independent EOS.",
    verification_status="analytic bilinear fields, node/inverse consistency, dimensions and strict domain/data tests",
    limitations=("Not boiling, gas/supercritical/two-phase transport or metastable-liquid modeling.",
                 "Interpolation error requires independent off-grid source checks; no uncertainty is invented.",
                 "Interpolated Cp is a transport property, not an exact derivative of the piecewise-linear enthalpy surface."),
)


@dataclass(frozen=True, slots=True)
class LiquidState:
    density_kg_m3: float
    enthalpy_j_kg: float
    cp_j_kg_k: float
    viscosity_pa_s: float
    conductivity_w_m_k: float


@dataclass(frozen=True, slots=True)
class LiquidTable:
    fluid_id: str
    temperatures_k: tuple[float,...]
    pressures_pa: tuple[float,...]
    states: tuple[tuple[LiquidState,...],...]
    lowest_saturation_temperature_k: float
    source: str
    enthalpy_reference: str
    raw_sha256: tuple[str,...]

    def __post_init__(self):
        def real(v):return type(v) in {int,float} and math.isfinite(v)
        if (type(self.temperatures_k) is not tuple or type(self.pressures_pa) is not tuple
            or not 2<=len(self.temperatures_k)<=129 or not 2<=len(self.pressures_pa)<=25):
            raise InvalidInputError("Bounded immutable T/P axes with at least2 nodes each required; one cold point is not a property window")
        for axis in (self.temperatures_k,self.pressures_pa):
            if not all(real(v) and v>0 for v in axis) or any(b<=a for a,b in pairwise(axis)):
                raise InvalidInputError("Strictly increasing finite positive T/P axes required")
        if not real(self.lowest_saturation_temperature_k) or self.temperatures_k[-1]>=self.lowest_saturation_temperature_k:
            raise InvalidInputError("Entire table must remain strictly below a sourced lowest saturation temperature for the pressure interval")
        if any(type(v) is not str or not v.strip() for v in (self.fluid_id,self.source,self.enthalpy_reference)):
            raise InvalidInputError("Explicit fluid, property source and common enthalpy reference required")
        if (type(self.raw_sha256) is not tuple or not self.raw_sha256 or
            any(type(v) is not str or len(v)!=64 or set(v)-set("0123456789abcdef") for v in self.raw_sha256)):
            raise InvalidInputError("Retained raw source response SHA256 identities required")
        if type(self.states) is not tuple or len(self.states)!=len(self.temperatures_k):
            raise InvalidInputError("Exactly one immutable property row per temperature required")
        for row in self.states:
            if type(row) is not tuple or len(row)!=len(self.pressures_pa):raise InvalidInputError("Complete rectangular pressure columns required")
            for state in row:
                if type(state) is not LiquidState:raise InvalidInputError("Exact immutable SI liquid-state records required")
                for f in fields(LiquidState):
                    value=getattr(state,f.name)
                    if not real(value) or (f.name!="enthalpy_j_kg" and value<=0):
                        raise InvalidInputError("Finite positive SI transport/density/Cp and finite common-reference enthalpy required")
        for index in range(len(self.pressures_pa)):
            if any(b[index].enthalpy_j_kg<=a[index].enthalpy_j_kg for a,b in pairwise(self.states)):
                raise InvalidInputError("Liquid enthalpy must strictly increase with temperature at every pressure")

    def _pressure(self,pressure:Quantity)->float:
        value=as_si(pressure,PRESSURE,"liquid pressure")
        if not math.isfinite(value) or not self.pressures_pa[0]<=value<=self.pressures_pa[-1]:
            raise OutOfRangeError("Liquid pressure is outside the sourced property surface; no extrapolation")
        return value

    def evaluate(self,temperature:Quantity,pressure:Quantity)->LiquidState:
        t=as_si(temperature,TEMPERATURE,"liquid temperature");p=self._pressure(pressure)
        if not math.isfinite(t) or not self.temperatures_k[0]<=t<=self.temperatures_k[-1]:
            raise OutOfRangeError("Heated liquid temperature is outside the sourced subcooled property surface; no cold-value fallback")
        values=[]
        for f in fields(LiquidState):
            at_pressure=[interpolate(self.pressures_pa,[getattr(s,f.name) for s in row],p) for row in self.states]
            values.append(interpolate(self.temperatures_k,at_pressure,t))
        return LiquidState(*values)

    def temperature_for_enthalpy(self,enthalpy:Quantity,pressure:Quantity)->float:
        h=as_si(enthalpy,SPECIFIC_ENERGY,"liquid enthalpy");p=self._pressure(pressure)
        nodes=[interpolate(self.pressures_pa,[s.enthalpy_j_kg for s in row],p) for row in self.states]
        if not math.isfinite(h) or not nodes[0]<=h<=nodes[-1]:
            raise OutOfRangeError("Coolant enthalpy is outside the sourced liquid surface; phase change/extrapolation is unsupported")
        return interpolate(nodes,self.temperatures_k,h)
