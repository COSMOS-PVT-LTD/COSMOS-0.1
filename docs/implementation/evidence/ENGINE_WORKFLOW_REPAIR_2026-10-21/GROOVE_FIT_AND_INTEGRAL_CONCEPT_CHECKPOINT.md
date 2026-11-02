# Approved groove-fit and integral concept checkpoint

2026-10-21. The two approved subtasks are complete within their **isolated study
and investigation scopes**. Full engine hot-state/pressure readiness is not
complete. R08 HOLD. The owner engine, running8878 viewer and earlier candidates
remain unchanged. No material/allowable installation, commit/push, manufacturing
release or supplier outreach was performed.

Approval: `APPROVED_GROOVE_FIT_AND_INTEGRAL_CONCEPT.md`. Input artifact:
`PROPOSED_FIVE_GROOVE_CAD_1500N.json`. The approval did not select actual supplier
seals or authorize arbitrary vent holes or hardware use.

## Five nominal blind grooves: generated and software-verified

The new candidate is retained in
`output/connected-engine-five-grooves-2026-10-21-v1/`:

| Identity | Value |
| --- | --- |
| Project | `bb7ebea6-15f9-43b8-b6c0-fd2a2d358155` |
| Component | `afc95eb3-2d0c-55b7-95eb-2644f67e01d0` |
| Model commit | `c3fc6a8c-cddd-47e6-b8b7-897b31d4ef24` |
| Cold replay baseline | `3ce745d6-445a-4fca-81af-be9c09f200dc` |
| Build | `834a6255-f944-50b8-b248-82e8d6a00122` |
| Job | `149d6412-5179-4b55-8bb5-e85508a737e3` |
| Saved graph | `components-3df0ec293394526c32ad3d462fa0932f719a43295631fd9d8fbb1f7f677338ed` |

Normal project save -> exact interface HTTP inspection -> managed native build
-> independent STEP/STL QA -> retained downloads -> browser preview passed.
Result: **16metal bodies,182768triangles**, COMPLETED, source-current candidate;
STEP and STL pass. Fuel-through-regeneration and direct-LOX circuits remain
connected/segregated; both mounting interfaces retain8/8matching bolt axes.
Injector bores/counts, gas volume, saved throat/nozzle and pipe routing are not
resized or re-solved. This remains explicit **cold-baseline replay**, not a new
hot operating-point or material calculation.

The full native assembly is retained as
`PRELIMINARY-CONNECTED-SEPARABLE-HEAD-source.brep`, `...export.step`,
`...export.stl`, with immutable hashes in `artifact-sha256.json`.

### Exact nominal fit measurements

All grooves have2.000mm radial width and1.270mm depth. The table uses the exact
saved graph, not pixels or a screenshot. Gaps are conservative **radial envelope
separations** to all inclined fluid/bolt bores over the groove's full axial
interval, not a claim of measured manufactured minimum Euclidean clearance.

| Indexed groove / intended study barrier | Face | Radial envelope mm | Blind floor mm | Minimum conservative bore radial gap mm |
| --- | --- | --- | --- | --- |
| 0 / fuel inner | Rear/start | 18-20 | 6.730 | 5.509245 |
| 1 / fuel outer | Rear/start | 30-32 | 6.730 | 1.827534 |
| 2 / LOX inner | Rear/start | 35-37 | 6.730 | 1.373664 |
| 3 / LOX outer | Rear/start | 44-46 | 6.730 | 2.340522 |
| 4 / gas-joint envelope | Front/end | 55-57 | 6.730 | 15.058973 |

All exceed the unchanged0.600mm numerical geometry-resolution margin for this
study's150µm export tolerance. That margin is **not** a manufacturing tolerance,
pressure-wall allowable, seal land requirement or oxygen-service acceptance.
Removed nominal groove volume is2.984387357cm3. Opposite-face grooves occupy
different radii; no overlapping axial groove cuts or breached blind floor are
silently accepted.

The bundle's final output is named `gas-joint-groove`; the five distinct native
semantics are `face-groove-gas-joint-groove-0` through `...-4`. They are not five
gas seals: the index/radius/face table above retains their intended study roles.
No actual seal solid, selected supplier part, service preload, qualified metal
seal recovery or leak test is supplied. The UI correctly displays five native
grooves with selected seal NOT_SUPPLIED and service fit NOT_ASSESSED.

### Implementation and preservation of bounded capacity

Adding five separate modifiers to the20feature assembly exceeded the existing
24feature envelope. That initial unbuilt attempt is retained in
`output/five-groove-fit-preparation-2026-10-21-v1/` (no candidate accepted).
Instead of increasing the feature cap, the additive
`interface.face_grooves` modifier supports an explicit indexed count1..5 in one
node. Every cut retains the original single-groove blind-floor, wall/land,
full-range inclined-bore and prior-cavity exclusion checks. Unique native labels
are retained for each groove. No new generic expression/CSG evaluator is exposed.

