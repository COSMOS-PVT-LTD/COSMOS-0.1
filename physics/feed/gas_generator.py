"""Steady design-point GG power feedback, not a turbomachinery map solver."""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.dimension import DENSITY, MASS_FLOW_RATE, POWER, PRESSURE, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from physics.feed.pressure_fed import _si
from physics.model import ModelIdentity
from physics.si import SPECIFIC_HEAT

GAS_GENERATOR = ModelIdentity(
    model_id="PHYS.feed.open_gas_generator",
    model_name="Steady single-shaft open GG design-point balance",
    physical_domain="feed",
    equations=(
        "wp=dp/(rho*eta_p)",
        "wt=eta_t*cp*Tt*(1-(Pt_out/Pt_in)^((gamma-1)/gamma))",
        "mGG=(sum(base_i*wp_i)+aux)/(eta_shaft*wt-sum(GG_fraction_i*wp_i))",
    ),
    inputs=(
        "liquid pump boundaries [SI]",
        "gas total state [SI]",
        "explicit efficiencies and GG O/F",
    ),
    outputs=(
        "GG mass flow [kg/s]",
        "pump and turbine shaft power [W]",
        "signed shaft residual [W]",
    ),
    assumptions=(
        "Steady single-shaft open cycle; incompressible liquid, constant-property ideal turbine gas.",
        "Fixed design-point pressures and efficiencies; all GG propellant also crosses its pump.",
        "Core and external branch flows are imposed; no speed/map/network operating-point solution.",
    ),
    validity_range="Positive finite flows, density and total states; 0<efficiencies<=1; gamma>1; expanding turbine; feasible positive feedback denominator.",
    source="NASA Glenn Power Turbine Thermodynamics https://www.grc.nasa.gov/WWW/K-12/airplane/powtrbth.html ; DOE-HDBK-1012/3-92 HT-03 continuity and extended Bernoulli, pp9-11,25,47-49 https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL3.pdf",
    verification_status="independent affine feedback/energy fixtures; software verification only",
    limitations=(
        "Explicit properties/efficiencies are not qualified component maps or combustion calculations.",
        "No cavitation, startup, phase transition, shaft speed, bearing life or hardware acceptance.",
        "No experimental validation, production or flight readiness.",
    ),
)


def efficiency(value: float, name: str) -> float:
    if (
        type(value) not in {int, float}
        or not math.isfinite(value)
        or not 0 < value <= 1
    ):
        raise InvalidInputError(f"{name} must be finite and in (0,1].")
    return float(value)


@dataclass(frozen=True, slots=True)
class LiquidPump:
    density: Quantity
    inlet_pressure: Quantity
    outlet_pressure: Quantity
    efficiency: float

    def specific_work(self) -> float:
        rho = _si(self.density, DENSITY, "pump density", positive=True)
        pin = _si(self.inlet_pressure, PRESSURE, "pump inlet", positive=True)
        pout = _si(self.outlet_pressure, PRESSURE, "pump outlet", positive=True)
        eta = efficiency(self.efficiency, "pump efficiency")
        value = (pout - pin) / rho / eta
        if not math.isfinite(value) or value <= 0:
            raise InvalidInputError(
                "Pump requires a finite positive pressure rise/specific shaft work."
            )
        return value


@dataclass(frozen=True, slots=True)
class Turbine:
    inlet_total_temperature: Quantity
    inlet_total_pressure: Quantity
    outlet_total_pressure: Quantity
    specific_heat: Quantity
    gamma: float
    efficiency: float
    shaft_efficiency: float

    def evaluate(self) -> tuple[float, float]:
        temp = _si(
            self.inlet_total_temperature, TEMPERATURE, "turbine Tt", positive=True
        )
        pin = _si(self.inlet_total_pressure, PRESSURE, "turbine Pt in", positive=True)
        pout = _si(
            self.outlet_total_pressure, PRESSURE, "turbine Pt out", positive=True
        )
        cp = _si(self.specific_heat, SPECIFIC_HEAT, "gas cp", positive=True)
        eta = efficiency(self.efficiency, "turbine efficiency")
        efficiency(self.shaft_efficiency, "shaft efficiency")
        if (
            type(self.gamma) not in {int, float}
            or not math.isfinite(self.gamma)
            or self.gamma <= 1
            or pout >= pin
        ):
            raise InvalidInputError("Require finite gamma>1 and Pt_out<Pt_in.")
        # log differences and expm1 retain resolution for near-unity ratios.
        exponent = ((self.gamma - 1) / self.gamma) * (math.log(pout) - math.log(pin))
        work = eta * cp * temp * -math.expm1(exponent)
        outlet = temp - work / cp
        if (
            not math.isfinite(work)
            or work <= 0
            or not math.isfinite(outlet)
            or outlet <= 0
        ):
            raise InvalidInputError(
                "Turbine work/exit temperature is not finite and positive."
            )
        return work, outlet


