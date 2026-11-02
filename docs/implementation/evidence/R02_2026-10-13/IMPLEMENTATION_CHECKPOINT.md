# R02 Visualization and Graphs — implementation checkpoint

## Source/library selection

Authenticated read-only GitHub CLI identified account `trishul4kumar-ui` and enumerated its starred repositories. Scientific visualization candidates included `matplotlib/matplotlib`, `pnkraemer/tueplots`, `vispy/vispy`, `pyqtgraph/pyqtgraph`, `pyvista/pyvista`, `marcomusy/vedo`, `visit-dav/visit`, `datoviz/datoviz`, `fastplotlib/fastplotlib`, `K3D-tools/K3D-jupyter`, `widgetti/ipyvolume`, `molstar/molstar`, `MPanknin/kiln-render`, and `alandefreitas/matplotplusplus`. Starred repositories informed the assessment; their code was not copied into COSMOS or installed automatically.

Chosen implementation: **ECharts 6.1.0** SVG renderer for the existing embedded vanilla-JS desktop surface; **Three.js 0.186.0** and OrbitControls for explicit user-requested Knowledge spatial navigation. Python/Qt/Jupyter/large-field visualization packages are not needed for these finite 2D source profiles. Future large engineering fields still need actual measured runtime/workload qualification, not a library-only claim.

Primary references: [ECharts release](https://github.com/apache/echarts/releases/tag/6.1.0), [renderer guidance](https://apache.github.io/echarts-handbook/en/best-practices/canvas-vs-svg/), [Three.js release](https://github.com/mrdoob/three.js/releases/tag/r186), [OrbitControls](https://threejs.org/docs/pages/OrbitControls.html), [GPU disposal](https://threejs.org/docs/pages/WebGLRenderer.html). Local npm version-pinned vendor assets, upstream/local hashes and modification declarations are in `gui/static/vendor/manifest.json`. Preserve ECharts Apache-2.0 LICENSE/NOTICE and Three.js MIT LICENSE. `scripts/vendor_visualization.py` reproducibly fetches official HTTPS archives and localizes OrbitControls' module import. Certificate verification is never disabled; OS curl trust was used after the Python runtime's CA bundle failed verification.

## Implemented boundaries

- `systems/visualization/plots.py`: detached read-only source projections for current nozzle/cooling profiles and existing P09 radial temperature/reference, residual normalization and signed conservation histories. Explicit axes/units/model/source hash/freshness/verification/validation/unknown uncertainty. Stale/failed/missing/nonfinite input does not masquerade as a current plot. No new physics/solver or invented 3D field/CFL.
- `api/visualization_workbench.py`: authenticated GET-only projections from existing source services; no source writes, client success flags, raw paths or external network. Simulation source must be completed/current and actor-owned.
- `gui/static/workbench/visualization.html`, `gui/static/visualization/view.js`, `styles.css`: dedicated workspace, design/run source selection, scales, source inspector, exact-row paged table, zoom reset and export controls.
- `gui/static/visualization/knowledge-graph.js`: source-backed Three.js graph, accessible source node/edge list, nonphysical deterministic layout, detached original metadata selection, bounded data, fallback/reduced-motion/visibility/resource disposal. See `KNOWLEDGE_GRAPH_ADAPTER.md`. Integrated through `maharshi.js`; preserved legacy ForceGraph only for module-load failure.
- `chart.js` and scientific chart tests: delegated finite adapter implementation, verify its handoff and exports before acceptance. View currently expects UMD `window.ScientificChart` with `setData`, `resize`, `dispose`, `resetZoom`, `exportSVG`, `exportCSV`.

## Verification / next work

Source/API/auth focused group **15 passed**; Knowledge adapter **19 passed**, actual local r186 module import PASS. Ruff and Mypy checks described in R01 checkpoint. No final institutional-quality, responsive, accessibility, measured-performance, exact-export or native pywebview acceptance claim yet.

Disposable UI QA fixture helper: `preview_smoke.py` uses only a newly owned `/private/tmp/cosmos-r02-preview.*` root and localhost port 8844. A synthetic VIEWER login was reached through the in-app browser; actual scientific chart and 3D integrated visual inspection are still pending. Fixture outputs are explicitly synthetic software QA, not physical evidence. Do not expose its fixture account/server publicly. User's pre-existing 8787 server is untouched.

Resume: confirm chart handoff, rerun all JS/Python/Ruff/Mypy checks, inspect actual 2D plots and Three.js graph in browser and native webview, test log rejection/export source sidecars/fallback/responsiveness, collect screenshots and bounded performance measurements. Then update acceptance and continue R03. No commits/pushes/installer signing or production publication authorized by this turn.
