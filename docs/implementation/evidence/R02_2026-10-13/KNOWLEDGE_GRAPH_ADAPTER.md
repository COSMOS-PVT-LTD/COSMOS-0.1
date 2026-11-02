# R02 Knowledge graph adapter

## Delivered scope

Added `gui/static/visualization/knowledge-graph.js` and `tests/js/knowledge_graph.test.cjs`. Existing GUI integration, server, HTML, scientific models, Knowledge ingestion and vendor modules were not modified by this subtask. This is a visualization adapter, not new engineering analysis or Knowledge validation.

The adapter uses local Three.js r186 modules (`../vendor/three/three.module.js`, `../vendor/three/OrbitControls.js`). It does not fetch resources or fabricate example nodes or relationships. Source node records and directed relationships are preserved as detached, frozen JSON records. Backend `RELATED_TO` links derived from shared keywords remain such links; they are not recast as causal or experimentally validated relationships.

The Data Visualization guidance influenced the explicit layout disclaimer, inspectable source records, accessible non-WebGL presentation, finite-data refusal and separation of source semantics from visual positions.

## Integration contract

```js
import { KnowledgeGraph3D } from './visualization/knowledge-graph.js';
const graph = new KnowledgeGraph3D(canvas, { onSelect, onStatus });
graph.load(graphPayload);
graph.resize();
graph.dispose();
```

- `load(payload)` returns `true` for valid source data, including accessible-list fallback when WebGL is unavailable. Invalid data returns `false`, clears previous graph data/display and reports a diagnostic.
- `onSelect(record)` receives a detached original source node record. It adds no visual coordinates, validation claims or inferred source fields. Connect this to the existing source-backed inspector.
- `onStatus(status)` receives `{ state, code, message, renderer, nodeCount, edgeCount, layoutScope, physicalUnits: false, scientificValidation: false }`. `renderer` is `three-webgl2` or `accessible-list`. It can fire during construction; the callback must not assume the graph variable has already been assigned.
- `resize()` is safe when WebGL is unavailable; `dispose()` is idempotent.
- Exported pure preparation/validation helpers support data-contract tests independently of rendering.

`layoutScope` states: “Spatial layout only: positions, proximity and link lengths are not physical units, similarity scores or engineering validation.” Deterministic ID-stable layout is for navigation only. The 3D links are lines, not arrowheads; the adjacent accessible relationship list supplies exact direction, type and source shared terms.

## Safety, accessibility and lifecycle

- Rejects malformed arrays, duplicate identities, dangling edges, conflicting supplied counts, nonfinite JSON values and out-of-bound layout coordinates; it does not silently invent or drop connectivity.
- Bounds: 1,000 nodes, 5,000 edges and 8 MiB serialized payload. The source-backed node/relationship lists paginate 25 entries at a time without truncating the accepted data. These are protective limits, not benchmarked performance guarantees.
- Always-available keyboard node buttons, plain-text labels/summaries and relationship lists permit use without WebGL. Selection survives source-preserving reloads when the selected identity remains present.
- Pointer selection distinguishes clicks from orbit drags. Reduced-motion preference disables damping; there is no automatic spin or perpetual force simulation.
- Rendering is demand-driven and pauses when explicitly paused, hidden or offscreen. Device pixel ratio is capped at two.
- Initial WebGL failure, rendering failure or context loss releases GPU resources and retains the accessible source list with an explicit diagnostic.
- Disposal cancels queued frames, disconnects observers, unregisters listeners, disposes controls, geometry, materials, instancing and renderer resources, removes injected DOM and restores original canvas attributes/styles.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| Focused Node data/DOM/Three lifecycle unit tests | 19 passed, 0 failed, 0 skipped | `knowledge-graph-tests.log` |
| JavaScript syntax checks for adapter and test | Passed | `node --check` on both files |
| Actual local r186 ESM import and pure preparation smoke | Passed | `knowledge-graph-module-smoke.log` |

Command for focused tests:

```sh
/opt/homebrew/bin/node --test tests/js/knowledge_graph.test.cjs
```

The unit tests inject DOM, renderer, controls and observer mocks. They verify data preservation/refusal, source counts, fallback, paging, safe text, focus/selection, click-versus-drag behavior, visibility/pause/reduced motion, resize and cleanup. The separate smoke imports the actual vendored modules and prepares one supplied source node.

These checks do **not** establish actual WebGL rendering quality, browser accessibility conformance, large-graph throughput, GUI navigation integration, scientific model validity or physical readiness. Root-owned acceptance must exercise the integrated real Knowledge page in a browser: actual source payload, node inspector, relationship paging, keyboard access, narrow layout, reduced motion, pause/tab visibility, resize, unavailable WebGL and navigation/disposal.

API references used for implementation: [WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer.html), [OrbitControls](https://threejs.org/docs/pages/OrbitControls.html), [Raycaster](https://threejs.org/docs/pages/Raycaster.html), [InstancedMesh](https://threejs.org/docs/pages/InstancedMesh.html). Installed local source reports revision 186; live integration uses the repository-vendored modules, not a CDN.
