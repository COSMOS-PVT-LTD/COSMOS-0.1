# Developer entry point - not a GUI or managed publication

From the repository's existing Python environment:

```python
from api.pressure_fed import assess_pressure_fed

# design: existing PropulsionDesign with explicitly selected PRESSURE_FED and
# CURRENT retained assumed-state operating-point/propellant/thermo/performance.
# specification: complete explicit SI/source specification, not inferred defaults.
envelope = assess_pressure_fed(design, specification)
result = envelope["result"]
```

The callable changes neither argument, saves nothing and activates no stage. Errors use the existing COSMOS input/insufficient-data/out-of-range contracts; no success-shaped fallback is returned. Exact schema/units/assumptions are documented in `MODEL_CONTRACT.md`. `example-input.json` illustrates shape with **synthetic software-verification constants only**; do not apply its values to a real engine. `example-result.json` retains the actual example and complete consumed canonical source/hash/method identities.

Inspect independent fuel/oxidizer `mass_residual_kg_s`, `pressure_residual_pa`, `pressure_state` and overall `assessment_balances_closed_within_declared_tolerances`. A surplus is explicitly not closure at imposed flow. Even when those algebraic checks pass, `workflow_cycle_complete` is false, shaft power is NOT_APPLICABLE/null, scientific applicability UNKNOWN and physical validation NOT_PERFORMED. The tank boundary does not size or certify pressurant hardware.

No HTTP endpoint or GUI control is introduced. Future publication must use the accepted managed project authority with same-project baseline capture, original result retention and qualified draft-safe UI. Do not wire this developer API into an ad-hoc unauthenticated route or store its unattached result under the upstream workflow cycle node.
