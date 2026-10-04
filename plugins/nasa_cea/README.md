# NASA CEA adapter (`plugins/nasa_cea`)

Binds the modern PyPI package [`cea`](https://pypi.org/project/cea/) (NASA
Chemical Equilibrium with Applications, v3.3+) as a
`ThermochemistryEngine` for `physics.thermochemistry.cea_interface`.

Physics stays fail-closed and does **not** embed CEA. This adapter lives
outside `physics/` and returns SI `ThermochemicalResult` values only.

## Install

```bash
cd /path/to/COSMOS_0.1
pip install -r requirements-cea.txt
```

Requires Python ≥ 3.11.

## Use

```python
from physics.quantities import pascal
from physics.thermochemistry.cea_interface import CeaRequest, run_thermochemistry
from plugins.nasa_cea import bind_nasa_cea_engine

engine = bind_nasa_cea_engine()
result = run_thermochemistry(
    CeaRequest(
        fuel_id="LCH4",          # or CH4(L), methane, …
        oxidizer_id="LOX",       # or O2(L), O2, …
        mixture_ratio=2.7239,    # O/F by mass
        chamber_pressure=pascal(0.5e6),
    ),
    engine=engine,
)
print(result.chamber_temperature.to_si(), result.gamma, result.molar_mass.to_si())
```

Systems workflow:

```python
from systems.stages.thermochemistry import run_thermochemistry_stage
from plugins.nasa_cea import bind_nasa_cea_engine

run_thermochemistry_stage(design, engine=bind_nasa_cea_engine())
```

## Golden check (METHLOX-1.5Kn)

```bash
PYTHONPATH=. python scripts/smoke_nasa_cea_methalox.py
```

Expect chamber temperature ≈ 3093 K at Pc = 0.5 MPa, O/F = 2.7239
(matches the Desktop RPA `METHLOX-1.5Kn` case).

## Notes

- Species aliases are in `species_map.py`. Prefer `cea_species_name` values
  from the propellant registry when available (`CH4(L)`, `O2(L)`).
- Your archived `git-hub repo's/CEA` folder (CEA2 Fortran zips + RP-1311)
  remains the historical reference corpus; this adapter uses the modern
  `nasa/cea` Python package from PyPI.
