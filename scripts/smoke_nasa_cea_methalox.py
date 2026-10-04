#!/usr/bin/env python3
"""Golden smoke: nasa/cea vs METHLOX-1.5Kn RPA chamber temperature."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from physics.quantities import pascal
from physics.thermochemistry.cea_interface import CeaRequest, run_thermochemistry
from plugins.nasa_cea import bind_nasa_cea_engine

# RPA case METHLOX-1.5Kn
OF = 2.7239
PC_PA = 0.5e6
TC_RPA_K = 3093.3


def main() -> int:
    engine = bind_nasa_cea_engine()
    result = run_thermochemistry(
        CeaRequest(
            fuel_id="LCH4",
            oxidizer_id="LOX",
            mixture_ratio=OF,
            chamber_pressure=pascal(PC_PA),
            equilibrium=True,
            notes="METHLOX-1.5Kn golden smoke",
        ),
        engine=engine,
    )
    tc = result.chamber_temperature.to_si()
    mw = result.molar_mass.to_si()
    cstar = (
        None
        if result.characteristic_velocity is None
        else result.characteristic_velocity.to_si()
    )
    print(f"engine     : {result.engine_name}")
    print(f"Tc [K]     : {tc:.3f}  (RPA {TC_RPA_K})")
    print(f"gamma [-]  : {result.gamma:.6f}")
    print(f"MW [kg/mol]: {mw:.6f}  ({mw*1000:.3f} g/mol)")
    print(f"c* [m/s]   : {cstar:.3f}" if cstar is not None else "c* [m/s]   : None")
    delta = abs(tc - TC_RPA_K)
    print(f"|ΔTc|      : {delta:.3f} K")
    if delta > 15.0:
        print("FAIL: chamber temperature far from RPA golden case.")
        return 1
    print("PASS: within 15 K of RPA METHLOX-1.5Kn Tc.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
