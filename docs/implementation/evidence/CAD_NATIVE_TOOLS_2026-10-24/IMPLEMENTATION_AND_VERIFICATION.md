# Native CAD tools: implementation and verification

Date: 2026-10-24. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.
Git HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`; substantial pre-existing uncommitted work remains. This report describes the tested working tree, not that committed SHA or a release. No commit, push, migration, or R08 development was performed for this task.

## Outcome and scope

The requested three capabilities are implemented as a bounded native-CAD vertical slice, integrated with the existing component editor, saved revisions, native build pipeline and shared 3D workspace. They do not constitute a general-purpose mechanical CAD suite or a manufacturing/physical-engine release.

| Capability | Implemented | Explicit boundary |
| --- | --- | --- |
| Solid clearance/interference | Native BREP minimum distance, Boolean common volume, containment/interference checks, numerical contact bands, required-gap comparison, source-coordinate witnesses and viewport annotations | One explicitly selected pair at a time. Not an AABB/mesh approximation, but also not infinite-precision mathematics, signed penetration depth, all-pairs engine clearance qualification or tolerance-stack/contact certification |
| Driving constraints | Persisted unit-aware fixed dimensions, diameter-to-radius and directed affine equality/ratio/offset rules; same-parent local frame-origin axes; preview, save/CAS/history and actual CAD regeneration | Directed feature-dimension system, not a general nonlinear sketch or assembly-mate solver. No circular systems, conflicting target writers, implicit unit conversions or hydraulic-source overrides |
| Engineering drawing generation | Native hidden-line projections, three third-angle orthographic views at an explicit common scale, native envelope dimensions, complete resolved nominal feature schedule, title block, PDF/SVG/provenance downloads | UNRELEASED engineering sheets. No automatic supplier tolerances, GD&T/datums, section/detail drawing authoring, weld/finish specifications, fit certification, assembly BOM or manufacturing sign-off. SVG is sheet 1; PDF contains continuation schedules |

“Exact” clearance here means evaluation of retained solid BREP instead of display tessellation, using an explicitly declared numerical resolution. Near-contact and unresolved-small-volume cases remain INDETERMINATE.

## Architecture and implementation map

The frozen layering and existing snapshot/feature-graph/native-worker path are preserved.

- `systems/geometry/driving_constraints.py`: bounded directed constraint resolution, unit checks, dependency sorting, immutable input and resolution receipt.
- `systems/geometry/component_model.py`: optional source constraints compiled into the existing DesignSnapshot/FeatureGraph and source hash. Models without a constraint block retain their previous source semantics.
- `systems/geometry/component_authority.py`: save-time resolution before source-binding checks; method fingerprinting includes the new driver and runtime policy. Source-bound injector bore/count edits cannot bypass their hydraulic provenance.
- `systems/geometry/cad_tools.py`: project-authorized retained-candidate selection, BREP hash/part mapping, bounded process execution, explicit inspection/drawing declarations and provenance.
- `plugins/geometry/workers/cad_inspection_worker.py`: isolated OCCT distance/Common/HLR operations; native geometry is millimetres and returned values are canonical SI.
- `systems/geometry/manufacturing_drawing.py`: shared deterministic A3 PDF/SVG layout and continuation parameter schedules. Native code and ReportLab do not load into the application interpreter.
- `api/cad_tools.py`, `api/project_authority.py`: thin authorized project routes; fixed-name attachment downloads for all three drawing formats.
- `gui/static/component-geometry.js`: saved driving-rule editor and preview; native-tool callbacks bound to the selected job/source.
- `gui/static/ngg/viewport.js`: native inspection/drawing ribbon commands, required explicit numeric inputs, exact source/pair guards, witness annotations and inspection JSON provenance. Transport remains outside the shared viewport. Pending/stale/disposed responses are guarded.
- `gui/server.py`: explicit UNRELEASED attachment scope; OCCT-only presentation hides the disabled reference fixture laboratory.
- `api/occt_component_runtime.py`, `api/component_geometry.py`, `api/ngg_workbench.py`: separately qualified OCCT-only component admission; no PicoGK/combined-runtime admission by substitution.

### Routes

Under `/api/projects/<project>/cad-tools`:

- `GET /capabilities`
- `POST /constraints`: preview only; body is exactly `{specification: ...}`. Saving still uses the existing authorized component CAS command.
- `GET /jobs/<job>/clearance`: exact pair, required clearance, numerical length and volume resolutions.
- `GET /jobs/<job>/drawing.pdf`, `.svg`, `.json`: exact retained source part, explicit scale/curve deflection and title-block declarations.

Project authorization, exact saved source identities, request validation and the existing mutation protections are retained. Native processes have bounded time/output/queue/resources and private temporary files. No arbitrary scripts or caller-supplied runtime commands are accepted.

## Approved runtime decision

The user explicitly approved: **“Approve separately qualified OCCT-only profile.”**

See `ADR_OCCT_ONLY_RUNTIME.md`. Current local profiles:

- Component building: `component-runtime/runtime.json`.
- Native inspection/drawing: `inspection-runtime-v2/runtime.json`.
- Earlier `inspection-runtime/` remains unchanged as historical qualification. Its older API hash is intentionally no longer current after the JSON attachment fix; do not use it as the active profile.
- Pinned dependency list: `requirements-cad-inspection.lock.txt`; isolated interpreter: `.venv-cad-inspection/bin/python`.
- Qualification scripts: `scripts/qualify_occt_component_runtime.py` and `scripts/qualify_cad_tools.py`.

The old combined manifest references missing temporary files. It was neither repaired by resealing nor silently relaxed. This new profile is expressly local software research: `production_enabled=false`, `picogk_enabled=false`. It does not enable the combined reference fixture laboratory, nozzle profile or PicoGK implementation.

## Real engine-concept browser verification

Only the new isolated preview root was edited:
`output/cad-native-tools-2026-10-24/app-data`.
The source root was copied using online SQLite backups and integrity checks by `scripts/prepare_cad_tools_preview.py`. The user's owner engine root and the previous task viewer on port 8896 were not switched or migrated.

Source identities:

- Project: `bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.
- Component: `afc95eb3-2d0c-55b7-95eb-2644f67e01d0`.
- Saved constrained revision v2: `16caabb8-c49c-4e54-b8ad-87ed9aed7360`.
- Captured build: `b496ea6b-f95a-5005-96e2-99ddab7bc6cf`.
- Build commit: `9a7c2679-a10b-460f-9b72-63fe9d24991c`.
- Completed job: `73334941-5197-4818-8a1a-616c16ac5009`.
- Native revision: `geometry-job-542ca8969c9d474e8a76ad3152bd3847`.
- BREP SHA256: `342f7119524730ca7b9da640679f3e91ee5888da79f9cb0a13190743e2b1259d`.

