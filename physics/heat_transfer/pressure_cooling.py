"""Additive pressure-enthalpy-consistent coolant model; old model unchanged.

Incompressible h(T,p)=Cp*T+p/rho gives
  m*Cp*dT/ds = U*P*(Taw-T) - (m/rho)*dp/ds.
Each constant-property cell is integrated exactly, including frictional heat.
Geometry/correlation validity is reused from the existing channel model.
"""

from __future__ import annotations

import math
from dataclasses import replace

from physics.exceptions import OutOfRangeError
from physics.heat_transfer.regenerative import (
    CoolingEvaluation,
    CoolingInputs,
    GasWallStation,
    regenerative_cooling,
)


def pressure_coupled_cooling(stations: tuple[GasWallStation, ...], inputs: CoolingInputs) -> CoolingEvaluation:
    base = regenerative_cooling(stations, inputs)
    mass, cp, rho = inputs.mass_flow.to_si(), inputs.specific_heat.to_si(), inputs.density.to_si()
    temperature, pressure = inputs.inlet_temperature.to_si(), inputs.inlet_pressure.to_si()
    wall, kw = inputs.wall_thickness.to_si(), inputs.wall_conductivity.to_si()
    rows = []
    for segment in base.segments:
        hot = 2 * math.pi * segment.radius_m * segment.path_length_m
        cold = inputs.channel_count * inputs.channel_width.to_si() * segment.path_length_m
        hg, taw, loss = segment.gas_coefficient_w_m2_k, segment.gas_adiabatic_temperature_k, segment.pressure_loss_pa
        ua = hot / (1 / hg + wall / kw + hot / (cold * base.coolant_coefficient_w_m2_k))
        source_temperature = mass * loss / (rho * ua)
        rise = (taw + source_temperature - temperature) * -math.expm1(-ua / (mass * cp))
        heat = mass * cp * rise - mass * loss / rho
        flux = heat / hot
        peak_flux = ua / hot * (taw - temperature - rise)
        hot_wall, cold_wall = taw - flux / hg, taw - flux / hg - flux * wall / kw
        peak_hot = taw - peak_flux / hg
        peak_cold = peak_hot - peak_flux * wall / kw
        if (
            not all(math.isfinite(v) for v in (rise, heat, flux, peak_hot, peak_cold, pressure-loss))
            or heat <= 0 or temperature + rise >= taw
            or not inputs.min_temperature.to_si() <= temperature + rise <= inputs.max_temperature.to_si()
            or peak_cold > inputs.max_temperature.to_si()
            or peak_hot > inputs.max_wall_temperature.to_si()
            or pressure - loss <= inputs.max_vapour_pressure.to_si()
        ):
            raise OutOfRangeError("Pressure-coupled coolant exceeds heating/phase/property/wall window.")
        rows.append(replace(segment, coolant_in_temperature_k=temperature, coolant_out_temperature_k=temperature + rise,
                            coolant_out_pressure_pa=pressure-loss, hot_wall_temperature_k=hot_wall, cold_wall_temperature_k=cold_wall,
                            peak_hot_wall_temperature_k=peak_hot, peak_cold_wall_temperature_k=peak_cold, heat_flux_w_m2=flux, heat_w=heat))
        temperature += rise
        pressure -= loss
    total_heat = math.fsum(s.heat_w for s in rows)
    enthalpy_rise = cp * (temperature - inputs.inlet_temperature.to_si()) + (pressure - inputs.inlet_pressure.to_si()) / rho
    return replace(base, segments=tuple(rows), total_heat_w=total_heat, outlet_temperature_k=temperature, outlet_pressure_pa=pressure, energy_residual_w=total_heat-mass*enthalpy_rise)
