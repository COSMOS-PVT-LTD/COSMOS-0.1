# 3D inspection tools — implementation and verification

Date: 2026-10-22. Scope: the current user's 3D-viewing request only. R08 remains on hold. This does not close the engine thermal/feed, manufacturing, seal-selection or physical-validation work.

## Outcome

The shared retained-triangulation viewer now provides all requested viewing categories. The component editor, managed nozzle preview and reference-fixture preview mount the same toolset. Scientific architecture, CAD generation, authoritative project records, exports, material assignments and engineering calculations were not changed.

The former 31-line WebGL1 display could not provide per-part materials, perspective cameras, occlusion-aware selection or the requested layouts. It has been replaced **within the existing presentation boundary** using the already-vendored offline Three.js r186 and OrbitControls. No library download, new dependency, geometry-kernel substitution or scientific architecture change was introduced. Its existing `load`, `clear`, `fit`, `orient`, `clip`, `draw`, `stats`, `dispose` entry points are retained. `load` is now asynchronous; all three repository callers await it and reject stale/disposed loads.

## Implemented tools and limits

| Category | Implementation | Important boundary |
| --- | --- | --- |
| Projection | Orthographic and perspective cameras; scale-preserving switching | Display camera only |
| Principal views | Front, back, right/side, left, top, bottom | Explicit world axes; selected projection remains in effect |
| Axonometric | Isometric, dimetric and trimetric direction presets, forcing orthographic | Custom orbit is labelled when view direction changes |
| Section | Half, reversed half, slab, X/Y/Z or arbitrary normalized plane; SI offsets; centre shortcut; amber intersection traces | Open mesh cuts, **not** capped solids, analytic sections, measured areas or exported drawings |
| Auxiliary | Custom plane normal or a picked triangle's normal, forcing orthographic | Triangulated normal, not analytic CAD face identity |
| Detail | Magnified lower-right selected-part inset, independent camera, labelled frame and picking | Whole selected part, not a dimensioned circular drafting detail |
| Broken | Choose source axis and omitted interval; middle-30% shortcut; two independently clipped copies, upper portion translated to close 85% of interval; visible NOT TO SCALE badge | Display-only omitted band/shortening, not a broken engineering drawing or modified source mesh |
| Exploded | Deterministic radial or ordered X/Y/Z part offsets, amount slider, reassemble | Illustrative offsets, not collision checking, assembly constraints or a manufacturing sequence |
| Wireframe | Triangle wireframe | Includes tessellation, not only analytic edges |
| Hidden line | Depth-only surfaces, visible sharp mesh edges and approximate displaced silhouette hull | Not analytic CAD hidden-line removal; tessellation artifacts can remain |
| Legacy hidden | Visible edges plus dashed depth-occluded edges | Same mesh/silhouette limitation |
| Shaded / edges | Lit shaded faces; optional sharp feature-edge overlay | Display normals and 25-degree edge threshold |
| Conceptual | Toon-lit part colours with edge overlay | Presentation, not scientific field data |
| Realistic | PBR metallic/roughness material and studio lights | Not a photograph, ray tracing, measured reflectance or thermal/material simulation |
| X-Ray | Transparent faces and edge overlay | Conventional sorted transparency can show overlap artifacts |
| Appearance | Part selector, native colour picker, 10-colour palette, opacity, visibility, isolate/show-all, apply-to-all, per-part/default reset | Session-only appearance; **does not assign engineering materials** |
| Navigation | Orbit, pan, zoom, fit-visible, fit-selected; arrows, Shift-arrows, +/−, F/Home, 0/1/2/3 | Zoom/distance bounded; event-driven render rather than permanent animation |
| Expanded view | Dedicated inspection sidebar and full-height canvas; narrow-window stacked layout; Escape and forward/reverse focus loop; background inert/restored | Only display host is moved/restored; no app-data changes |

## Source locations

- `gui/static/ngg/viewport.js`: bounded presentation helpers, immutable source copy, parts/ranges validation, Three.js renderer, materials, cameras, clipping/layouts, picking, controls, cleanup.
- `gui/static/ngg/styles.css`: shared inspection tools, palette, responsive expanded layout and detail/broken annotations.
- `gui/static/component-geometry.js`: exact retained multi-part preview integration and stale-load guard.
- `gui/static/managed-engine-builds.js`: exact retained single-body nozzle preview integration and stale-load guard.
- `gui/static/ngg/view.js`: reference-fixture integration; separate display host leaves server metrology outside the expanded view.
- `tests/js/ngg_view_tools.test.cjs`: 16 focused tests, including real Three.js scene objects without a mock graphics kernel.

Presentation fields stop `input`/`change` propagation into the engineering editor. No fetch, scientific POST, localStorage, project save, migration or material mutation exists in the tool module. All tool operations use local display state. Exact part intervals must cover the entire preview once, without gaps/overlap; malformed metadata fails closed.

Ray casting selects visible source triangles, excludes clipped-away intersections and subtracts layout offsets before returning original global vertex indices. A clipped triangle without a visible original vertex does not fabricate a measurement index. The original server-owned geometry remains authoritative.

## Test results

