# Engine-specific R08 acceptance: exact remaining inputs

The nominal diagnostic of saved engine commit
`06f920dc-ff93-4aa3-8c74-a08c43f2bac3` passes. It is not an accepted
intended-use qualification. The immutable input/report identities are in
`CLOSEOUT_QUALIFICATION.md` and `output/r08-saved-engine-nominal-final-2026-10-25.xml`.

## Verified nominal reference inventory

Independent formulas agree with the exact BREP areas of all 16 source parts;
the largest relative difference is approximately `5.04e-15` (floating-point
roundoff, not a manufacturing tolerance). Independent STEP/STL software checks
also pass. Areas below are rounded display values, not replacement reference
values for a future policy. Ninety-seven nominal source-bound witness spans
were identified; this is not approval of their engineering coverage or limits.

| Exact source part | Nominal surface area [m²] | Nominal witness count |
| --- | ---: | ---: |
| collector-mount-bolts | 0.102063554 | 17 |
| fuel-supply | 0.004183596 | 1 |
| gas-joint-groove | 0.066129758 | 30 |
| head-mount-bolts | 0.090651970 | 29 |
| illustrative-sector-cooling | 0.242168838 | 1 |
| lower-coolant-header | 0.029343585 | 9 |
| oxidizer-supply | 0.004693791 | 1 |
| return-collector | 0.001349880 | 1 |
| return-elbow-a | 0.001032996 | 1 |
| return-elbow-b | 0.001032996 | 1 |
| return-elbow-c | 0.001032996 | 1 |
| return-elbow-d | 0.001032996 | 1 |
| return-head | 0.001349880 | 1 |
| return-inward | 0.003119664 | 1 |
| return-outward | 0.001243518 | 1 |
| return-over-flange | 0.005420127 | 1 |

The saved model exports metal-only bodies. A coolant-volume study needs an
explicitly revised model with the required fluid-domain outputs and new QA;
the software cannot infer/pretend those outputs are present in this revision.

## Inputs/decisions needed to close the engine gate

1. **Intended use and accountable reviewer.** Name the specific geometry-analysis
   preparation use and a genuine different authorized engineer. Software-test
   accounts are not acceptable substitutes. Manufacturing/hot-fire acceptance
   is outside this profile.
2. **Tolerance basis.** Supply or approve a revisioned drawing/analysis requirement
   for each part's volume/area/dimension/position and representation errors.
   Geometry source/export tolerances and nominal formulas alone do not specify
   acceptable engineering deviations. No universal tolerance is installed.
3. **Critical coverage.** Approve witness locations and admissible spans for
   chamber/throat/nozzle hot-wall ligaments, channel floor/roof/ribs and header
   connectivity, injector fuel/LOX ports and separating webs, flange lands and
   blind groove floor, pipe ends/bend walls and mating interfaces. In particular,
   the automatically identified single cooling-body wall witness is NOT adequate
   evidence of full channel/roof/rib coverage. Add explicitly reviewed locations
   within the declared per-part/overall capacity, or separately scope components.
4. **Materials, selections and mesh intent.** Name required metal/fluid regions,
   exact study surfaces, minimum resolved features, maximum edge/curvature
   targets and cell budget with applicability sources. Material labels are not
   sourced temperature-dependent properties or allowables. R08 creates no mesh.
5. **Feasible refinement scope.** Approve deliberate exact component submodels or
   another separately qualified capacity plan. The whole-engine 0.6 mm PicoGK
   build already contains 3,694,536 triangles against a 4M limit. Finer whole-engine
   feasibility is not proven. A different selected output set is a different
   source/model; every result must retain that identity. Component passes do not
   automatically accept the entire assembly.
6. **New policy-bound captures and actual decision.** Save the approved policy
   BEFORE every new analytic/PicoGK capture; evaluate its explicit three-grid
   campaign and investigate every failed/local/outlier check. A different active
   authorized engineer must bind the exact terminal report hash/head and declare
   coverage, limitations and the decision. Accepted export remains guarded against
   later source/method/runtime drift, failed topology and withdrawal.

No production data was edited to complete this inventory. No actual engine
intended-use policy or independent acceptance was recorded. These pending
inputs are not hidden implementation claims or a reason to silently start R09.