The browser added and evaluated a fixed fuel-supply length rule of **0.08 m**, preserving the original nominal length, then saved v2 and rebuilt all **16 exported bodies**. Independent STEP checks and STL topology/dimension checks passed the explicitly supplied pre-existing software QA ceilings. This is not a new engineering tolerance specification. The retained record reports 56.64 seconds for the worker, exit 0; geometry QA completion also includes its independent checks.

A separate real native HTTP regression changed a synthetic pipe length from **0.04 to 0.065 m** and checked that the regenerated native/independent bounds changed accordingly. Therefore the driving-rule implementation is not merely a display label.

The rebuilt engine pair `fuel-supply` / `oxidizer-supply` was evaluated through the final browser UI:

- Required gap: 0.001 m, numerical length resolution: 1e-8 m, volume resolution: 1e-15 m³.
- Native minimum solid distance: **0.3883849145028302 m**.
- Common solid volume: **0 m³**; DISJOINT / SATISFIED for this selected-pair query only.
- Native witnesses were annotated on the original source parts, not exploded-layout positions.

The browser downloaded the final PDF and JSON successfully. A browser-discovered JSON attachment-header defect was fixed, covered by HTTP regression, and independently requalified into `inspection-runtime-v2/`. The final PDF SHA256 is **089dc1f98e2f2e5f11042cfbb048a3c1eb1015e8fbe77587f55b01b229d95e9d**, identical between the browser download and evidence file.

### Evidence files

- `output/cad-native-tools-2026-10-24/rebuilt-native-record.json`
- `output/cad-native-tools-2026-10-24/rebuilt-native-inputs.json`
- `output/cad-native-tools-2026-10-24/native-cad-workspace.png`
- `output/pdf/cad-native-tools-2026-10-24-final/retained-engine-clearance.json`
- `output/pdf/cad-native-tools-2026-10-24-final/UNRELEASED-flange-drawing.pdf`
- `output/pdf/cad-native-tools-2026-10-24-final/UNRELEASED-flange-drawing.svg`
- `output/pdf/cad-native-tools-2026-10-24-final/browser-drawing-provenance.json`
- `output/pdf/cad-native-tools-2026-10-24-final/drawing-pdf-provenance.json`
- `output/pdf/cad-native-tools-2026-10-24-final/page1.png`, `page2.png`: both rendered and visually inspected; no clipping, overlap or missing schedule text observed.

PDF metadata uses deterministic invariant generation (fixed metadata timestamp). Currentness is established by the explicit job/model/source IDs, not PDF creation time. Poppler emitted a local Fontconfig configuration warning, but rendered both complete sheets successfully.

## Test results

All listed final suites executed with zero failures, errors or skips. Counts below do not double-count the separate 14-case driver qualification report, which is already included in the 55-case unit regression.

