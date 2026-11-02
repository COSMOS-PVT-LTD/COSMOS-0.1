# Compact-engine redesign: isolated software implementation

Date: 2026-10-28. This implements the approved **first bounded redesign slice**,
not an accepted replacement engine or completion of R08.

## Approval and preservation

The user approved proceeding with the direction in
`docs/implementation/evidence/ENGINE_REFERENCE_REVIEW_2026-10-28/REVIEW_AND_REDESIGN_BRIEF.md`:
integrated cooling body/collectors, removable injector head, and a continuous
fuel-return route. The source review remains a historical research snapshot.

The 1.5 kN, sea-level static, 5 bar absolute, methane/LOX, pressure-fed requirements
remain unchanged. No owner project, engine baseline, live data root, viewer,
historical receipt or existing generator was replaced. No commit/push, cleanup,
material qualification, seal selection or hot-fire approval occurred. R08 remains
**ON HOLD at the user's request**; these are small extension-development checks,
not a resumed R08 campaign.

## Implemented

| Area | Implementation and exact source |
|---|---|
| Typed candidate | `systems/geometry/engine_redesign.py`: separate v1 schema; exact source part selections; bounded variable-radial-depth axial-sector station table with explicit SI units |
| Integrated geometry | CSG recipe fuses the uncut cooled-body operand and both source collectors, then subtracts the actual variable channel profiles; the head, plate, blind groove envelopes and supply pipes are retained |
| Return body | Same-bore/wall source pipe primitives form one connected unbranched chain with two actual external endpoints, from the upper collector to the separate fuel manifold; no interpretation of nine CAD segments as nine physical fittings |
| Geometry handoff | Actual station apertures/perimeters, radial ligaments and independent piecewise-polynomial channel volume; no rectangular-channel substitution or claim that axial apertures are normal-flow sections |
| Governance | `systems/geometry/engine_redesign_authority.py`: separate managed domain, exact source dependency/hash, compare-and-swap heads, idempotent retries, retained revisions and staleness; no baseline activation route |
| HTTP | `api/engine_redesign.py`, routed by `api/project_authority.py`: authorized seed, preview, save, list, history and exact-revision recipe reads; no posted paths, native commands, results or qualification overrides |
| Editor | `gui/static/engine-redesign.js`, loaded by `gui/server.py`: source/candidate selection, editable interior station dimensions in mm backed by SI, locked end apertures, unsaved-change guards, inspection, durable revisions and research-input download |
| Research viewer | Local-only manifest/STL inspector; requires current saved candidate, exact source/recipe SHA256 and artifact checksum; finite metre vertices and complete unique part spans; maximum 200k triangles. Reuses existing offline Three.js CAD display tools. Does not upload files or make artifact acceptance claims |
| OCCT extension | `plugins/geometry/compact_occt.py`: new exact union/subtraction builder, rigid placements, valid single-solid checks, independent integral comparison and metal interference rejection; no healing/sewing/fuzzy fusion |
| PicoGK extension | `plugins/geometry/workers/pico-compact/`: new C# entry point links the unchanged original component-field source, performs actual implicit unions/cuts, and writes native VDB plus explicitly SI binary STL; no OCCT mesh-to-PicoGK substitution |
| Offline execution | `scripts/generate_engine_redesign.py`: source-bound research input, explicit backend, no overwrites, >=10 GiB free before a full build, bounded voxel/cell budgets, unqualified artifact names and source/command hash provenance. This is not an admitted production runtime or an R08 qualification command |

On the retained source geometry the compiler produces **6 metal groups from 16
source metal parts** (two collectors + cooled body become one group; nine return
pieces become one group). The default candidate preserves the source envelope,
channel dimensions and flow path. Editing an interior depth changes the actual
cut profiles, reference volume and recipe hash. It does not resize the injector,
invent optimized dimensions or promise improved efficiency.

The frozen source regression fixture was copied from the retained research input
`output/picogk-components-2026-10-24/final-generation-evidence/captured-inputs.json`
(SHA256 `58761b31a87a729cd207d6cbda6a1bf110771e3b3835e6355788a8504e5fbb86`).
`tests/fixtures/compact_engine_source.json` contains only the source specification,
not app data or an approval. Automated HTTP tests install that geometry only in
isolated test repositories; they do not claim a matching hydraulic baseline.

