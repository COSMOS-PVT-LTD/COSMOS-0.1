# COSMOS NASA CEA integration — 2026-10-08

## Implemented scope

NASA's official `cea==3.3.4` native Fortran/Python package is installed in the
local COSMOS Python 3.11 environment. The optional adapter is now connected to
the authenticated Phase 3 API and workbench. It computes equilibrium chamber,
throat and supersonic exit states from registered liquid propellants, explicit
reactant temperatures, Pc, O/F and expansion ratio. It returns composition,
Tc, isentropic gamma, MW, c*, frozen/equilibrium Cp, viscosity, conductivity and
Prandtl numbers in SI, plus source/version/reactant/database provenance.

`systems/configuration/thermochemistry.py` owns saved mode/temperature input
validation. Configuration edits are atomic and invalidate the thermochemistry
and dependent result/geometry cone. Legacy designs keep their historical
assumed mode. The GUI offers explicit CEA/assumed modes, saved temperatures,
ordered station tables and a chamber composition disclosure. Full trace species
and database hashes survive save/reload, cloning and design JSON export.

`physics/compressible_flow/external_nozzle.py` scales a converged CEA solution
using Pc, At and ambient pressure; it is not a new equilibrium solver. Systems
performance consumes CURRENT CEA exit states and preserves its c*. The old
calorically perfect performance path remains only for assumed analysis. All
native calls are serialized. Incomplete/non-convergent solutions, invalid SI
dimensions, nonfinite values and malformed composition are rejected. There is
no automatic assumption fallback on engine failure. Reactant temperatures must
be within NASA's reported database ranges. Liquid/reactant-only species use
tabulated reference enthalpy; these entries are not heated-liquid EOS models,
and range acceptance does not establish liquid phase/pressure validity.

The authenticated endpoint remains `POST /api/propulsion/designs/<id>/run/phase3`:

```json
{
  "thermochemistry_configuration": {
    "mode": "nasa_cea",
    "fuel_temperature_k": 111.67,
    "oxidizer_temperature_k": 90.17
  },
  "throat_area_m2": 0.001,
  "expansion_ratio": 10
}
```

The existing design must have propellants, Pc, O/F and ambient pressure.
Reactant temperatures are not propellant defaults in workbench execution.
CEA mode rejects simultaneous assumed Tc/gamma/MW. Supported UI chemistry is
equilibrium with an infinite-area combustor, not frozen expansion or FAC.

## Supplied repository assessment and reuse

The requested `githubrepos` directory was found under its actual name
`Desktop/COSMOS/git-hub repo's`. CEA's `Win Gui/CEA+Fortran` source and databases
were useful: they were built locally using gfortran 14.1.0 as a regression
reference. Windows executables/Java GUI were not used as the macOS runtime.
Sources and input databases were not modified or vendored.

