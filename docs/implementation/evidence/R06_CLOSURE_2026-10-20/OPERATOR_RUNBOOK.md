# Use the selected solved operating model on the Mac

Use your normal launcher and existing configured application data root. Restart normally after source updates. Do not stop an unidentified listener, switch roots, enable a live migration or copy QA data into your project just to view the feature. The existing managed-project flag/membership controls still apply; flag-off mode retains original read access only.

1. Open **Projects & Mission** and select the managed project.
2. Save an explicit PRESSURE_FED or GAS_GENERATOR baseline. Generate its actual current divergent nozzle contour using the existing workflow. The new solver uses only its exact geometry, not the old assumed/adiabatic station state as the new solution. It does not overwrite the original design.
3. For regeneration, save explicit counterflow (`exit_to_throat`), no-film channel/wall geometry in the existing cooling configuration. New states/properties/heat are recalculated. No film injection or silent routing substitution is available in this solver.
4. Expand **Solved engine operating point — CEA / regenerative feedback**. Choose the exact saved baseline, cycle and cooling routing. Expand the grouped unit-labelled controls.
5. Supply explicit, independently sourced constant-property liquid reference/inlet states, property/phase windows, resistance characteristics, and for GG actual pump fit coefficients/windows, efficiencies, effective choked throat and turbine boundary. The software cannot invent component maps or establish their physical applicability. Reference reactant temperatures must be in the pinned NASA database range; heated feed enthalpy is separately accounted for, not simulated by extrapolating liquid database temperature.
6. Enter bounded initial guesses/scales, finite-difference/residual policy, explicit iteration/evaluation/time budgets, thermal policy and separate dimensional conservation tolerances. No numeric defaults are supplied. Solver tolerances are not measurement uncertainty or physical design acceptance. If prediction/property/characteristic evidence is unavailable, obtain qualified source data; do not copy the synthetic software fixture numbers.
7. Optionally paste **your explicit specification JSON** into the import control and apply it to fields for review. Wrong units, extra/missing fields or unsupported schema are refused, not silently normalized. Importing does not run or save a result. Strict server validation still governs the eventual command.
8. Click **Run and retain solved engine candidate**. Inputs are durably captured before the bounded calculation. Check execution, termination, convergence, independent conservation and physical-admissibility fields separately. Only a current converged/admissible/conservative result shows **CURRENT SOLVED CANDIDATE — declared model only**. Failed/exhausted runs retain originals/diagnostics without an active candidate.
9. Inspect actual solved pressures/flows/O/F and for GG speed/GG flows, regenerative heat/return state, all signed residuals and full original source. Display source-bound balance, Newton and thermal histories; use the dropdown to choose the actual history. Export raw residual CSV, original input/result JSON and plot CSV/SVG plus complete provenance/source companions. Keep companions with SVG; it is not a standalone validated artifact.
10. For uncertain network results, retry the same unchanged operation identity or its captured command. Do not invent new data or duplicate a request by discarding its identity silently. Explicitly abandon uncertain identity or discard local drafts only when intended. Retained server originals are not deleted.
11. CURRENT means matching retained baseline/method/runtime identities, not physical validation. Changing source or method can make older candidates historical while preserving their exact bytes. A candidate is not automatically installed into the frozen upstream design. New engineering inputs require an explicit new revision/command.

## Supported scope

Steady regulated-tank pressure-fed and open GG, single-phase constant-property liquids, explicitly bounded characteristic fits, NASA3.3.4 HP chemistry, adiabatic infinite-area chamber/convergent and cooled frozen calorically-perfect divergent quasi-1D nozzle, full-core-fuel counterflow. No shocks/separation, film mass injection, phase change, general CFD, transient startup, pressurant sizing or other cycle architectures. Hardware/experimental acceptance is not available through a success flag or endpoint.

## Reproduce local verification

From `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`:

```sh
.venv-release-p12/bin/python -m pytest -q tests/unit_tests/systems_layer/test_engine_operating.py tests/integration_tests/gui/test_engine_operating_http.py tests/unit_tests/physics/test_heated_nozzle.py tests/unit_tests/numerics/test_bounded_system.py
node --test tests/js/engine_operating.test.cjs
```

The selected model requires pinned `cea==3.3.4` from the existing `requirements-cea.txt`; no dependency was installed during this increment. The dedicated existing CI CEA job now includes these new tests. A normal environment without this optional runtime must explicitly skip native qualification and refuse actual model evaluation, never use an assumed-state fallback.

Full local qualification uses `.venv-release-p12/bin/python -m pytest -q`, `node --test tests/js/*.test.cjs`, the existing Ruff/Mypy CI target sets and seven existing strict TypeScript consumers. Protect `cache/cea/test_key.json` with a fresh temporary copy and EXIT-trap restore/`cmp`; full tests intentionally mutate it. Existing TypeScript5.9.3 executable: `/Users/vaibhavkumarn/.npm/_npx/69f9afb961c37556/node_modules/typescript/bin/tsc`, flags `--noEmit --strict --target ES2022 --module commonjs --moduleResolution node --lib ES2022,DOM`.

Actual GUI qualification server: `tests/ui/r06_operating/preview.py`, guarded fresh root `/private/tmp/cosmos-r06-operating-qa.YQvvwK`, port8873; `--resume` was used only for the exact root's restart. No successful solver record is seeded. It is synthetic software QA, not your engineering project. `check_exports.py` compares actual downloads against exact durable authority; `collect_r06_operating_evidence.py` records source preservation/test identities without rewriting older receipts. QA root/downloads are retained; task server/tab are closed after checks.
