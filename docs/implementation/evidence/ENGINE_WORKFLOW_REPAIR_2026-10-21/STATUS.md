# Engine workflow repair and approved cold-study status

Latest connected-engine checkpoint: `CONNECTED_ENGINE_CURRENT_STATUS.md`.
It supersedes older capability/test counts below without rewriting their
historical evidence.12-body injector/cooling-header candidate and new bounded
thermal/feed/joint kernels are implemented; the full matched engine goal is
**not complete**. Material research proposal: `LPBF_HIP_MATERIAL_DATA_PROPOSAL.md`.

2026-10-21. Existing checkout `293223ebef190eaa647e67dc581eb186b2b5d987`
plus preserved uncommitted work. No commit, push, migration or release performed.
**Full engine / accurate calculated native CAD goal remains ACTIVE; R08 HOLD.**

## What changed

1. `systems/configuration/analysis.py`, `subsystems.py`: explicit engineering
   inputs persist separately from replaceable calculation outputs. No guessed
   material, wall temperature or coolant domain is installed.
2. `systems/workflow/analysis.py`, `api/propulsion_workflow.py`,
   `api/project_authority.py`, `gui/server.py`: one captured `/run/analysis` command
   executes independent ready stages and produces named missing-input/dependency
   requests. Invalid specified inputs still fail; missing inputs are not treated
   as a failed numerical solve. Summary/consistency/review are retained even when
   sibling stages are incomplete. CAS/replay/source history remain enforced.
3. `gui/static/propulsion-suite.js`, `cosmos-api.js`: Run/Recalculate uses that
   command. Separate model coverage, calculation state, source freshness and next
   action are displayed. Existing selected-cycle and operating-point editors are
   mounted in Engine Cycle; no duplicate browser physics or circular graph.
   Optional empty target comparison no longer crashes the inspector. Embedded
   drafts block workspace/baseline changes and participate in unload/shell guards.
4. `systems/cycle/models.py`, workflow graph/orchestrator: pressure-fed / GG models
   are available **PARTIAL**, rather than globally NOT_IMPLEMENTED. Selection is
   still not a solved balance. A new explicit analysis acknowledges the existing
   design identity without fabricating a numerical identity-stage result.
5. `systems/stages/thermal.py`: explicitly selected CURRENT CEA chamber frozen-
   composition transport has result-ID/engine provenance. This is not a remedy
   for the separate frozen-expansion failure. Wall temperature remains explicit.
6. `physics/solid_mechanics/pressure_vessels.py`, `systems/stages/structure.py`:
   explicitly selectable closed-end elastic Lamé pressure model; original thin-
   wall model retained. No automatic out-of-range fallback. Radial/hoop/axial and
   bore von Mises stress; governing ratio used by `consistency.py`. No material
   range or external-pressure buckling waiver. See the model contract here.
7. `systems/stages/consistency.py`: required dependency flags are Boolean, not
   the string `"false"`; actual missing required sources can no longer be skipped.

## Approved case and preservation

Original project `01cd79e6-3923-4eca-ae1f-544cc30d8901`, design
`6524df5d-46f9-5b74-b214-8f5ada56acf6`, r18, saved v4,
commit `638d6ea3-4057-4b90-8dd4-8fc956b4772d` is preserved unchanged at the
post-install comparison. Source hash:
`7504cf9bf0b6371ea9af5228df5b0587dd8b32e08247c2b20d1c88860d977bcf`.

The approved study is a separate managed design in that project:
`538a39dc-34c8-5261-a93c-933e43983960`, labelled
**Methalox 1.5 kN · approved cold study · NOT hardware ready**.
Initial approved analysis: r4, saved v3,
commit `f2a11b28-fd3f-4bd6-b6f5-ed459699fb60`.
Later GUI recalculations are new retained revisions, not overwrites of these bytes.

Approved: duration5s, imposed regulated source8bar absolute each, injector drop1bar
each, assumed Cd0.70, 8 ports each; GRCop-42 / INCONEL718 are **candidates only**.
NIST cold injector properties are separately sourced at Pc+drop=6bar; 8bar source
rows remain separate. Both cold states are explicitly liquid. NIST values are
reference-fluid calculations, not engine measurements or a heated-fluid window.

The current ideal CEA core flows give fuel/oxidizer hydraulic diameters about
2.2662 / 2.8695mm under those cold assumptions. Mass split residual is zero in
this calculation. These are conditional model outputs, not fabrication guidance,
atomization/stability acceptance or a CAD qualification. Old equal-hole CAD does
not represent them and has not been silently replaced.

Retained local outputs (repository-relative, intentionally ignored runtime data):

- `output/engine-goal-2026-10-21-v1/`: exact original envelope and isolated normal
  analysis qualification; original content unchanged at that check.
