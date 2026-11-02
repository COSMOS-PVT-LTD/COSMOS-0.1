# Compact 1.5 kN engine regeneration

30 October 2026. User explicitly resumed whole-engine research generation and
requested matched thermal/feed analysis. This does not resume R08 engineering
qualification, install a desktop application, select supplier hardware, or approve
manufacturing/hot-fire use. Existing app data and earlier baselines are retained.

## Exact design, not a substitute fixture

- Project: `bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.
- Selected candidate commit: `dcf4adff-9540-443e-9e6e-a4775fab92fd`.
- Development selection commit: `2afd02ce-36b8-4939-b71b-c5f8d7872d6a`.
- Component source commit: `06f920dc-ff93-4aa3-8c74-a08c43f2bac3`.
- Exact bound propulsion commit: `3ce745d6-445a-4fca-81af-be9c09f200dc`.
- Recipe SHA256: `a357d5c073e62a95b872eb6f210a3537d78d67bd9ad36f82a86166825df478f5`.

`scripts/prepare_compact_regeneration.py` reads the existing store in SQLite
read-only mode, verifies immutable blob hashes and all three selected heads,
and exports the exact approved research input. It does not silently use the
newer, different propulsion head or create a new saved owner-project revision.

New output root:
`output/engine-redesign-regenerated-2026-10-30/`.

The approved compact candidate integrates sixteen source metal parts into six
metal groups. It contains the existing injector/head geometry, cooled chamber,
throat/nozzle, integrated collectors, continuous fuel-return body, supply bores
and retained interface/groove envelopes. A group name is not selected bolt/seal
hardware. The default compact candidate retains the source gas path and sizes;
regeneration is not a new efficiency optimum or proof of functional hardware.

## Geometry execution and independent inspection

The OCCT research build completed. `occt/UNQUALIFIED-assembly.step` is a complete
six-solid assembly, with per-group BREP files alongside it. A fresh independent
STEP reader confirmed millimetre file units, six valid solids, source bounds,
and volumes matching independent recipe integrals. The maximum relative volume
error was approximately `7.74e-13`, below the existing generator's numerical
software tolerance `1e-6`. This numerical tolerance is not an engineering drawing
or manufacturing tolerance. Sorted-volume part association is not semantic face
or solid identity transfer.

The native PicoGK 0.5 mm run reached the existing 600-second execution bound.
Its incomplete outputs and log are retained; no completed native manifest or
successful geometry claim is attached to that attempt. A separate 0.8 mm research
attempt completed with the same recipe. Its 2,053,040 native triangles passed
the independent basic topology checks. Coarser voxels do not inherit a finer
attempt's accuracy, and no resolution here establishes critical-feature fidelity.

The performance bottleneck was repeated evaluation of the identical 44-station
channel meridian for six sector cuts. Only the unqualified `pico-compact` extension
was changed: strict identical-profile/transform detection factors the shared
meridian using `min_i max(M,W_i) = max(M,min_i W_i)`, removes hot-loop LINQ closure
allocations and preserves first-equal-minimum signed-zero behaviour. The included
original admitted component-field source and old binaries were not modified.
A new Release worker was compiled in the campaign output, not installed.

The first managed comparison exposed signed-zero bit differences; its failed
receipt and first worker are retained. After correction, all 25,572 actual-case
samples across six groups (including 5,062 reference tie-band samples) matched
the original raw double, classification and float32 kernel results bit-for-bit,
with maximum residual error zero. This is software evidence, not a mathematical
certificate of all points or engine fidelity acceptance.

The new worker then completed a **0.6 mm** full native build within the unchanged
600-second, 120-million-cell and 4-million-triangle limits. It produces
**3,654,936 native triangles** and named native VDB groups. Independent inspection
found one connected, closed, consistently oriented component per metal group,
with no encoded duplicate/degenerate faces or edge-incidence/orientation defects.
The largest observed per-part volume difference from the independent recipe was
approximately **0.622%**, reported as an observation with no invented intended-use
acceptance threshold. Final names/hashes and actual floating-point voxel size are
in STATUS.json and the native manifest. The 0.5 mm timeout was not relabelled as
a successful build or deleted to hide the failure.

`scripts/inspect_compact_regeneration.py` independently inspects STEP reimport
and unchanged native STL spans/topology/integrals. It never repairs geometry or
grants R08 acceptance. Display-only reduction, when available, keeps the original
native VDB/STL/STEP intact and explicitly retains source hashes and its method.

## Matched thermal/feed result: BLOCKED, not solved

`matched-analysis-verified.json` is a fresh exact-candidate applicability result,
not a completed hot-wall/feed solution. All computed heat, wall temperature,
coolant-outlet temperature/pressure and full operating-point fields remain null.
The blockers are software/model/data gaps, independently of future experiments:

1. The six real channels are variable radial-depth **axial sectors**, not the
   existing constant-area flow-normal thermal cells. No automatic rectangular
   surrogate or circular correlation using axial `4A/P` is applied.
2. An applicable sector friction/convection law and matched chamber/convergent/
   throat/nozzle hot-gas boundaries are not supplied.
3. Retained GRCop-42 research conductivity spans 298.15–810.95 K. The present
   conservative single-phase methane wall model requires a coolant-contact wall
   below 135.35123 K. These particular model/data domains do not overlap. This is
   not a prediction that the real engine wall has either temperature. The code
   does not extrapolate or replace the alloy to manufacture a solution.
4. Material machine/process/HIP/heat-treatment condition remains unresolved;
   research curves are not selected engine allowables. Rib/roof/bimetal conduction
   and cooled-wall strength are not represented by a planar ligament calculation.
5. Collector, entrance, bends, distribution, valve and regulator characteristics
   are not provided. The return route is 0.3116838287 m of centreline with a 7 mm
   bore; nine CAD primitives do not imply nine real fittings or fully developed
   long-pipe behaviour in every segment.
6. Heated-injector density/enthalpy, combustion heat withdrawal, CEA recomputation
   and full engine mass/pressure closure are not coupled to this candidate.

The retained NIST liquid surface covers methane 111.15–133.15 K and 5–8 bar.
Raw isobar/saturation checksums were verified and the liquid surface reconstructed
from those TSV bytes, matching the retained derived record. The supplier PDF and
original material-transcription bytes were checksum verified, and staged curves
were independently restaged from that original-unit transcription. The numerical
PDF transcription was not independently re-extracted in this campaign. These
limitations are explicit in the assessment's provenance. No live input was widened
or installed and no generated graph was rebound to an older thermal result.

## Source changes

- `systems/geometry/compact_analysis.py`: pure source-bound readiness diagnostics.
- `scripts/prepare_compact_regeneration.py`: read-only selected-source export.
- `scripts/assess_compact_regeneration.py`: raw-byte verification and source-bound
  scientific applicability assessment.
- `scripts/inspect_compact_regeneration.py`: independent native artifact checks.
- `scripts/prepare_compact_display.py`: separately labelled display derivative.
- `scripts/view_compact_regeneration.py`: terminal-launched read-only native
  viewer, reusing COSMOS's offline Three.js/CAD controls, without installation.
- `scripts/finalize_compact_regeneration.py`: checks the selected evidence and
  unchanged source heads, hashes artifacts, and records partial request completion.
- `gui/static/engine-redesign.js`: accepts explicitly source-hashed display
  derivatives in addition to bounded original research STL. Derivatives cannot
  present themselves as original native engineering CAD.

The frozen layering and old admitted native generators remain unchanged.
Engineering acceptance, physical validation and R08 remain separate and pending.

## Verification and launch

The verification skill traced exact saved selection -> source/recipe checks ->
native generation -> independent artifact checks -> hash-checked display derivative
-> real Cocoa/WebKit 3D rendering. This viewer reads generated files and public
offline assets only; it does not open accounts, write projects or install an app.
The section-controls panel was opened through native UI automation. Applying a
section was not separately verified in this timed capture. Existing CAD control
regressions passed; display sections are not capped CAD solids or engineering
section drawings.

- 72 focused Python checks plus 3 explicitly enabled small native checks passed
  (75 total selected cases; not a full repository test run).
- 32 selected JavaScript checks passed.
- Final independent engine STEP/native-mesh software checks passed.
- The actual final native viewport rendered six parts and 199,792 separately
  reduced display triangles, orthographic/isometric with XYZ references.
- `REGENERATED_ENGINE.png` is the actual final source-native render, not an AI
  illustration. The earlier coarse screenshot is retained separately.
- No app installation, live data migration, baseline overwrite, commit, push,
  remote CI, R08 acceptance or physical-validation action was performed.

Run the model viewer from Terminal:

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
.venv-release-p12/bin/python -m scripts.view_compact_regeneration --campaign output/engine-redesign-regenerated-2026-10-30
```

