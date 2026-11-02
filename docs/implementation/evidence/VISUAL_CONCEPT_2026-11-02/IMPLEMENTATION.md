# Fixed visual concept — 2026-11-02

The Native Geometry workbench has a **Visual concept · discussion only** section.
It displays a fixed exterior illustration with deliberately disconnected surfaces,
arbitrary proportions and two decorative markers. It is not an editable CAD solid,
contains no internal parts or engineering dimensions, and is not a reproduction of
the detailed sketched assembly. No STEP/STL export or project save was added.

`scripts/build_visual_concept.py` uses OCCT in memory for the exterior surface
triangles and invokes `plugins/geometry/workers/visual-concept/` to obtain the
PicoGK decorative-marker mesh. It writes the fixed, pre-generated display asset
`gui/static/visual-concept-data.js` only to a new path. The application serves this
asset and `gui/static/visual-concept.js` only for the Native Geometry page when the
managed-project interface is enabled. Normal viewing does not execute either kernel.

The artwork is separate from the existing saved project, has no data-root dependency,
and does not alter the R08 hold. The supplied-image catalogue is [REFERENCES.md](REFERENCES.md).

## Verification

- PicoGK fixed-marker worker: build passed, zero warnings or errors.
- OCCT and PicoGK both executed in the artwork generation run.
- Actual isolated native COSMOS window: sign-in, Native Geometry, load, fit and
  standard-view controls were exercised; the five-part display rendered.
- The focused native screenshot is [VISUAL_CONCEPT.png](VISUAL_CONCEPT.png).
- Isolated authenticated HTTP integration plus geometry UI checks: 32 passed.
- Display decoder and existing viewer JavaScript checks: 18 passed.
- Scoped Python Ruff checks passed.

To view in the user's normal development workspace, launch the existing source
application, open **Native Geometry**, and choose **Show visual concept**. The
isolated test window runs with a separate local data root; it is not a replacement
for the user's saved project. No application bundle was installed.
