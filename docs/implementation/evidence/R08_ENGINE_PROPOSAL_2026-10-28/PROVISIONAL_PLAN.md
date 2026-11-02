# R08 engine-specific qualification proposal — DRAFT-2

28 October 2026. **For owner approval only. Not installed, executed or accepted.**

The user requested a provisional plan on this date. This document does not
record technical approval or independent review. The machine-readable approval
target is `PROVISIONAL_PLAN_V2.json`. Earlier drafts in this folder are superseded.

## 1. Recommended intended use and explicit exclusions

Propose **geometry-analysis preparation of the exact saved preliminary engine**:
dimensional/representation comparisons, named source surfaces and virtual
mechanical-layout studies. Precision analytic OCCT geometry is the proposed
baseline. PicoGK remains the native implicit generator, with a separately
declared per-component three-grid qualification/screening campaign.

This is not manufacturing, seal selection, leakage/pressure integrity, material
allowable qualification, coolant-flow continuity, CFD/FEA, hot-fire approval or
physical validation. The saved revision has sixteen metal outputs; no coolant
volume is silently added. A fluid-volume study needs a separately approved
source revision and new qualification.

**No automatic fallback:** an analytic pass does not accept the implicit model.
A failed implicit comparison stays failed. If only analytic geometry can meet
the approved budget, the owner/reviewer must explicitly decide the intended-use
scope or authorize separately qualified capacity/algorithm development. R08 is
not automatically closed for both representations.

## 2. Exact source and preservation

- Saved engine commit: `06f920dc-ff93-4aa3-8c74-a08c43f2bac3`.
- Capture SHA256: `58761b31a87a729cd207d6cbda6a1bf110771e3b3835e6355788a8504e5fbb86`.
- Original native count baseline: `output/picogk-components-2026-10-24/final-generation-evidence/summary.json`;
  its input checksum binds the same capture.
- Original source tolerance: 1 micrometre; original export setting: 150 micrometres.
- All sixteen original parts, nominal parameters and world placements are retained.
- Proposed child specifications select one exact existing output feature each.
  Offline compilation verifies equality of each resulting `Part` with the parent
  part. This is not automatic engine-assembly acceptance or a live source edit.
- Child export settings are proposed at 8.75–25 micrometres; their explicit
  changes create new model identities. Original captures and receipts are not
  retroactively approved or resealed.

## 3. Proposed numerical budgets — approval required

These are **authored provisional numerical-error allocations for the above
geometry-only use**, not values prescribed by a standard, drawing, material
certificate, NASA or a seal supplier. They may be rejected or revised *before*
the final policies/builds are captured. Do not loosen them after observing a
failed result.

For each individual source-bound local span `s`:

- Proposed allowed span error: `Delta = min(0.100 mm, 0.05 × s)`.
- Proposed span interval: `[s − Delta, s + Delta]`.
- Proposed maximum nearest-surface endpoint error: `Delta / 2`.
- Proposed analytic export deflection: the lesser of the existing 0.150 mm
  setting and one half of the strictest endpoint budget for that component.

The half-budget for each endpoint is a geometric error allocation: two endpoint
errors can add in the measured span. It is not proof that meshing achieves the
budget or that the chosen feature dimension is safe.

Proposed per-component global comparisons:

- Straight/elbow pipes: 0.2% relative volume and 0.5% relative area.
- Chamber/cooling, manifolds and grooved injector: 0.5% volume and 1.0% area.
- Centroid, bounds and sampled/direct surface-distance ceilings: 0.050 mm,
  with the stricter local endpoint/span requirements retained separately.
- Topology is not a percentage allowance: required bodies, watertight/manifold
  conditions, orientation, independent reimport and semantic mapping must pass.

Nominal references are the preserved source and independent analytic formulas,
already checked against exact BREP areas in the 25 October diagnostic. That
agreement is not an engineering tolerance or physical measurement.

## 4. Proposed critical-feature coverage

The JSON contains **960 nominal source-bound witnesses in 73 batches**, covering
all sixteen parts. Each batch has at most 32 witnesses, preserving the current
R08 per-part limit rather than silently increasing it. Source endpoint residuals
are at most approximately `6.03e-17 m`; this checks nominal-coordinate membership,
not the accuracy of any new generated mesh.