## Verification

- Focused Python regression: **142 passed**. Includes new candidate/governance
  HTTP tests, existing component/port/circuit/joint/cooling/section/runtime tests,
  and three explicitly enabled new small native feature tests.
- JavaScript: **15 passed** across new research decoder and existing component/
  PicoGK controls. Node syntax check passed.
- New PicoCompact C# project built with **0 warnings, 0 errors**, using the
  installed SDK and a local-only restore source. Existing runtime output was
  not overwritten. Build output: `output/compact-engine-software-2026-10-28/worker/`.
- OCCT manufactured fixture: exact adjacent-ring union with variable sector cut;
  gap and overlap rejection; BREP/STEP export; independent STEP reimport volume.
- PicoGK manufactured fixture: native implicit union/cut, named VDB round trip,
  finite SI mesh, closed and consistently oriented edges, positive integral-
  compared volume. This small fixture does not establish full-engine fidelity.
- Existing component and PicoGK pinned source manifests still have **zero source
  hash differences**. They do not qualify the new extension.
- Raw focused pytest JUnit report:
  `output/compact-engine-software-2026-10-28/regression.xml`.
- Verification skill used to trace the local browser -> HTTP -> managed store ->
  rendered saved revision. A repository listing limit mismatch was found and
  fixed; the UI now pages within the existing 20-record authority limit.
  The first isolated server's Native Geometry flag was disabled; it was enabled
  only in subsequent temporary test instances, not in the user's viewer.
- Final browser check: prepared a candidate, changed station 13 depth to 2 mm,
  inspected/saved it, reloaded and reopened it, confirmed the retained depth and
  exact source/candidate commits, and saved a second revision. Research import
  controls rendered; observed browser error log was empty. Screenshot:
  `ui-candidate.png`. Test-store models are not engine evidence.

## How to use after an authorized backend reload

1. Open **Native Geometry** with its existing feature flag and managed-project
   composition enabled. Find **Compact engine · isolated redesign candidate**
   below the existing component editor.
2. Select the project and exact current saved component model. Prepare a separate
   candidate. Sources outside this bounded connected family are rejected.
3. Inspect or edit interior radial station dimensions, inspect again, and save a
   separate candidate revision. Existing engine/model heads are not advanced.
4. Download the research build input. Full builds remain storage-gated; do not
   resume qualification or overwrite a live engine to bypass that gate.
5. When resources permit, execute the offline research command using a **new**
   output directory and this **new** worker, then inspect its matching manifest/
   STL with the local research viewer. Never attach the new geometry to an old
   qualified build receipt.

The user previously requested keeping the viewer running. It was not restarted.
Refreshing static HTML against an old backend alone does not install new routes.

## Remaining, explicitly not claimed

- No full new engine CAD build was executed. Approximately 6 GiB free remained
  during development, below the full-build 10 GiB guard; nothing was deleted.
- New native runtime admission, whole-engine topology/fidelity, intended-use
  tolerances, critical-feature coverage, refinement/reimport qualification and
  genuine independent engineering review remain pending under the R08 hold.
- Automatic candidate generation from **arbitrary thrust** is not established:
  this extension derives from a valid exact source model in its bounded family.
- Variable-sector matched hot-fluid/coolant thermal, cooled-wall/material and
  feed/operating closure are **not** silently inherited from the old geometry.
  They require matched recomputation/new model support before engineering use.
- Smooth manifold transitions/fillets, outer-jacket optimization, helical
  channels, pressure-loss optimization, powder removal, minimum-normal wall
  checks, bimetal bonding/process design and manufacturing drawings are not
  completed by a Boolean union or a radial-station edit.
- Existing seal grooves are only source envelopes; supplier gland/load data,
  fluid compatibility, leak criteria and joint acceptance remain independent.
- Local artifact decoder logic is tested; a full-engine artifact import/render
  could not be verified without a matching new full-engine build. No miniature
  fixture was relabelled as engine evidence.

No efficiency, strength, physical readiness, production readiness or whole-
redesign completion claim is made by this implementation.