1. Full JavaScript suite: **455 passed, zero failed/skipped**. Final resource-lifetime/zoom adjustment was followed by **16/16 focused viewer tests passing**.
2. Initial default component HTTP run: **5 passed, 2 explicitly skipped** because no pinned native campaign was supplied.
3. Expanded component + fixture HTTP campaign with the prior explicit R07 runtime: **16 passed, 1 failed**. The native component review/handoff test failed before geometry construction due to the runtime dependency failure below. This is not reported as an all-green native campaign.
4. JavaScript syntax checks passed for the modified preview controllers and renderer.
5. Browser: real retained **16-part / 182,768-triangle** assembly successfully fetched, validated and rendered. All 8 visual styles, perspective, 6 principal directions, 3 axonometric presets, custom auxiliary normal, picked-triangle auxiliary, half/slab/oblique cuts, colour application, 1/16 isolation, 15/16 visibility, reassembly, exploded layout, broken layout, detail inset, reset, original-index surface selection and expanded/escaped view were exercised. Browser console: **no errors or warnings** during these checks.
6. Keyboard checks: forward Tab from the canvas wraps to projection, reverse Tab wraps back to canvas, Escape restores the original host and focus. Background `inert` attributes were observed during the modal view; custom camera orbit updates the preset indicator.

Browser end-to-end verification covers the managed component route. Nozzle and fixture entry points have shared scene/loader/source-contract coverage; no fresh successful native build is claimed for those entry points in this campaign.

### Separate native-runtime blocker

Explicit manifest used:
`docs/implementation/evidence/R07_COMPONENTS_2026-10-20/runtime-qualified-groove-fit-v1.json`.

Worker failure: `cannot import name 'Bnd_Box' from 'OCP.Bnd' (unknown location)`.

The manifest points at the release Python with:
`PYTHONPATH=/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1:/private/tmp/cosmos-r05_3-native.IcKKdc/cad-tools`.

A direct read-only import using that same path confirms `OCP.__file__` and `OCP.Bnd.__file__` are `None`, and `hasattr(OCP.Bnd, 'Bnd_Box')` is false. The Bnd directory contains a cached bytecode file but not its importable source/native binding. The prior temporary installation is incomplete. Why those files are absent has not been established. It was **not** repaired, auto-installed, requalified or relabelled passing in this display-only task. Restoring a pinned CAD environment and rerunning the native campaign is separate work. Existing retained STEP/STL and display reads remain usable; fresh native generation is not certified working by this turn.

## Browser/data evidence

- Isolated viewer: `http://localhost:8896/app/workbench/native-geometry?project=bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.
- Exact model: `afc95eb3-2d0c-55b7-95eb-2644f67e01d0`.
- Captured build: `834a6255-f944-50b8-b248-82e8d6a00122`.
- Retained completed job: `149d6412-5179-4b55-8bb5-e85508a737e3`.
- Source count after display reset: **548,304 original display vertices**; no decimation or substitute model.
- Screenshots: `output/view-tools-2026-10-22/`: all eight `style-*.png`, `02-perspective.png`, `03-coloured-isolated-injector.png`, `04-half-section.png`, `05-slab-section.png`, `06-oblique-slab.png`, `07-auxiliary-detail.png`, `08-exploded-layout.png`, `09-broken-layout.png`, `10-final-view-tools.png`.
- Final screenshot SHA256: `236cac37e3c81398439f18aed1042c5399263514d80702d0a5b6a5952b9541e5`.

Port 8878 still belongs to the existing PID 77508. It was not restarted or signalled. No live owner project was migrated, recalculated or rewritten. The protected CEA fixture still hashes to `6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`. No commit, push or release was performed; the wider checkout remains dirty/uncommitted.

## Implementation hashes

| File | SHA256 |
| --- | --- |
| `gui/static/ngg/viewport.js` | `b1f1bf3950d726ae67cb88223ab914861bb138783e8677aa6a41fb63e31f2188` |
| `gui/static/ngg/view.js` | `9bdb5d23ce3f7b9d4364c574ed45983fac2a2b0e5fecb95e8f5575e5ec0a7421` |
| `gui/static/ngg/styles.css` | `c0583209de61d763c2bd50a61e4947f3248c0723acd92b7a38d855b9ed16a6c9` |
| `gui/static/component-geometry.js` | `bd7e8fe80cfb8e0aa8a863733da6d48f5ae5be2dd5b0b2e1e232c19dc7fd5f00` |
| `gui/static/managed-engine-builds.js` | `d4f2c61ea7a643943d34298e91c254c3e50cecfdf5b5fbe79d8fadbdc115f34d` |
| `tests/js/ngg_view_tools.test.cjs` | `300c83018b90ef6cb2593a2b5c4ad2c52be89a05d3b3861d80883f3e2705920f` |

References used for the existing vendor's presentation API: [Three.js WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer.html), [Material](https://threejs.org/docs/pages/Material.html), [OrbitControls](https://threejs.org/docs/pages/OrbitControls.html). WebGL2 is required; renderer failure leaves exact artifacts and QA available rather than claiming a successful display.

## Use

Open a retained completed component/nozzle candidate, then its 3D-preview button. Projection, presets and style appear at the top; expand the named groups for parts/colour, section, auxiliary/detail or exploded/broken layouts. **Expand 3D viewer** opens the inspection sidebar; Escape returns to the workbench. Save any unrelated form edits before reloading an already-open page to load these frontend changes. No backend restart is necessary for these static assets.