`systems/geometry/separable_head_cad.py` groups supplied grooves per operand,
validates all input IDs and reserves them against collisions. Its complete
engine proposal now uses21features. Existing single-groove documents remain
supported. The24feature/frame,200ktriangle and independent fidelity limits are
unchanged. `api/component_geometry.py` exposes the bounded indexed operation.

An unqualified build first checked capacity at182768triangles:
`output/five-groove-unqualified-smoke-2026-10-21-v1/`. This was not promoted or
published as accepted; the subsequent normal managed build independently passed.

## Browser proof and availability

Open `http://localhost:8896/app/workbench/native-geometry?project=bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.
Select the exact saved component, inspect its completed attempt and load the
retained preview. The visible-body selector can isolate `gas-joint-groove / metal`.
Four rear grooves and one front groove were visually inspected by rotating that
plate. Screenshots are retained beside the candidate:

- `ui-four-rear-grooves.png`
- `ui-one-front-groove.png`
- `ui-complete-groove-study-assembly.png` (viewer left on All retained bodies;
  the assembled head covers the plate grooves, so isolate the plate to inspect)

Rear/front screenshot SHA256, respectively:
`4d53ebbc8f1829c1a4e67af9cdfe5276719a30e82ae94ea1acd2670872dd1696`,
`1f8dddb1671f38279d011c402c0b86756f14303918150f01fb8bcf2ccda4eae3`.

The browser's final warning/error log was empty. Rapid navigation away from the
login redirect caused one aborted context request and server BrokenPipeError;
the fresh native page's save/source inspection, retained job and preview loaded
normally. No blank failure was accepted as a working page and no production
server change was made to suppress that diagnostic.

The earlier8878/8892-8895 processes are not restarted or relabelled as current
methods. The new component methods are loaded in the fresh isolated8896 viewer.
User edits and owner data are not opened for writes.

## Integral collector/jacket investigation

See `INTEGRAL_COLLECTOR_JACKET_CONCEPT.md` and the separate source-bound
`output/integral-collector-feasibility-2026-10-21-v3/` evidence. An explicit
unqualified native probe produced one valid metal solid and one connected source
coolant void. Shared metal face area1938.141580mm2, metal925.321989cm3 and
coolant206.934791cm3 agree with independent source formulas; modeled coolant has
no solid blocking volume. No fuzzy fuse, bridge material, healing or resized
passage was used. V1's failed face-area measurement and subsequent corrected
attempts are retained.

This probe is **not** an admitted integral component in the16-body engine,
not STEP/STL-qualified as a new combined body, and not a bimetallic bond or
manufacturing qualification. It investigates the upper seam only. The source
0.700mm collector gas/coolant wall, lower-header seam and other pressure joints
remain unresolved. Primary NASA research and concrete material-region,
DFM/powder-removal, semantic/native qualification and hot-analysis work are
documented in the concept report without transferring other hardware's evidence.

## Tests and method scope

- Fresh `groove-fit-v1` campaign:48component native +7component HTTP +7nozzle/HTTP
  +31native fixture regression = **93passed, none skipped**.164native runtime
  identities and new receipts sealed; prior qualification files are unchanged.
  `docs/implementation/evidence/R07_COMPONENTS_2026-10-20/runtime-qualified-groove-fit-v1.json`.
-314geometry/system tests passed,424deselected in
  `groove-integral-geometry-unit-v1.xml`.
-31focused groove/layout/integral-preparation tests passed in
  `groove-fit-integral-unit-v1.xml` (overlaps the314tests; do not sum them).
  Covers indexed/sequential cut equivalence, analytic removed volume/centroid,
  unique roles, bounds, common blind floors, unsupported source/gap/bore and
  missing channel contacts.
-439JavaScript tests passed; no display engine or styling rewrite was performed.
- Ruff passed10targeted files; mypy passed5targeted implementation files.
- The integral native probe has seven passing geometry diagnostics, **not**
  component admission, material/process qualification or experimental validation.

Historical owner reference remainsr18/v4 at commit
`638d6ea3-4057-4b90-8dd4-8fc956b4772d`. Viewer8878 remains PID77508.
The final authenticated read-only HTTP check reconfirmed that exact owner
revision/commit and canonical SHA256
`7504cf9bf0b6371ea9af5228df5b0587dd8b32e08247c2b20d1c88860d977bcf`.
Protected
`cache/cea/test_key.json` remains SHA256
`6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`.
No remote CI/release claim is made for this dirty checkout.

## Remaining full-engine work

These approvals resolve the nominal groove-fit experiment and select the
integral manufacturing direction for investigation; they do not resolve:

- A qualified supplier seal, tolerances, compatibility, service-temperature
  load/recovery data, fasteners/preload, flange distortion or leakage evidence.
- A production-admitted integral collector with material regions and complete
  semantic/native export qualification.
- Matched sector-channel/collector/chamber thermal, feed and warmed-injection
  whole-engine closure and cooled-wall/bimetal structural analysis.
- All remaining lower-header, pipe/feed and injector pressure interfaces.
- Real experimental evidence, uncertainty and qualified acceptance.

The overall engine goal remains open; no R08 development begins.
