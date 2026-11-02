"""Build a user-supplied legacy CEA2 in isolation and cross-check the adapter.

No source/data are vendored or edited. This is software regression evidence,
not physical validation. Requires gfortran and optional requirements-cea.txt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from physics.quantities import pascal
from physics.thermochemistry.cea_interface import (
    CeaRequest,
    run_thermochemistry,
)
from plugins.nasa_cea import bind_nasa_cea_engine


def row(text: str, label: str) -> list[float]:
    line = next(line for line in text.splitlines() if line.strip().startswith(label))
    return [float(token) for token in re.findall(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?", line.split(label, 1)[1])]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True, help="Directory containing cea2.f, cea.inc, thermo.inp, trans.inp")
    args = parser.parse_args()
    source = args.source_dir.resolve(strict=True)
    files = ("cea2.f", "cea.inc", "thermo.inp", "trans.inp")
    for name in files:
        if not (source / name).is_file():
            raise SystemExit(f"Missing legacy input: {source / name}")
    compiler = shutil.which("gfortran")
    if compiler is None:
        raise SystemExit("gfortran is required; NASA Python runtime itself can use its prebuilt wheel.")
    with tempfile.TemporaryDirectory(prefix="cosmos-cea2-") as folder:
        build = Path(folder)
        for name in files:
            shutil.copy2(source / name, build / name)
        flags = []
        if sys.platform == "darwin":
            sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
            flags = [f"-Wl,-syslibroot,{sdk}"]
        subprocess.run([compiler, "-std=legacy", "-O2", *flags, "-o", str(build / "cea2"), "cea2.f"], cwd=build, check=True, timeout=60)
        for name in ("thermo", "trans"):
            subprocess.run([str(build / "cea2")], input=name + "\n", text=True, cwd=build, check=True, capture_output=True, timeout=30)
        comparisons = []
        for fuel, tf, ratio, pc, eps in (("CH4(L)", 111.67, 2.7239, 5e5, 10),
                                       ("H2(L)", 20.27, 5.55157, 53.3172e5, 25),
                                       ("RP-1", 298.15, 2.3, 5e6, 8)):
            deck = (f"problem rocket equilibrium o/f={ratio} p,bar={pc/1e5} supar={eps}\n"
                    f"reactants fuel={fuel} wt%=100 t,k={tf}\noxid=O2(L) wt%=100 t,k=90.17\n"
                    "output siunits transport\nend\n")
            (build / "check.inp").write_text(deck)
            subprocess.run([str(build / "cea2")], input="check\n", text=True, cwd=build, check=True, capture_output=True, timeout=30)
            text = (build / "check.out").read_text()
            native = run_thermochemistry(CeaRequest(fuel, "O2(L)", ratio, pascal(pc), expansion_ratio=eps),
                                        bind_nasa_cea_engine(fuel_temperature_k=tf, oxidizer_temperature_k=90.17))
            ref = {"Tc_K": row(text, "T, K")[0], "MW_kg_mol": row(text, "M, (1/n)")[0] / 1000,
                   "cstar_m_s": row(text, "CSTAR, M/SEC")[0], "exit_T_K": row(text, "T, K")[-1],
                   "exit_P_Pa": row(text, "P, BAR")[-1] * 1e5,
                   "chamber_k_frozen_W_m_K": row(text.split("WITH FROZEN REACTIONS", 1)[1], "CONDUCTIVITY")[0] * .1}
            modern = {"Tc_K": native.chamber_temperature.to_si(), "MW_kg_mol": native.molar_mass.to_si(),
                      "cstar_m_s": native.characteristic_velocity.to_si(), "exit_T_K": native.rocket_stations["exit"]["temperature_k"],
                      "exit_P_Pa": native.rocket_stations["exit"]["pressure_pa"],
                      "chamber_k_frozen_W_m_K": native.rocket_stations["chamber"]["conductivity_frozen_w_m_k"]}
            passed = all(math.isclose(modern[key], value, rel_tol=.003) for key, value in ref.items())
            comparisons.append({"fuel": fuel, "legacy": ref, "modern": modern, "relative_tolerance": .003, "pass": passed})
        report = {"kind": "SOFTWARE_REGRESSION_NOT_PHYSICAL_VALIDATION", "cea_version": "3.3.4",
                  "legacy_source_sha256": {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in files},
                  "comparisons": comparisons}
        print(json.dumps(report, indent=2, allow_nan=False))
        if not all(case["pass"] for case in comparisons):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