Close the native window to stop its task-local viewer. It is a read-only view of
these generated artifacts, not a replacement installed COSMOS application. To use
the existing candidate editor instead, load the exact selected project/candidate,
then choose `display/manifest.json` and `display/DISPLAY-ONLY-export.stl` in its
local research-artifact controls. No uploaded mesh becomes engineering-accepted
or a completed thermal result by being displayed.

Selected artifacts:

- `output/engine-redesign-regenerated-2026-10-30/occt/UNQUALIFIED-assembly.step`.
- `output/engine-redesign-regenerated-2026-10-30/picogk-optimized-0p6mm/UNQUALIFIED-source.vdb`.
- `output/engine-redesign-regenerated-2026-10-30/picogk-optimized-0p6mm/UNQUALIFIED-export.stl`.
- `output/engine-redesign-regenerated-2026-10-30/independent-inspection-final.json`.
- `output/engine-redesign-regenerated-2026-10-30/matched-analysis-final.json`.

**Readiness decision:** whole saved CAD regeneration is delivered as research
geometry. The requested matched thermal/feed **solution remains unfinished**.
The next work is the actual variable-sector/phase-aware thermal-hydraulic model,
compatible condition-specific material/property basis, physical-route response
data and full heated operating closure. Neither free storage nor successful CAD
generation supplies those missing scientific requirements.