The official maintained NASA dependency was selected as the runtime because it
already has an optional COSMOS adapter, a direct native Python API, macOS arm64
wheels and source/data licensing. Reference:
[NASA CEA repository](https://github.com/nasa/cea/tree/v3.3.4),
[NASA installation/API documentation](https://nasa.github.io/cea/interfaces/python_api.html).

The README files for proptools, Bamboo, LPREpy, RocketSolver and the MATLAB
regenerative engine tool were inspected for relevance. They provide preliminary
equations, cooling/contour models or solid-motor assumptions, not a required
replacement for this thermochemistry boundary. CEAM/MATLAB/Windows archives,
T-MATS, aero, radio/control and 3D nozzle projects were inventoried but were not
deeply qualified or integrated in this CEA task. Importing unrelated or
unqualified model packages would not improve the scoped CEA integration.

NASA CEA's [Apache-2.0 license](https://github.com/nasa/cea/blob/v3.3.4/LICENSE.txt)
and [notices](https://github.com/nasa/cea/blob/v3.3.4/NOTICE.txt) remain with the
external dependency. This integration does not assert NASA endorsement.

## Verification evidence

The user-supplied CEA2 source was compiled with:

```sh
.venv-remediation/bin/python scripts/verify_cea_reference.py --source-dir "/Users/vaibhavkumarn/Desktop/COSMOS/git-hub repo's/CEA/Win Gui/CEA+Fortran"
```

This command builds and regenerates `thermo.lib`/`trans.lib` in temporary storage,
then executes real CEA2 and real NASA CEA 3.3.4. No mocked values enter these
reference comparisons. All six compared quantities per case passed the declared
relative tolerance of 0.3% (legacy output includes rounded values):

| Case | Pc / O/F / Ae/At | CEA2 Tc [K] | CEA 3.3.4 Tc [K] | CEA2 c* [m/s] | CEA 3.3.4 c* [m/s] |
|---|---|---:|---:|---:|---:|
| LOX/LCH4, 90.17/111.67 K | 5 bar / 2.7239 / 10 | 3093.34 | 3093.338429 | 1832.2 | 1832.209565 |
| LOX/LH2, 90.17/20.27 K | 53.3172 bar / 5.55157 / 25 | 3383.84 | 3383.844614 | 2332.3 | 2332.335804 |
| LOX/RP-1, 90.17/298.15 K | 50 bar / 2.3 / 8 | 3534.66 | 3534.659048 | 1802.3 | 1802.278785 |

MW, exit pressure/temperature and frozen chamber conductivity also matched.
The independent CEA2 transport comparison confirms conductivity ×0.1 in SI
despite inconsistent upstream API labels. Every returned station also passes
the Prandtl identity check. Solver version and binary database hashes are stored
per result; the reproducible reference script prints legacy source/data hashes.

NASA RP-1311 example 8 is covered separately by a native hydrolox regression.
The recorded RPA smoke example is secondary evidence, not an independent
physical validation dataset.

Local software gates: 2234 Python tests passed, 5 unrelated tests skipped;
23 JavaScript tests passed; Ruff passed all configured source/test/tool targets;
Mypy passed 318 source files; JS syntax and diff whitespace checks passed.
Authenticated native CEA API execution, failure rejection and export freshness
were tested. Browser verification checked explicit configuration save,
Phase 3 execution, ordered SI station display, saved-result reload, input-change
invalidation, persisted expansion-ratio edits and out-of-range inlet rejection in an
isolated temporary design store, not the user's actual design data.

`bash scripts/build_macos_app.sh` rebuilt `dist/COSMOS 0.1.app` and its Info.plist
passed `plutil -lint`. The launcher selects the CEA-enabled local venv. The icon
conversion now explicitly emits PNG before generating ICNS. This bundle relies
on this local checkout/venv; a standalone redistributable application is not
claimed. Requirements pass `pip check`.

A separate native CEA CI job was added to `.github/workflows/ci.yml`; existing
core jobs do not need the optional engine. CI configuration is implemented, but
no hosted GitHub run or publishing is claimed in this local task.

## Engineering limits

Software agreement is not zero error, physical validation or hardware readiness.
CEA performance here is ideal, adiabatic, one-dimensional attached equilibrium
flow: no combustion efficiency, injector atomization/stability, finite-rate
chemistry, viscous/divergence losses, flow separation or cycle closure.
Ambient pressure at/above Pc and non-positive ideal net thrust are rejected.
Overexpanded cases with positive ideal thrust are explicitly marked as having
UNKNOWN attached-flow applicability; no shock/separation prediction is implied.

The existing generated bell contour's station profiles are still a separate
constant-chamber-gamma approximation; they are explicitly NOT CEA equilibrium
station profiles and can differ from the CEA performance exit. Regenerative/film
cooling still needs explicit gas/coolant properties, validity windows and source
data. CEA transport output is not silently substituted into those fields, and
does not supply liquid coolant density or a two-phase property model. Cycle power
balance remains deferred. `CURRENT` means freshness; validation remains
`NOT_CLAIMED`.
