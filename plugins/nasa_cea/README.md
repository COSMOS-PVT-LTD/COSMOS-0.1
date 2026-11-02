# NASA CEA adapter (`plugins/nasa_cea`)

Binds the modern PyPI package [`cea`](https://pypi.org/project/cea/) (NASA
Chemical Equilibrium with Applications, pinned v3.3.4) as a
`ThermochemistryEngine` for `physics.thermochemistry.cea_interface`.

Physics stays fail-closed and does **not** embed CEA. This adapter lives
outside `physics/` and returns SI `ThermochemicalResult` values only.

## Install

```bash
cd /path/to/COSMOS_0.1
.venv-remediation/bin/python -m pip install -r requirements-cea.txt
```

Requires Python ≥ 3.11 and NumPy 2.x. The official macOS arm64 wheel includes
the compiled Fortran engine and databases. This is an optional dependency:
missing or incompatible engines fail explicitly in CEA mode.

The local double-click app can be rebuilt with `bash scripts/build_macos_app.sh`.
Its launcher prefers `.venv-remediation/bin/python`, like `launch_cosmos.command`.
The app bundle is a local launcher, not a self-contained distributable.

## Workbench

On **00 Design Project** or **05 Thermochemistry**, select **NASA CEA 3.3.4 ·
equilibrium** and provide fuel/oxidizer inlet temperatures in kelvin. Supply
registered propellants, Pc, O/F, Ae/At > 1, positive throat area and ambient
pressure (explicit zero for vacuum). Save and run Phase 3. No assumed Tc/gamma/MW
are needed in CEA mode. The temperatures are not inferred from fuel names.
The adapter enforces NASA's reactant temperature ranges. Liquid/reactant-only
entries use tabulated reference enthalpy rather than a heated-liquid EOS model;
acceptance inside those ranges does not establish liquid phase/pressure validity
or model feed-temperature-dependent enthalpy. Qualified custom enthalpy and
fluid-property support remains future work.

The result includes chamber/throat/exit states, frozen and equilibrium gas
transport properties, chamber product mole fractions, c*, engine version,
reactant species/temperatures and database SHA-256 fingerprints. Full trace
species remain in the design JSON export. Gamma is CEA's isentropic exponent.

Performance uses CEA c* and exit states: mdot=Pc At/c*, then momentum/pressure
thrust and Isp. It does not replace CEA c* with a constant-gamma result. Assumed
mode remains a separate preliminary analysis; legacy saved designs are not
automatically promoted to CEA. Temperature/source changes invalidate downstream
results. Unavailable, non-convergent or malformed CEA output never falls back.

The workbench currently exposes **equilibrium / infinite-area combustor only**.
The standalone request's older `equilibrium=False` path freezes at the chamber,
but must converge at every requested station; some v3.3.4 frozen area-ratio
cases fail. Frozen/FAC workbench modes are not claimed or offered.

## Use

```python
from physics.quantities import pascal
from physics.thermochemistry.cea_interface import CeaRequest, run_thermochemistry
from plugins.nasa_cea import bind_nasa_cea_engine

engine = bind_nasa_cea_engine(
    fuel_temperature_k=111.67, oxidizer_temperature_k=90.17,
    require_explicit_temperatures=True,
)
result = run_thermochemistry(
    CeaRequest(
        fuel_id="LCH4",          # or CH4(L), methane, …
        oxidizer_id="LOX",       # or O2(L), O2, …
        mixture_ratio=2.7239,    # O/F by mass
        chamber_pressure=pascal(0.5e6),
        expansion_ratio=10.0,
    ),
    engine=engine,
)
print(result.chamber_temperature.to_si(), result.gamma, result.molar_mass.to_si())
```

Application workflow (persists mode and inlet state):

```python
from api.propulsion_workflow import run_phase3

run_phase3(design, throat_area_m2=0.001, thermochemistry_configuration={
    "mode": "nasa_cea", "fuel_temperature_k": 111.67,
    "oxidizer_temperature_k": 90.17,
})
```

## Software reference checks

```bash
.venv-remediation/bin/python scripts/smoke_nasa_cea_methalox.py
.venv-remediation/bin/python scripts/verify_cea_reference.py --source-dir "/Users/vaibhavkumarn/Desktop/COSMOS/git-hub repo's/CEA/Win Gui/CEA+Fortran"
```

The first is a secondary comparison with the recorded RPA `METHLOX-1.5Kn`
temperature (~3093 K), not physical validation. The second builds the provided
CEA2 source using gfortran in an isolated temporary directory, regenerates its
native databases and compares methalox, hydrolox and kerolox states and gas
conductivity. It leaves the supplied sources unchanged. Tests also check the
distributed NASA RP-1311 example 8 and the authenticated save/run/reload flow.

## Notes

- Species aliases are in `species_map.py`. Prefer `cea_species_name` values
  from the propellant registry when available (`CH4(L)`, `O2(L)`).
- Your archived `git-hub repo's/CEA` folder (CEA2 Fortran zips + RP-1311)
  is used as an independent software regression reference, not the runtime.
- Native calls are serialized because CEA has shared database/logging state.
- v3.3.4's conductivity labels are inconsistent: its numerical values satisfy
  `Pr = mu[mP] * Cp[kJ/(kg K)] / k`. The adapter uses conductivity ×0.1
  W/(m K), viscosity ×1e-4 Pa s, Cp ×1000 J/(kg K), pressure ×1e5 Pa,
  molecular weight /1000 kg/mol and Isp[m/s] /9.80665 s. Both the Prandtl
  identity and the independently compiled CEA2 transport output verify the
  conductivity conversion. No ambiguous raw units reach Systems.
- The dependency ships malformed type stubs; dynamic import is restricted to
  the native adapter. Typed Core/Physics/Systems contracts remain checked.
- NASA CEA and its data are supplied by the external dependency under
  [Apache-2.0](https://github.com/nasa/cea/blob/v3.3.4/LICENSE.txt), with
  [NASA attribution/data notices](https://github.com/nasa/cea/blob/v3.3.4/NOTICE.txt).
  No third-party source or database is copied into COSMOS. No NASA endorsement
  is implied.
- Ideal CEA performance is not hot-fire validation. Existing contour stations
  still use constant chamber gamma/Tc/MW; cooling still uses explicit constant
  gas/coolant properties and preliminary correlations. CEA transport data are
  available in the result, but not silently substituted into thermal inputs.
  Cycle power balance, injector stability, losses and hardware readiness remain
  outside this integration.