| Suite | Passed | Retained report |
| --- | ---: | --- |
| Driver, component/source-binding and runtime admission units | 55 | `output/cad-foundation-regression-2026-10-24-final.xml` |
| Existing native component fixtures, real OCCT + independent STEP/STL checks | 48 | `output/cad-component-native-2026-10-24.xml` |
| Component HTTP workflow | 7 | `output/cad-component-http-2026-10-24.xml` |
| Native inspection/drawing fixtures | 13 | `output/cad-tools-native-2026-10-24-v2.xml` |
| Native CAD HTTP, driving-save/rebuild and authorization | 5 | `output/cad-tools-http-2026-10-24-v2.xml` |
| JavaScript regressions | 482 | `output/cad-js-2026-10-24.xml` |

Total scoped evidence: **128 Python + 482 JavaScript passing checks**, plus the real 16-body browser rebuild and export checks. This is not a whole-repository test rerun, remote CI result, qualified-engine review, usability study or hardware validation. Failed intermediate development checks remain historical and were not used as passing qualification.

Native cases include known box gaps/overlaps/contact, complete containment, small-volume ambiguity, overlapping AABBs without real interference, witness distances, HLR hidden/visible edges, oversize-page rejection and PDF/SVG validity. Runtime tests reject changed methods/interpreters/commands/receipts/reports, insufficient/skipped evidence and attempts to enable production/PicoGK.

## Open and use

The isolated final viewer is running at:
`http://localhost:8897/app/workbench/native-geometry?project=bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.

1. Open the component model, expand captured source `b496ea6b-f95a-5005-96e2-99ddab7bc6cf`, load attempt history and inspect the COMPLETED job above.
2. Show retained component 3D preview, maximize, then use **Inspect → Solid clearance** or **Engineering drawing**.
3. Clearance requires explicit pair/gap/numerical resolutions. Drawings require explicit declarations, scale and curve deflection; use `NOT SPECIFIED` for unresolved draft declarations instead of invented manufacturing values.
4. Driving rules are in the component editor's **Driving dimensions** section. Evaluate locally, save the exact revision, then regenerate native CAD. Saving does not overwrite any earlier CAD artifact.

If restarting this task-only viewer later, first check that port 8897 is available. From the repository directory:

```sh
COSMOS_NEW_SHELL=1 COSMOS_DURABLE_PROJECTS=1 COSMOS_NGG=1 \
COSMOS_NGG_RUNTIME_CONFIG="$PWD/docs/implementation/evidence/CAD_NATIVE_TOOLS_2026-10-24/component-runtime/runtime.json" \
COSMOS_CAD_TOOLS_CONFIG="$PWD/docs/implementation/evidence/CAD_NATIVE_TOOLS_2026-10-24/inspection-runtime-v2/runtime.json" \
.venv-release-p12/bin/python -c 'from gui.server import serve_application; serve_application("/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/output/cad-native-tools-2026-10-24/app-data",host="127.0.0.1",port=8897)'
```

The manifests are intentionally machine-local and hash-pinned. Source or runtime changes require fresh qualification, not editing old receipts. Do not point this preview command at the owner's app-data folder as an implicit migration or runtime switch.

## Remaining engineering/release boundaries

No source requirements were invented or declared physically validated. Matching thermal/feed solving, joint/seal supplier qualification, process-specific material allowables, manufacturing tolerances, independent engineering approval and experimental measurements remain separate engine-readiness work. A common-volume result does not qualify seals, pipes, cooling flow or pressure joints. R08 stays on hold.

Protected CEA file `cache/cea/test_key.json` remains SHA256 `6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`. Historical qualification/manufacturing/physical receipts were not rewritten. The coordinator lease correctly rejected a concurrent offline collector; evidence was collected only after gracefully closing this task-owned viewer, then the viewer was restarted on the same isolated root.

## Primary technical sources

The implementation was checked against the installed pinned binding and official APIs:

- [OCCT BRepExtrema_DistShapeShape](https://dev.opencascade.org/doc/refman/html/class_b_rep_extrema___dist_shape_shape.html): native shape-distance evaluation, numerical deflection and containment handling.
- [OCCT BRepAlgoAPI_Common](https://dev.opencascade.org/doc/refman/html/class_b_rep_algo_a_p_i___common.html): Boolean common geometry. Installed OCP 7.8.1 exposes IsDone, not HasErrors; the worker uses the actual binding and validates the result topology.
- [OCCT HLRBRep_HLRToShape](https://dev.opencascade.org/doc/refman/html/class_h_l_r_b_rep___h_l_r_to_shape.html): classified visible/hidden projection edges.
- [cadquery-ocp 7.8.1.1](https://pypi.org/project/cadquery-ocp/7.8.1.1/): pinned native package version used by the isolated runtime.

The PDF skill informed deterministic, visually checked multi-page layout. The verification skill required browser-to-API-to-native-source checks and exposed the JSON attachment issue before handoff.
