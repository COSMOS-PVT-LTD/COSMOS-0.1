# CAD inspection and reference dimensions

2026-10-22 implementation; reverified 2026-10-24. Implements the user's dimensions/measurement/angle request in the existing shared CAD workspace. R08 remains on hold. This is an inspection-tool increment, not a claim that COSMOS now contains every feature of a general-purpose CAD system. Fresh completion evidence is in `COMPLETION_2026-10-24.md` beside this report.

## Research and feature selection

Primary documentation reviewed:

- [Autodesk Fusion: Measure reference](https://help.autodesk.com/view/fusion360/ENU/?contextId=SIM-MEASURE-CMD): selection-dependent distance/angle/area/radius, coordinates, snap selection, units and precision.
- [Onshape: Measure](https://cad.onshape.com/help/Content/View/measure_tool.htm): geometry-dependent measurements, world-axis deltas, units, and inspection in section views.
- [Onshape: Dimension](https://cad.onshape.com/help/Content/Sketch/dimension.htm): reference/driven dimensions are distinct from driving sketch dimensions.
- [Autodesk Fusion: Analysis tools](https://help.autodesk.com/view/fusion360/ENU/?contextId=SLD-INSPECT-TOOLS): measurement, section analysis and interference are separate functions; interference evaluates solid-body overlap rather than bounding-box overlap.
- [Onshape: Mass properties](https://cad.onshape.com/help/Content/View/mass_properties_tool.htm): mass calculations depend on assigned material density; volume/area and centroid are useful inspection quantities, but do not justify guessing mass from display appearance.

| Tool suited to COSMOS | Implementation and boundary |
| --- | --- |
| Distance, world XYZ deltas | Two retained mesh points; SI calculation, converted display units. Not minimum distance between whole CAD bodies. |
| Coordinates | Original vertex or ray/triangle intersection, with part and original triangle identity. |
| Angular dimension | A–B–C angle at B, 0–180 degrees; degree/radian presentation. |
| Radius / diameter | Circumcircle through three explicit mesh picks, including centre and circular reference outline. Does not establish that a CAD edge is circular. |
| Surface orientation | Oriented triangle-normal angle; not analytic face/dihedral metrology. |
| Snap / keyboard selection | Nearest **visible original vertex of the hit triangle**, or surface intersection; explicit original-index input provides keyboard/reproducible access. No invented B-rep face or edge IDs. |
| On-model reference dimensions | Point markers, distance legs, angle legs/arc and circle/radius outline; labels explicitly marked REF. Pin/show/hide/remove up to 16 session annotations. |
| Length / angle units and precision | mm/cm/m/in, degrees/radians, 0–6 displayed decimal places. More digits do not increase precision or certify uncertainty. |
| Body properties | Selected-body world-axis bounds/extents; retained independent STEP volume, surface area and volume centroid when the exact component context is available. Otherwise explicitly mesh-bounds-only. |
| Analytic section properties | Existing source-bound local-X annulus/sector/bore service exposed inside the inspector. Part, position, method, area, radii and source response retained; unsupported planes/features fail explicitly. |
| Inspection export | Readable JSON with job/model/artifact identities, original picks, SI values, presentation units, pinned dimensions, STEP properties and latest successful source section. Also inspect the last generated JSON within the UI. |
| Navigation / assembly inspection | Existing XYZ axes, camera projections, clipping, explode/break/detail, visibility, styles and colours preserved. Measurement values never use illustrative layout offsets. |

### Deliberately not represented as implemented

- Analytic B-rep face/edge picking, exact whole-body minimum clearance and solid interference queries.
- Wall-thickness, draft, curvature, tolerance/GD&T and fastener-stack acceptance analyses.
- Material-weighted mass/inertia without a complete assigned density/material basis.
- Driving sketch dimensions/constraints, interactive topology editing, assembly constraint solving, or manufacturing drawings/DXF/PMI.
- Physical measurement uncertainty, supplier acceptance, manufacturing or hot-fire qualification.

Those features need explicit kernel/data contracts and verification, not renamed mesh tools or decorative toolbar buttons. Source editors and STEP/STL/BREP downloads already exist; this increment neither replaces them nor declares display annotations to be manufacturing dimensions. The previously recorded incomplete pinned `OCP.Bnd.Bnd_Box` dependency has not been repaired or requalified here.

## Architecture and provenance

- `gui/static/ngg/viewport.js`: shared reference-measurement calculations, structured picks, source-to-display annotation mapping, inspector controls, report generation and body-property context validation.
- `gui/static/ngg/styles.css`: scoped result, pick list and reference-label presentation.
- `gui/static/component-geometry.js`: injects the exact already-read review context and a read-only section callback into the shared viewer.
- `tests/js/ngg_measurements.test.cjs`: new numeric, source-binding, raycast, offset, clipping and lifecycle regression cases.

The shared renderer still makes **no network requests or scientific-state writes**. Component transport stays in the caller. Existing fixture/nozzle callers gain mesh inspection and annotations without a fabricated independent STEP context.

Flow: select completed retained component attempt → existing authenticated `GET .../review-context` → exact job/model/body identity validation → inspection panel. Section command → caller's authenticated `GET .../sections?part_id=...&x_m=...` → source formula result → exact job/part/position checks → report. Disposed viewers, superseded section requests and replaced preview generations cannot install a stale section result.

Coordinates use retained Float32 SI triangles. Rendering translation is removed from ray hits. Annotation anchors follow part display offsets; hidden/clipped/omitted anchors suppress the corresponding annotation. Lines are foreground reference overlays, not inferred physical edges. Detail insets omit annotations to avoid mismatched-camera labels. Circle outlines require picks from one body; cross-body picks can define a numerical circumcircle but are not drawn as a feature outline.

Coincident angle points, zero normals and nearly collinear circle triples fail explicitly. Circumcentres are evaluated in a scaled local frame. No mesh measurement is promoted to tolerance-certified CAD metrology. STEP properties come from retained independent reimport, not pixel measurements or a newly run native campaign. Their volume centroid is not a material-weighted engine centre of mass; bounding dimensions are world-axis-aligned, not an optimal oriented box.

Annotations are session-only and clear on preview replacement/clear. Export before reloading. Existing source geometry, material assignment, engineering readiness and persistence authority are unchanged.

## Verification

- **480 JavaScript tests passed**, zero failed/skipped, including 14 new measurement tests and the existing 27 focused workspace/view-tool cases.
- **15 HTTP tests passed; 2 explicitly skipped**, using `test_component_projects_http.py` and `test_ngg_http.py`. Skips require a separately pinned native campaign; not reported as native successes.
- Fresh browser tab loaded the final bundle against the isolated retained component job, not the owner viewer. Real preview: 16 bodies / 182,768 triangles.
- Original vertices 0 and 1000: **130.849351594 mm** distance; signed deltas displayed independently.
- Original vertices 30288, 30378, 30474: **95.000000633 mm** radius / **190.000001266 mm** diameter; **134.286 degrees** three-point angle at the chosen display precision. These are mesh references, not manufacturing acceptance values.
- Original-index picking, live annotations, pinning and unit conversion exercised. Actual canvas intersection verified separately and labelled `surface hit`, not mislabelled as the nearby original vertex.
- STEP property panel showed retained job `149d6412-5179-4b55-8bb5-e85508a737e3` and model commit `c3fc6a8c-cddd-47e6-b8b7-897b31d4ef24`.
- `lower-coolant-header`, local X = **0.009 m**: source section area **0.0013796670626269893 m²**. Local X = 0.03 m was rejected as outside the supported local profile; this is not world X. Error remained visible without a fabricated result.
- Export button exercised; generated JSON read back from its UI preview: schema `cosmos.cad-inspection/1`, exact job/model/artifact context, three pinned dimensions, 16 STEP part-property records, correct section area and `reference_only: true`. On 2026-10-24 the actual file download was also verified and parsed at `/Users/vaibhavkumarn/Downloads/cosmos-cad-inspection.json`; SHA256 `1ca4cecd886881b410039ccc2e5bae3f380f500f66ac23cfda2dbf5dd853a121`.
- Exploded assembly kept the source values and moved annotation anchors with their bodies. Automated clipping/hidden-body/source-replacement tests passed.
- Browser console showed no errors/warnings during the completed inspection flow.

Commands:

```sh
node --test tests/js/*.test.cjs
.venv-release-p12/bin/python -m pytest tests/integration_tests/gui/test_component_projects_http.py tests/integration_tests/gui/test_ngg_http.py -q --tb=short -rs
```

Node was the existing bundled runtime at `/Users/vaibhavkumarn/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`.

## Use

Open a retained completed candidate → show its 3D preview → Maximize → **Inspect**. Choose Distance, Angle, Radius / diameter, Coordinates or Normal angle. Click geometry or supply original vertex indices; Pin reference dimension retains the reference in this session. Body properties and Source section area open their separate evidence-aware inspectors. Select Off to return to ordinary part selection; use the existing View navigation tools to orbit/pan.

Isolated preview: `http://localhost:8896/app/workbench/native-geometry?project=bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.

## Preservation

No new backend endpoint, dependency, native kernel, database migration, scientific input, material assignment, owner-project edit, commit, push or release. During the 2026-10-22 implementation, owner viewer port 8878 remained PID 77508 and was not signalled/restarted. On 2026-10-24 neither previous viewer was running; only the isolated 8896 viewer was started, using the existing task-owned output data folder. Port 8878 was not started. Protected CEA fixture SHA256 remained `6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`.

Verified source hashes before final evidence capture:

- `viewport.js`: `fde2475591df9f0ce4c9a1f306e017a96c946d99dd7d57c7508fe41d92c00afd`
- `styles.css`: `c0f85eb66160a6c5cb0b8aff8ef3bed38adfa41aa6ad8b7fced4de785bc00a80`
- `component-geometry.js`: `1dc51358f3710f67a4c291602a07552ad541c959c46221e6ccedd8acb50d8322`
- `ngg_measurements.test.cjs`: `557404c8a4d7bdd82f32d42697c4e07aef429549d79c6183b842643347198d8b`
