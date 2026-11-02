# R06 — sensitivity and selected cycle/feed closure

Started2026-10-19, user request to start next phase. Frozen architecture, accepted R05 storage authority and actual checkout govern. No owner-data import/root switch, credential/trust change, commit/push/release or hardware operation authorized.

Owner explicitly approved: **pressure-fed first, then gas-generator**, in response to the steady, single-phase pressure-feed → gas-generator pump/turbine/power/diversion scope question. Staged-combustion, expander and electric-pump remain unsupported, not implicitly included. `UNSPECIFIED` remains refusal/intent, not a physical cycle.

1. **R06.1 sensitivity** (RKT-01): exact retained propulsion baseline; bounded explicit one-at-a-time sample values and centered finite-difference steps; existing model evaluation only; invalid points retained, no gap interpolation or false uncertainty claims. Persist original per-sample input/results/source hashes, dependency and failure records in R05 authority. Authenticated scoped API, draft-safe Projects controls and existing scientific plot/export UI. Test deterministic benchmark sensitivities, units, invalid domains, floating-point spacing, stale baselines, conflicts/replay, failure/restart, cross-user/project denial, actual UI and scientific-source parity. First slice declares its model/parameter/output scope; unsupported CEA/parameters are refused rather than assumed.
2. **R06.2 pressure-fed** (RKT-02/03/08): additive Physics contracts for declared steady single-phase incompressible feed/pressure/head balances with explicit losses/densities/operating conditions and separately declared regulated pressurant assumptions. No transient blowdown, cryogenic phase change, gas-dissolution/heat transfer, cavitation model or tank structural acceptance. First pin equations, units, reference fixtures/admissibility/tolerances in the accepted model record; independent balance tests precede integration. Shaft power is not fabricated for a pump-free cycle; not-applicable versus zero must be explicit.
3. **R06.3 gas-generator** (RKT-02/04/08): explicit pump head/efficiency, turbine inlet state/expansion/efficiency, shaft losses, hot-gas mass/energy and diverted fuel/oxidizer/core mixture accounting. Unknown component maps/thermal properties are unavailable, not hidden defaults. Declare independent residual closure and admissible solution, iteration/termination and reference fixtures before use. No preburner, expander or electric-pump promotion.
4. **R06.4 integrated qualification**: exact summaries/report/plots and selective downstream invalidation; independent verification of every declared balance; preserve existing CEA/subsystem results/preliminary mode; retain lack of physical validation and unsupported architectures. Whole R06 stays PARTIAL until all selected gates pass.

## Reuse / verified entry

`numerics/sensitivity/local.py:gradient` already implements centered differences; `parameter_scan.py:scan` requires valid arrays and sample statistics and is not a per-point invalid-domain recovery service. Reuse gradient, do not replace its formula. `systems/workflow/orchestrator.py:run_phase3_chain`, API `run_phase3`, Physics result DTOs and R05 `RecordPayload`/CAS/dependencies supply existing calculations and authority. `systems/cycle/models.py` and graph currently mark every cycle NOT_IMPLEMENTED; leave those truthful until a real integrated model is verified. `systems/visualization/plots.py` and ScientificChart/export components remain plotting authority.

Start with measured baseline tests and `entry.json` source identities. No AGENTS files found in checkout/ancestors. Existing dirty work belongs to the user. Full tests require exact CEA cache restore; native evidence campaigns require a fresh output destination, not a reused historical recorder.

## Primary cycle sources checked at entry

The following are reference candidates, not yet equation-by-equation model acceptance or experimental evidence:

- NASA-SP-125, Huzel/Huang,1967, [Design of Liquid Propellant Rocket Engines,2nd ed.](https://ntrs.nasa.gov/citations/19710019929), public US Government work. Feed/engine system design reference; exact equation/page mappings must be recorded before cycle implementation.
- Cannon,2010, [Liquid Propulsion: Propellant Feed System Design](https://ntrs.nasa.gov/citations/20100035254), NASA Marshall, document20100035254. Pressure-fed/pump-fed classifications; mathematical envelopes still require full source review.
- NASA-SP-8081,1972, [Liquid propellant gas generators](https://ntrs.nasa.gov/citations/19730018978), public US Government work. GG/turbine temperature/component limitations; not a performance map for a specific COSMOS engine.

No vendor engine maps, hardware measurements, validated material data or qualified review signatures are supplied by this approval. Preliminary software verification must not be called physical or production readiness.