- `output/methalox-input-proposal-2026-10-21-v1/`: original draft and raw8bar data.
- `output/methalox-approved-study-2026-10-21-v1/`: approval-bound input document,
  raw6/8bar TSV, URLs/SHA256, isolated-install and viewer-install original/clone/
  input/analysis envelopes and preservation comparisons.
- `scripts/prepare_approved_methalox_study.py` never opens application storage.
  `scripts/apply_approved_methalox_study.py` requires a matching source commit,
  source basis, unchanged approval record and raw-property hashes, and creates a
  labelled clone through the normal managed HTTP/CAS route. It never overwrites
  the original or supplies missing thermal/material/feed data.

## Verification

- Python targeted regression: **667 passed**, 44.71s. Scope:
  `tests/unit_tests/systems_layer`, `tests/unit_tests/api`,
  `test_lame_cylinder.py`, `test_materials_and_solids.py`, and managed project /
  design-analysis HTTP integration tests. Not a full repository test claim.
- JavaScript: **433 passed**, all `tests/js/*.test.cjs`.
- Mypy: success on9 focused production source files; scoped Ruff and JS syntax
  checks pass. `git diff --check` on edited tracked production paths passes.
- Lamé tests independently cover traction, radial equilibrium, end force,
  hydrostatic invariance, equivalent stress, pressure scaling, thin-wall limit,
  dimensions, invalid inputs, persisted explicit selection, material-range and
  buckling rejection. Synthetic material fixtures are not this engine's liner.
- Existing qualified native runtime still verifies164 manifest identities. No
  component native implementation or old receipt was rewritten; this is an
  integrity check, **not** a fresh STEP/STL campaign for the new engine inputs.
- Protected `cache/cea/test_key.json` hash remains
  `6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`.
- Browser verification follows UI → API → managed capture/source → response.
  The first discovered inspector error was fixed before continuing. Final GUI
  evidence and exact post-recalculation identity are recorded below.

## Still required (not hidden by this repair)

Frozen-CEA failure diagnosis; sourced heated cryogenic property/phase domain;
process/condition-specific material properties; full chamber/convergent/nozzle
cooling and ligament/thermal structure; meaningful feed losses/controls and
source-current operating solve; current assessed evidence in overall review;
distinct-propellant injector CAD and feed routing; matching cooling CAD and
analysis topology; manifolds/interfaces/joints/plumbing; new native QA/export
campaign; measured experimental evidence and qualified review. Existing numerical
or CAD tests do not establish engine physical accuracy or hardware readiness.

## Subsequent completed software units — same date

- Frozen CEA transport failure is now resolved for the qualified study domain by
  an explicit full-product-reference / exact-zero-species transport adapter. No
  positive trace species are pruned. No vendor or version substitution. All325
  fresh scheduled equilibrium/frozen study points converged; the equilibrium O/F
  remains2.633. Historical errors remain intact. Contract and limits:
  `FROZEN_CEA_CONTRACT.md`; artifacts:
  `output/methalox-frozen-requalification-2026-10-21-v1/`.
- Added source-bound `injector.biprop_doublet`, distinct fuel/oxidizer bore
  radii/roles/STEP semantics, normal API seed and managed source-binding guards.
  Existing equal-radius families remain available. Source changes invalidate
  downstream CAD; independent radius edits cannot claim hydraulic coupling.
- New append-only native campaign **engine-v4**:22 component tests,7 component
  HTTP tests,7 preserved nozzle native/HTTP tests,31 preserved native fixtures;
  **67 passed, zero failures/skips**. New164-identity manifest:
  `docs/implementation/evidence/R07_COMPONENTS_2026-10-20/runtime-qualified-engine-v4.json`.
  The v3 receipt is unchanged, but is historical for the changed methods.
- Updated focused Python regression **705 passed** (47.65s), JS **433 passed**;
  adapter/component focused Mypy and Ruff pass. New tests include full-reference
  mismatch, positive-trace removal rejection and real source-binding/staleness.
- A new native assembly built through the actual managed API is **COMPLETED**,
  source-current and software-QA passing. Baseline remains approved-study r12,
  saved v6 commit `fe1fd666-53ea-4f3c-a909-af5c4c34a54b`. Model
  `2f5d2e83-b35f-5c86-9b80-132b84ae41ac`, commit
  `94be60a1-85a4-411f-ae1c-200c5141445a`; job
  `3ff256e2-e645-4a9a-9ec5-946a0ca815a9`.
- Assembly:8 actual bodies,82,164 triangles, STEP/STL/topology/semantic mapping
  pass. STEP-to-analytic relative volume error for injector about1e-13;8 fuel and
  8 oxidizer bore semantics survive STEP import. This is software geometry
  fidelity, **not physical accuracy or manufacturing approval**. Cooling remains
  explicitly illustrative. Missing feed manifolds/seals/thermal sizing are not
  disguised as completed engine hardware.