- Chamber/cooling body: all six channels at five sections — chamber, convergent,
  throat, divergent and nozzle exit. Five groups of thirty witnesses cover hot-wall
  radial spans, roof radial spans, channel radial depth, channel-width chords and
  channel-to-channel endpoint chords.
- Injector/grooves: every fuel/LOX/fastener bore at 10/50/90% of its through-metal
  extent in two cross-section directions; named groove widths, four-azimuth blind
  floor and depth-edge checks; retained source dimensions. There are 190 witnesses
  in eight batches for the grooved injector.
- Distributor head: every inlet/outlet/fastener bore, plenum interfaces,
  front/back webs, outer lands and the fuel/LOX separating web at multiple sections
  and quadrants — 199 witnesses in ten batches.
- Cooling headers: channel-sector depth/width sections, inlet/outlet/bolt bores,
  plenum inner/outer lands and front/back webs. The collector has 130 witnesses
  in nine batches; the lower header has 82 in eight batches.
- Each straight/elbow pipe: nineteen proposed wall/bore/source-span witnesses
  across three interior sections and multiple orientations. End-connection fits
  and axes remain separate assembly-inspection checks, not inferred from these
  interior measurements.

Important measurement semantics:

1. Radial wall spans are **not minimum normal thickness** on a sloped contour.
2. A channel/rib endpoint chord is **not arc width or proof of a material ligament**.
   Some rib chords can cross the gas bore. The JSON labels this explicitly and
   retains a nominal arc reference; no rib-thickness certification is claimed.
3. Inclined-bores have a true circular diameter normal to the axis, but a plane
   section can be elliptical. The major cross-section spans are labelled as such.
4. Source-selected unperforated header lands retain their azimuth and 33 sampled
   source-line membership checks. This is not a global minimum-thickness proof.
5. The proposed coverage needs genuine engineering review. The count of witnesses
   does not prove that every critical location or failure mode is covered.

## 5. Component refinement and resource plan

The original whole-engine 0.6 mm mesh has 3,694,536 triangles. Do not attempt
whole-assembly halving or raise the 4M/256MiB original-STL admission limit silently.
The proposed separate exact-output studies use these explicit coarse/middle/fine
voxel spacings, in millimetres:

- Chamber/cooling: **0.750 / 0.600 / 0.480**.
- Upper collector: **0.500 / 0.400 / 0.320**.
- Distributor head: **0.450 / 0.360 / 0.288**.
- Grooved injector: **0.400 / 0.320 / 0.256**.
- Lower cooling header: **0.300 / 0.240 / 0.192**.
- Each straight/elbow pipe: **0.125 / 0.100 / 0.080**.

Estimate per-part triangle demand as `1.25 × N_baseline × (h_baseline/h)^2`,
using each part's actual retained triangle count. The factor 1.25 is an authored
planning margin, not a bound or safety qualification. Estimated finest demand is
0.55–3.46M triangles per part, below the unchanged cap. Actual geometry may
deviate from inverse-square scaling; only measured attempts establish feasibility.
All three grids together project about 2.74 GB of STL data with this margin,
excluding fields, STEP/BREP, logs, temporary comparisons and app storage.

Propose serial execution, unchanged worker timeout/memory limits, cancellation
and preserved failed attempts; require at least **10 GiB free** before starting.
Only about 7.2 GiB was observed at the final planning check. No user files were deleted.

**Accuracy/resource conflict is unresolved:** these spacings are larger than
the strictest proposed endpoint budgets. A cap-feasible estimate is NOT a
tolerance-feasible campaign. The strict criteria are not relaxed to make the
large implicit components pass. If a part fails, retain the failure and request
an explicit decision on intended use, localized qualification or a separately
qualified new capacity/algorithm profile. No such change is authorized here.

## 6. Assembly interfaces and handoff requirements

