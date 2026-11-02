# R08 operation and engine qualification inputs

## What the new workflow does

In Native Geometry Generator, open an exact CURRENT saved component model and expand **R08 · Engineering geometry qualification and interoperability**.

1. Prepare a blank policy. It intentionally contains no numerical engineering defaults. Complete its explicit SI JSON and sources, then save it **before capturing native builds**.
2. With that same saved model, explicitly capture an OCCT build and the three PicoGK builds at the spacings declared in the policy. Use the existing generator forms and explicit QA inputs. Do not edit/re-save the model between those captures. No automatic refinement is performed.
3. Select the exact policy, enter the analytic job ID and the three implicit job IDs in coarse/middle/fine order, then evaluate. For a genuinely analytic-only policy, explicitly declare no implicit spacings and no cross-representation requirement; it cannot claim PicoGK qualification.
4. Inspect the retained calculation, critical witnesses, direct discrepancy/outliers, original checksums, selections and refinement metrics. COMPLETED means the computation finished; the policy checks can still fail.
5. A different active project engineer must provide a genuine independent decision and explicit rationale/qualification/limitations/checks. The builder, policy author and evaluator cannot approve their own work. Do not create fictitious reviewer accounts to accept an engine.
6. Only a current accepted decision permits the guarded analysis handoff/original downloads. A later REJECT withdraws acceptance; its expected review head must match. Edits, failed/unresolved checks, cancellation and stale sources cannot inherit an old pass. Remap proposals never transfer acceptance automatically.

Unknown network outcomes retain their operation ID for exact retry. **Abandon R08 retry identity · keep draft** preserves text while explicitly abandoning that local retry identity. **Discard R08 drafts** clears local forms, not retained source/evidence. Save/discard drafts before changing model/project/evidence context.

## Policy contract

Authoritative parser: `systems/geometry/qualification_policy.py`. Permitted intended uses: `SOFTWARE_QUALIFICATION` or `GEOMETRY_ANALYSIS_PREPARATION`, not manufacturing/hot-fire approval. Unit system is `SI_m`. Every number must be a JSON number, not a string, Boolean, NaN or infinity.

- Each exact part: relative volume/area ceilings; independent reference area/source; centroid, bounds, source-residual, reverse and direct representation distance limits; explicit critical-feature witnesses.
- Critical kinds: `WALL_SPAN`, `CHANNEL_SPAN`, `PORT_DIAMETER`, `INTERFACE_SPAN`, `DIMENSION`. Supply two nominal world-coordinate surface endpoints, accepted span bounds, local surface-distance tolerance and source. This measures that declared local span, **not** a global minimum wall/channel dimension.
- Every material/fluid region: exact part ID, matching role, material label and applicability source. Labels do not create material properties or allowables.
- Named boundaries: whole-part labels or exact imported analytic semantic-face labels, with purpose/source. Ambiguous/missing labels prevent pass.
- Mesh intent: explicit minimum feature, cells across it, maximum edge/curvature target and cell budget/source. No actual volume mesh or solver is created.
- Sampling: explicit 16–2048 samples per part and 1–64 retained outliers per direction. The maximum/count still include all sampled errors even when the saved outlier list is bounded.
- Three distinct decreasing implicit spacings within the existing generator envelope. Fewer/missing attempts cannot pass a cross-representation policy. Certified mesh self-intersection requests fail closed because that certification is not implemented.

`tests/fixtures/geometry_qualification.py` contains a manufactured pipe policy/formula fixture for software testing only. **Do not copy its dimensions, tolerances or material declarations into the methalox engine as engineering approval.**

## Inputs still needed for the real engine

Before a real R08 engine acceptance, supply/approve:

1. Intended use: conceptual visualization, specified geometry-analysis preparation or another separately scoped use. A manufacturing purpose needs a separately qualified workflow.
2. Reference drawing/specification and per-part tolerance basis, with units, revision and applicability. Nominal CAD dimensions alone do not determine acceptable engineering error.
3. Critical locations and coverage: hot wall/ligaments; channel widths/depths and header connections; fuel/LOX port sizes and separating lands; flange mounting interfaces and blind groove envelopes; supply/return pipe interfaces. Identify source-bound local witness endpoints. Global minimum thickness, seal service fit and pressure integrity are not implied by local witnesses.
4. Independent area/dimension references appropriate to each part, and explicit material/fluid region labels/sources.
5. Named study boundaries and a feasible mesh/refinement plan. Split/select component qualification deliberately where whole-assembly studies exceed the preserved bounds; do not silently omit parts or relabel partial evidence as a full-engine pass.
6. Genuine independent authorized engineering review. No authentic engine acceptance was performed by the software tests.

## Running the isolated verification viewer

The checked viewer uses the **synthetic software-fixture store**, not the owner's engine data. Open:

`http://127.0.0.1:8899/app/workbench/native-geometry?project=c422fb23-3e9a-4d3a-bb97-67bda9c22500`

After reboot, check port ownership/free state first. Never kill an unidentified listener. Start only one server/coordinator per data root:

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
COSMOS_NEW_SHELL=1 COSMOS_DURABLE_PROJECTS=1 COSMOS_NGG=1 \
COSMOS_NGG_RUNTIME_CONFIG="$PWD/docs/implementation/evidence/PICOGK_COMPONENTS_2026-10-24/occt-runtime/runtime.json" \
COSMOS_PICOGK_COMPONENT_CONFIG="$PWD/docs/implementation/evidence/PICOGK_COMPONENTS_2026-10-24/pico-runtime-v4/runtime.json" \
COSMOS_GEOMETRY_QUALIFICATION_CONFIG="$PWD/docs/implementation/evidence/R08_2026-10-25/runtime-v4/runtime.json" \
.venv-release-p12/bin/python -c 'from gui.server import serve_application;serve_application("/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/output/r08-qualified-campaign-v4-2026-10-25/test_actual_r08_predeclaration0/state",host="127.0.0.1",port=8899)'
```

For the existing engine viewer, **do not** concurrently launch another server against its active root. Save edits and obtain approval before gracefully restarting its verified listener. Reuse its prior command/root/runtime settings and add the `COSMOS_GEOMETRY_QUALIFICATION_CONFIG` line above. No data migration is needed. Old exploratory builds remain historical evidence, not predeclared R08 acceptance.

## Qualification and preservation

New runtime issuance is append-only. `scripts/qualify_geometry_qa.py` requires passing unskipped unit, HTTP, actual governed two-kernel/three-resolution native evidence **and all 22 declared family campaigns** (`--families`). Do not edit/reseal a historical receipt or qualify changed code using stale test runs. Rerun applicable tests after source changes; receipts are trusted local operator records, not adversarial execution/credential certificates. Preserve failed/cancelled/historical attempts and their exact originals. No changes were made to the existing generator runtime admission or its accepted numerical limits.

The exact current report paths and profile SHA are in `CLOSEOUT_QUALIFICATION.md`
and `STATUS.json`. The source-bound nominal diagnostic and remaining real-engine
inputs are in `ENGINE_ACCEPTANCE_INPUTS.md`. Do not reuse its floating-point
formula agreement as a tolerance or transfer software-fixture limits to an engine.

If an older running backend lacks R08 routes, the new client now disables only
the R08 panel and preserves existing component tools. This is not automatic
permission to restart a viewer or point a second server at an active data root.
