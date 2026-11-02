# Reference-inspired mechanical 3D workspace

Date: 2026-10-22. Scope: current user's professional CAD/scientific workspace request. R08 remains on hold; no scientific model or engineering acceptance state was changed.

## Implemented

- Compact document/source bar and functional View, Assembly, Inspect and Appearance ribbons.
- Neutral graphite live model canvas, plus dark/light canvas choices.
- Collapsible retained-body browser with exact IDs, filtering, visibility and selection.
- Source-bound part selection linked to amber mesh-edge highlighting and display properties.
- Existing projection, axonometric, section/slab, auxiliary, detail, broken/exploded, eight-style, opacity and colour tools preserved.
- Real Three.js X/Y/Z axes at **source world origin (0,0,0)**, independent of illustrative part translations. Red X, green Y, blue Z, labelled in the viewport.
- Camera-linked orientation widget with six signed **view-from** directions. The camera is placed on the selected side of the pivot, not claimed to point along the same signed ray. Pole labels separate to remain clickable.
- Optional XY/XZ/YZ world-reference grids; spacing follows a bounded SI 1/2/5/10 progression. Displayed mm spacing does not convert source geometry.
- Orbit/pan/select modes, zoom commands, projected-bounds fit, expanded modal and keyboard controls.
- Narrow-layout container queries and one-active-panel/overlay behaviour, preserving canvas space.
- Offline Tabler v3.44.0 icons, exact upstream SVG assets with the MIT licence in `gui/assets/cad-icons/LICENSE`.

The reference is used for layout and interaction inspiration. BricsCAD branding, gear raster imagery and unsupported sketch/solid/constraint/BOM commands were not copied or fabricated. The grey background is a real renderer background; the engine is retained geometry, not an image.

## Main files

| Path | Responsibility |
| --- | --- |
| `gui/static/ngg/viewport.js` | Shared scene/reference axes, orientation, selection highlighting, navigation and ribbon/tree/properties shell |
| `gui/static/ngg/styles.css` | Scoped industrial workspace layout, density, panels and responsive rules |
| `gui/static/component-geometry.js` | Exact retained component job identity passed into the workspace |
| `gui/static/managed-engine-builds.js` | Exact retained nozzle identity passed into the same workspace |
| `gui/static/ngg/view.js` | Exact fixture identity passed into the same workspace |
| `gui/assets/cad-icons/` | 21 official SVG icons and their licence |
| `tests/js/ngg_cad_workspace.test.cjs` | 11 new reference-frame, grid, fitting, selection, navigation, source-identity and asset tests |
| `tests/js/ngg_view_tools.test.cjs` | 16 existing focused display/picking/state tests retained |
| `design-qa.md` | Required visual comparison, findings, fixes, evidence and final internal QA result |

No new application routes, persistence authority, external runtime dependency, backend restart or scientific-kernel replacement was introduced. The existing safe asset fallback serves the locally installed icons. Source triangles remain copied/read-only to display operations; helpers are outside the part mesh/picking/export set. Rendering remains event-driven.

## Fresh verification

- **466 JavaScript tests passed**, zero failed/skipped, using the bundled Node runtime and `--test tests/js/*.test.cjs`.
- **15 HTTP tests passed, 2 skipped** for `test_component_projects_http.py` and `test_ngg_http.py`. Skips explicitly require a separately pinned native campaign; no native success is substituted.
- JS syntax check passed.
- Real browser preview: **16 parts, 182,768 triangles, 548,304 original vertices**, retained source unchanged by pan/layout/colour commands.
- Browser-tested all signed axis views, grid, ribbon/tab navigation, part filtering/selection/colour, section inspector, explode/reassemble and all eight render styles.
- Expanded modal focus loop and background inert checked. Docked workspace widths **677 px and 541 px** had no horizontal document overflow. Original shell navigation width **224 px** restored after responsive testing.
- Browser console: no errors/warnings during final checks.
- Internal design QA: **passed** after ribbon/framing, pole-label and narrow-panel fixes; not a formal human usability or accessibility certification.

Native generation was not requalified. The earlier incomplete temporary `OCP.Bnd.Bnd_Box` dependency remains a separate limitation documented in `../VIEW_TOOLS_2026-10-22/IMPLEMENTATION_AND_VERIFICATION.md`. Viewing retained artifacts does not require successful regeneration.

## Evidence / preview

Isolated viewer:
`http://localhost:8896/app/workbench/native-geometry?project=bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.

- Model: `afc95eb3-2d0c-55b7-95eb-2644f67e01d0`.
- Build: `834a6255-f944-50b8-b248-82e8d6a00122`.
- Retained job: `149d6412-5179-4b55-8bb5-e85508a737e3`.
- Screenshot collection: `output/cad-workspace-2026-10-22/`.
- Final screenshot: `10-final-current-cad.png`, SHA256 `78be2e6910d8ab4753804efcacff93a85ee45f7712fc6acdac012b560990745e`.
- Final viewer source SHA256: `b963a81ed902bb698a8c89c7ff35e77c9fb4e8a73744f987de67cd9e8712956a`.
- Final workspace CSS SHA256: `1aafc238b26b7aa5358600110a5b3fae0aebd6c175f9f791c1f5f6bf9bdb9759`.
- New test source SHA256: `e9789ca96a5acadccefb8a844a4b8c85797ff17cf116400715fb8736d7d6462e`.

Source icon provenance: [Tabler v3.44.0](https://github.com/tabler/tabler-icons/tree/v3.44.0), [MIT licence](https://github.com/tabler/tabler-icons/blob/v3.44.0/LICENSE). Existing offline rendering helpers: [Three.js AxesHelper](https://threejs.org/docs/pages/AxesHelper.html), [GridHelper](https://threejs.org/docs/pages/GridHelper.html).

## Preservation

Port 8878 remains owned by PID 77508; it was not restarted or signalled. No owner project, engine source, candidate artifact, material property, seal approval, feed/thermal model or export was rewritten. Protected CEA fixture SHA256 remains `6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`. No commit/push or release was performed; the existing dirty checkout is preserved.

## Use and limits

Open a retained completed candidate and its 3D preview. **Maximize** opens the mechanical workspace; **Restore** or Escape returns it to its prior position. The left rail opens the model browser, appearance, section, layout and help. The ribbon groups commands by purpose. X/Y/Z are source-world directions, not new engine-local frames. Colours, highlight, grids, shortened/exploded layouts and helper axes are presentation state, not material assignment, metrology, structural evidence or an accurate manufacturing disassembly plan.
