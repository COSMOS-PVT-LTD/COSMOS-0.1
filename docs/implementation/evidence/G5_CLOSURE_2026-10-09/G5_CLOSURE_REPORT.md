# G5 geometry software-qualification closure

**Decision: PASS for the bounded local macOS software-fixture gate. P08 may begin.**

No physical, engineering publication, native distribution, cross-platform or human owner acceptance is claimed. Original P07 PARTIAL decision and failed artifacts remain immutable historical evidence; `before/` retains its sealed implementation. This closure overlays, not rewrites, that result.

## Executed evidence

- `native-final.log`, `native-tests.xml`: **56 passed**, 111.35s: all 54 original actual-native checks plus two genuine wrong-radius rejection tests. No mocks for native geometry/reimport.
- `occt-focused.log`: **8 passed**, all seven analytic STEP positive fixtures and combined sphere STEP/STL.
- `focused-tests.log`: **271 passed, 2 skipped** (independent optional prerequisite tests); `ruff.log`: PASS.
- `candidate-reaudit.json`, `reaudit.log`: 30 immutable records reparsed; source/export hashes and all independent QA decisions repeated; five resolution-convergence series preserved. All eight OCCT positives accepted; expected coarse/degenerate/empty negatives remain refused. No published artifacts.
- `native-config.json`, `run3/native-config.json`: 94 current exact runtime/source hashes. Native dependencies remain the pre-existing isolated developer installation, not app dependencies.

## Root causes and actual fixes

| Failure | Evidence | Fix (no tolerance relaxation) |
| --- | --- | --- |
| STEP union/difference samples exceed 1um | Metre import forward error 1.546um; same STEP imported in native mm ~0.000612um | `plugins/geometry/workers/step_reader.py`: native-mm import, explicit conversion of **all** volume/centroid/bounds/samples/projections back to SI |
| Trimmed Boolean bounds inflated or sampled inaccurately | Default bounding boxes include carrier extents; independent fixed-deflection trimmed bounds recover actual body extrema | Explicit OCC STL bounds with 0.5um absolute deflection. QA still requires <=1um. This is sampled bounds, not a certified Hausdorff bound. |
| Union spherical face reported Unknown | Actual `ADVANCED_FACE` references `SPHERICAL_SURFACE`; Gmsh 4.15 source exact `DynamicType` classifier omits trimmed wrapper types; principal curvatures are constant spherical values | Bounded actual STEP carrier-reference proof **and** independent 18 principal-curvature observations per unknown face. Raw Unknown retained; no general Unknown whitelist. Unknown with nonspherical carriers cannot pass. |
| Sphere STL has 2 zero-area triangles, 4 nonmanifold edges, 2 orientation errors; 1.735um forward deviation | Native-mm mesh/explicit SI encoding at declared 60% chord budget: 167,316 triangles, zero topology defects, max forward 0.828um, reverse 0.445um | `plugins/geometry/workers/stl_encoding.py`: versioned exact-zero exclusion <=1%; no epsilon/welding/smoothing, no surviving vertex changes beyond declared mm->m float32 encoding; normals reflect surviving winding. Tighten generation, not QA limits. |

`occt_worker.py`: explicit local/write STEP units (1mm and 1000mm), initialized metre header, no geometric B-rep scaling; native precision conversion. A diagnostic run exposed an incorrect header-only unit setting and was stopped without acceptance; `run1/` and its log preserve that failed experiment. Final actual reimport verifies dimensions and metre headers. `CAD_VERSION` is bumped to `occt-7.8.1.ocp-7.8.1.1.g5v2`; old semantic generation is not relabelled.

Additional correctness: reverse closest-point checks now reject projections outside trimmed faces, as required by the API; no untrimmed-carrier shortcut. Private native STL intermediate cleanup includes failure/cancellation. Two genuine 11mm-radius solids still fail the 10mm reference policy; no artifacts accepted/published.

## Unchanged limits and release boundaries

STEP relative volume <=1e-7; centroid/bounds/forward/reverse <=1um. Analytic STL <=200k triangles, exact manifold/orientation checks, 1.5um forward / 2um reverse, predeclared volume/centroid bounds. PicoGK h/requested tolerances and explicit conditioning policy unchanged; coarse intersection still rejects rather than silently refining.

Native RSS accounting covers the worker leader only; POSIX process isolation is not a hostile-code filesystem/network sandbox. Full regression/physics parity continues in P08. Gmsh tool/API/process independence shares OCCT implementation; analytic reference formulas provide another verification leg. No arbitrary engineering geometry or trusted publication is available.

Gmsh API and bounding/closest-point semantics: [official documentation](https://gmsh.info/doc/texinfo/). Classifier diagnosis verified against [official pinned 4.15.0 source archive](https://gmsh.info/src/gmsh-4.15.0-source.tgz), `src/geo/OCCFace.cpp:342-360`; sampled installed API behavior, not inferred from a newer version. No dependency upgrade or license/distribution approval performed.