Before an engine-level decision, independently inspect the declared pipe/header
connections, cooling collector/body interfaces, head/injector/flange locations,
bolt/gland mappings, source orientation and intentional clearances/interferences.
Propose 0.050 mm center-offset and 0.1 degree axis/angle comparison budgets for
this geometry-only study; these are also unapproved numerical allocations.
Retain exact CAD-inspection results and explicit interface-pair identities.

Global normal wall/rib minima are not certified by the current R08 witness
method. Pressure seals and wet-fluid connectivity are not established by matching
port center coordinates. Any required certification beyond the current bounded
method needs an approved implementation/qualification change, not a positive flag.

Material assignments and study mesh intent remain `null` in the draft. The single
cooling metal output must not silently become two qualified liner/jacket material
regions. A real material-region split is a new source revision. No coolant-fluid
volume, physical boundary condition or generated volume mesh is claimed.

## 7. Governed execution after approval

1. Record approval of this exact plan/hash, intended-use limits, coverage and
   unresolved-scope decisions. Assign real region/mesh intent and a different real
   authorized reviewer. Plan approval alone is not engine acceptance.
2. Save the approved derived models in an isolated campaign project with the exact
   parent source checksum, original placements and explicit changed export settings.
3. Save **all** per-batch policies before any corresponding native build capture.
   Analytic-only and cross-representation policies are different qualifications:
   73 coverage batches imply up to 73 analytic-only plus 73 cross-representation
   policy/evaluation records, not a single undisclosed global check.
4. Reuse each component's one new analytic and three new PicoGK attempts only across
   policies that predate those exact captures and bind the same saved child model.
   This is 16 analytic + 48 implicit native attempts if all reach execution.
   Preserve rejected/topology/resource attempts; do not fabricate missing grids.
5. Retain process time/RSS, all measured local/global deviations, maximum/percentile
   sampled distances, outliers, exact originals, separate source/export hashes,
   units/frames, independent reimport and semantic selections.
6. A genuine different authorized engineer reviews each required batch and the
   assembly/interface ledger. The current per-policy acceptance system does not
   automatically establish whole-engine aggregate acceptance. The engine ledger
   must bind all required model/policy/job heads, report/original hashes and actual
   decisions; no component, batch or failed representation can be dropped.
7. Close engine-specific R08 only for the explicitly accepted intended-use scope
   when every required record/check is satisfied. R09 remains on hold unless the
   user separately authorizes it. Manufacturing/physical validation remain separate.

## 8. Sources and limits of their authority

[NASA NPARC grid-convergence guidance](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)
supports explicit refinement studies, non-integer grid ratios and checking the
asymptotic assumptions before extrapolation. It concerns CFD; it does **not**
certify PicoGK surface accuracy, prescribe the above engine tolerances, or make
three successful geometry runs a certified GCI/Hausdorff result.

[OCCT meshing documentation](https://occt3d.com/dev/doc/overview/html/occt_user_guides__mesh.html)
distinguishes linear/angular tessellation settings and explains their effect on
accuracy and mesh size. This is methodological context, not evidence that the
installed pinned OCCT has been upgraded or that any proposed mesh already passed.

The proposed tolerance numbers and resource margin are clearly identified
engineering judgments for approval, not attributed to these sources. Source
provenance is not a substitute for independent engineering review.

## 9. Decision requested and preparation checks

**Approve or request changes to DRAFT-2 for geometry-analysis preparation only.**
The exact machine-readable approval target is `PROVISIONAL_PLAN_V2.json`, SHA256
`4fe19dc7819794ffc9dd5c596bbdd942b671e5f6a586b1c246dbbae2a69fa90c`.
Approval would endorse the proposed intended use, numerical allocations, coverage
and staged resource-screening approach. It would not remove the unresolved
accuracy/coverage limitations, appoint a reviewer, approve material/mesh-intent
assignments, increase runtime caps, or accept the engine. Those prerequisites
must be resolved explicitly before governed acceptance. Native execution also
requires the declared free-disk threshold and fully specified predeclared policies.

Preparation checks on 28 October 2026: **7 offline planning tests passed**, Ruff
passed, review-canvas TypeScript checking passed, and the existing source-bound
R08 runtime remained admitted. These are not new native geometry campaign
results. No policy was installed, live engine revision changed, independent
review recorded, or R09 started.