- Original r18 remains unchanged at the post-install verification. Owner data
  was not migrated. Viewer8878 uses the new qualified runtime. The user's open
  native tab was preserved; separate GUI verification rendered the exact new
  retained candidate and a coolant domain. Evidence screenshots:
  `SOURCE_BOUND_ASSEMBLY_GUI.png`, `ILLUSTRATIVE_COOLANT_DOMAIN_GUI.png`.

Native artifacts, exact specification, captured baseline, retained inputs,
reference/STEP/STL QA, hashes and identities:
`output/methalox-source-bound-components-2026-10-21-v1/`.

The older “Still required” list above is superseded for frozen transport and
distinct-propellant bore coupling only. Source-specific hot materials, heated
fluid/phase domain, matched full thermal/cooling/structure, feed/operating-point
closure, manifolds/interfaces and experimental validation remain open. **Goal
ACTIVE; R08 HOLD.** Primary material-data inspection is the next current task;
candidate names are not converted into allowables.

## Latest checkpoint - exact sector handoff and sourced liquid energy threshold

- Added pure Physics axial annular-sector geometry and bulk-saturation enthalpy
  threshold models, each with explicit identity, equations, dimensional/domain
  checks, assumptions and limitations. Neither is a new empirical cooling or
  physical-validation claim.
- Added read-only Systems/API/GUI saved-component cooling inspection. Exact
  areas/perimeters, 4A/P, centroid, piecewise-linear volume and lateral surfaces
  are retained with model/baseline commits and analysis-source hashes. Stale
  loaded methods cannot claim newly edited on-disk hashes. Historical sources
  remain inspectable, local drafts cannot masquerade as the saved source, and
  sector-to-rectangular thermal mapping is explicitly unsupported.
- The actual approved-study assembly has6 passages, axial-plane Dh
  3.224920872-3.760539208mm, void volume36.222673063cm3. Independent CAD-reference
  volume agreement, analytic limits, numerical quadrature, dimensions, scaling,
  rigid placement and no-exported-fluid cases pass.
- Current scientific artifacts:
  `output/methalox-thermal-envelope-2026-10-21-v3/`. Retained NIST common-reference
  inlet/saturated-liquid enthalpies yield nominal bulk-saturation thresholds
  17.946/20.606/22.995/25.179kW at5/6/7/8bar. No live thermal/material inputs were
  installed. These are not safe heat loads, gas-side loads, wall-boiling limits
  or a completed engine/cooling solution. Source/limitations/remaining sequence:
  `THERMAL_MATERIAL_FEASIBILITY.md`.
- Latest broad focused Python regression: **1046 passed in43.05s**. Scope:
  `tests/unit_tests/{physics,systems_layer,api,plugins,core}` plus
  `test_component_cooling_http.py`, `test_design_analysis_http.py` and
  `test_project_authority_http.py`. This is not all repository integrations or
  remote CI. The first combined run exposed5 pre-existing test registry-namespace
  leaks after Core isolation; the managed HTTP tests now use the same isolated
  catalog fixture as other managed scientific tests. No production alias guard
  or scientific assertion was weakened. All original tests were retained.
- The39 new focused section/energy/source/parser/HTTP checks pass. JavaScript
  **434 passed**, all `tests/js/*.test.cjs`; Mypy6 focused production files and
  scoped Ruff/JS syntax pass. Native engine-v4's164 exact method/runtime hashes
  remain admitted: these additive analysis/presentation files do not alter the
  native builder or reseal any historical receipt. Its67-test campaign above
  remains the separate native software evidence.
- Actual browser flow verified in an **isolated copy** of the retained source:
  open saved model, inspect exact cooling report, reject an unsaved title edit,
  discard that local edit and recover the identical saved model/report. Only
  the isolated server was restarted for latest method-provenance verification.
  Rendered JSON confirms Physics model ID and3 analysis source hashes. Screenshot:
  `SECTOR_COOLING_HANDOFF_ISOLATED_GUI.png` (readable full-context report); later
  V2/V3 captures are retained as additional observations.
- User explicitly answered **keep the8878 viewer running; verify in isolation**.
  That viewer was not restarted. The new handoff is not claimed loaded there.
  No live records were edited during this checkpoint; read-only recheck confirms
  originalr18 commit638d6ea3... / SHA7504cf9b... remains exact, and source-bound
  model94be60a1... is still current. Protected cache and v3 receipt hashes remain
  unchanged. No migration, commit/push, fabricated reviewer or R08 work.

Full engine goal remains unfinished: source-specific hot properties, matched
full-domain cooling/structure, feed/operating closure and missing physical
interfaces still require implementation/evidence. Physical validation requires
real measurements. Keep those open; do not report all stages green or full goal
completion from this checkpoint.