@dataclass(frozen=True, slots=True)
class PowerBalance:
    gg_mass_flow_kg_s: float
    gg_oxidizer_flow_kg_s: float
    gg_fuel_flow_kg_s: float
    oxidizer_pump_flow_kg_s: float
    fuel_pump_flow_kg_s: float
    oxidizer_pump_power_w: float
    fuel_pump_power_w: float
    turbine_power_w: float
    delivered_shaft_power_w: float
    shaft_loss_w: float
    auxiliary_power_w: float
    shaft_residual_w: float
    turbine_outlet_total_temperature_k: float
    turbine_energy_residual_w: float
    feedback_denominator_j_kg: float
    termination: str = "DIRECT_AFFINE"
    iterations: int = 0


def solve_power_balance(
    *,
    oxidizer_base_flow: Quantity,
    fuel_base_flow: Quantity,
    oxidizer_pump: LiquidPump,
    fuel_pump: LiquidPump,
    turbine: Turbine,
    gg_mixture_ratio: float,
    auxiliary_power: Quantity,
    maximum_gg_flow: Quantity,
) -> PowerBalance:
    """Solve GG pump feedback analytically, then independently evaluate residuals."""
    ox = _si(oxidizer_base_flow, MASS_FLOW_RATE, "oxidizer base", positive=True)
    fuel = _si(fuel_base_flow, MASS_FLOW_RATE, "fuel base", positive=True)
    aux = _si(auxiliary_power, POWER, "auxiliary power", nonnegative=True)
    limit = _si(maximum_gg_flow, MASS_FLOW_RATE, "GG flow limit", positive=True)
    if (
        type(gg_mixture_ratio) not in {int, float}
        or not math.isfinite(gg_mixture_ratio)
        or gg_mixture_ratio <= 0
    ):
        raise InvalidInputError("GG O/F must be finite and positive.")
    wf, wo = fuel_pump.specific_work(), oxidizer_pump.specific_work()
    wt, tout = turbine.evaluate()
    af = 1 / (1 + gg_mixture_ratio)
    ao = gg_mixture_ratio / (1 + gg_mixture_ratio)
    denominator = math.fsum((turbine.shaft_efficiency * wt, -ao * wo, -af * wf))
    if not math.isfinite(denominator) or denominator <= 0:
        raise InvalidInputError(
            "INFEASIBLE_POWER_FEEDBACK: turbine cannot power its own GG pump demand."
        )
    flow = math.fsum((ox * wo, fuel * wf, aux)) / denominator
    if not math.isfinite(flow) or not 0 < flow <= limit:
        raise InvalidInputError(
            "INFEASIBLE_GG_FLOW: positive solution exceeds the explicit GG mass-flow limit or finite range."
        )
    go, gf = flow * ao, flow * af
    mo, mf = ox + go, fuel + gf
    po, pf, pt = mo * wo, mf * wf, flow * wt
    delivered = pt * turbine.shaft_efficiency
    residual = math.fsum((delivered, -po, -pf, -aux))
    cp = _si(turbine.specific_heat, SPECIFIC_HEAT, "gas cp", positive=True)
    tin = _si(turbine.inlet_total_temperature, TEMPERATURE, "Tt in", positive=True)
    energy = math.fsum((flow * cp * (tin - tout), -pt))
    values = (go, gf, mo, mf, po, pf, pt, delivered, residual, energy)
    if (
        not all(math.isfinite(value) for value in values)
        or min(go, gf, po, pf, pt) <= 0
    ):
        raise InvalidInputError(
            "Gas-generator result overflows or underflows finite positive flow/work."
        )
    return PowerBalance(
        flow,
        go,
        gf,
        mo,
        mf,
        po,
        pf,
        pt,
        delivered,
        pt - delivered,
        aux,
        residual,
        tout,
        energy,
        denominator,
    )
