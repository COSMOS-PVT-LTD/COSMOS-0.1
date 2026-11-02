# Joint geometry and approved revised layout - full engine goal remains open

2026-10-21; HEAD293223e plus preserved inherited/local work. R08 HOLD.
No owner-design overwrite, viewer8878 restart, migration, commit, push or
manufacturing release. User approval is for the isolated revised concept study,
not installation, material allowables, hardware or hot-fire acceptance.

## Implemented and verified in this increment

- `systems/geometry/component_model.py`: typed `interface.bolt_pattern` cuts on
  one uniform annular operand. Explicit circle, hole, count and phase; existing
  plenums/ports, annular edges and bolt-to-bolt ligaments must remain resolved.
  Repatterning, unsupported inclined operands and unresolved cuts reject.
- `systems/geometry/joint_layout.py`: exact-source preparation of matching
  upper-header cuts from the actual retained collar. No best-fit bolt circle,
  selected bolt/thread/preload, automatic pressure sizing or owner mutation.
- `systems/geometry/component_joints.py`: actual world-frame coaxial opposed
  contacts, conservative full-circumference radial lands, matching clearance-
  bore axes and injector aperture containment. Separate collar and chamber
  solids are not silently made an integral load path or a sealed joint.
- `systems/geometry/component_interfaces.py`, `api/component_interfaces.py` and
  `gui/static/component-geometry.js`: exact saved-model inspection includes
  these joint findings. CURRENT, geometric connectivity and bolt-axis matches
  remain separate from engine solution, seal/attachment and physical acceptance.
- Closed15/90-degree elbow bounds now use the frozen Core16-significant-digit
  canonical representation. Exact endpoint inputs survive save/reload; outside-
  domain cases still reject. No Core precision change or geometric healing.
- `plugins/geometry/workers/component_step_reader.py`: independent imported
  annular tubes and long cylindrical bores get actual-curvature-local mesh
  refinement. Long-bore4:1 aspect is a meshing trigger, not a flow correlation.
  No triangle welding/deletion, Euler substitution, tolerance widening, new CAD
  healing or resource-cap increase.100k aggregate and30k/body node bounds remain.

## Actual19-body candidate

`output/connected-engine-joints-2026-10-21-v3/` contains proposal, captured cold
source replay, model, interface inspection, native result, review context, BREP,
STEP, STL and checksums. This is **not a fresh CEA/hot operating-point solve**.

| Identity / check | Observed result |
| --- | --- |
| Project | `ae60b08e-babb-43ec-bde1-176bf48ac282` |
| Model | `b4046821-a575-5ab2-9942-da3726d724c2` |
| Model commit | `37a3cbbc-c1b9-45ec-9879-edf71a2d2eed` |
| Cold baseline replay | `7a3aff89-133b-443c-895e-6b9eb4ea8fdb` |
| Build | `abed158d-f039-52a3-8d7e-ec68143789f1` |
| Native job | `d9c1aa6c-1940-4096-95ad-53aad54a5b5b` |
| Native result | COMPLETED; independent STEP and STL QA PASS |
| Scope |19 bodies:13 metal,6 illustrative coolant-fluid domains;177776 STL triangles, below unchanged200000 cap |
| Hydraulic openings |90;16 head/plate mates,12 header/channel mates,8 pipe mates,2 explicit supply boundaries |
| Upper header/collar |8/8 clearance-bore axes match; expected header Euler-30 verified |
| Fuel / LOX topology | Requested regeneration-before-injection and separate direct-LOX geometric routes connect |
| Engineering result | Engine INCOMPLETE; pressure NOT_CALCULATED; glands NOT_GENERATED; seals NOT_ASSESSED; physical validation NOT_PERFORMED |

Files: `PRELIMINARY-CONNECTED-HEADER-BOLTS-source.brep`,
`PRELIMINARY-CONNECTED-HEADER-BOLTS-export.step`,
`PRELIMINARY-CONNECTED-HEADER-BOLTS-export.stl`.

Isolated viewer:
`http://localhost:8894/app/workbench/native-geometry?project=ae60b08e-babb-43ec-bde1-176bf48ac282`.
This is the existing layout with matching header cuts, **not the approved new
separable-head concept CAD**. Earlier8892/8893 viewers/candidates are historical
after the new native identities. Owner8878 was not reloaded.

## Critical mechanical findings and approved concept work

The original injector discharges align with the chamber, but its plate radius
equals the gas bore: **zero annular face attachment/sealing land**. Both axial
header/channel interfaces have only1.5mm between gas bore and coolant openings.
Matching bolts do not fix these facts. The minimum proposed upper bolt-to-plenum
radial ligament is1.3712100715459mm; this is not a strength result.

`JOINT_SEAL_LAYOUT_PROPOSAL.md` records primary-source cryogenic seal research,
limits and alternatives. User approved developing the isolated separable-head /
collector-below-flange concept. No generic elastomer O-ring was selected or cut.

`systems/geometry/separable_head_layout.py` and
`scripts/prepare_separable_head_study.py` now implement a bounded source-bound
layout planner. Eight synthetic tests pass. Actual retained-source study:
`output/separable-head-layout-study-2026-10-21-v1/`:

- Explicit provisional outer mounting radius95mm, collector plenum outer
  radius74mm, bolt-circle radius85mm, clearance radius3.2mm and8 holes.
- Retains injector hydraulic bores/counts, gas-entry position and all downstream
  convergent/throat/nozzle stations. Replaces27mm of cylindrical chamber entry
  with an equal-bore collector passage rather than increasing/scaling gas volume.
- New collector axial interval-314.6666666666667..-287.6666666666667mm.
- Geometric gas-volume difference-4.065758146820642e-19m3, floating-point residual.
- Provisional conservative head-face land30.3712100715459mm and downstream
  supply-port/chamber radial clearance2.13560503577295mm.
- **Native revised geometry NOT_GENERATED, installed=false.** Front-supply header,
  head/plate bolt cuts, revised pipe route and collector/chamber joining still
  need implementation and actual QA. The collector's retained0.7mm gas-wall
  thickness and1.5mm chamber-interface land are unresolved thermal/joint issues,
  not made safe by this layout. No seal or allowable is inferred from fit.

## Verification ledger

- **1252 targeted Python tests passed**,72.96s: unit Physics, Systems, API,
  Plugins, Core, plus component-cooling/interfaces, design-analysis and managed
  project authority HTTP. Not the entire repository or remote CI.
- **65 focused geometry/joint/layout/HTTP tests passed**,1.67s; includes the
  eight new revised-layout tests and canonical-angle round trips/domain rejection.
- **438 JavaScript tests passed**, zero failures/skips.
- New exact `joints-v4` native campaign: **83 passed**, zero failures/errors/
  skips:38 component-native,7 component HTTP,7 nozzle/HTTP,31 original fixtures.
  XML/receipts are under `docs/implementation/evidence/R07_COMPONENTS_2026-10-20/`;
  `runtime-qualified-joints-v4.json` binds164 exact identities.
- Mypy passed on9 focused production files. Scoped Ruff and tracked diff
  whitespace checks passed. No remote CI, packaging/release or physical claim.
- Actual case passed normal authenticated create/source replay/CAS save/build,
  strict read-only interface query, export and browser preview. UI shows90
  openings,8/8 bolt axes,1.5mm inner lands,zero injector attachment land and
  incomplete-engine status together. Current-page browser error log was empty.
- Browser proof: `ui-joint-inspection.png`, `ui-19-body-joint-preview.png` in
  the actual candidate folder. Preview is display-only, not metrology/acceptance.

## Negative evidence retained

- `connected-engine-joints-2026-10-21-v1/`: preparation stopped before any
  managed writes because the retained canonical90-degree elbow exceeded the
  raw unrounded floating constant by two ulps. The Core-compatible closed-bound
  comparison fixes the actual save/reload defect, without changing Core.
- `joints-v2` native campaign and corresponding unit logs retain the failed first
  repair: the Core serializer requires a mapping, not a bare float. The corrected
  mapping-based API passed fresh unit/native campaigns. No failed XML was sealed.
- `joints-v3` preserved a scheduling-sensitive cancellation-witness failure:
  CANCELLED/PID existed but no started event at the fixed0.3s point. First XML is
  `fixture-regression-joints-v3-attempt-1-failed.xml`; exact-source unloaded retry
  passed31 unchanged tests. See `qualification-retry-joints-v3.json`. No assertion
  or production algorithm was relaxed for that retry. Final v4 ran fixtures
  separately and passed all31; timing sensitivity remains a hardening concern.
- Actual `connected-engine-joints-2026-10-21-v2/` remained FAILED: STEP dimensions/
  semantics and STL passed, but its imported new header had wrong Euler topology.
  Retained STEP diagnostics showed four-incident linear edges on coarse periodic
  bolt-cylinder meshes. Blanket refinement removed those defects but exceeded
  the100k-node bound (145379); it was **not admitted**. Local long-cylinder
  refinement gave39202 diagnostic nodes and correct Euler-30 with no bad edges.
  The new native regression, fresh83-test campaign and actual v3 assembly passed.

## Still required for the user's full engine goal

1. Implement/generate the approved revised head/collector/pipe concept, qualify
   actual gas and fluid connectivity, joints, intersections, sections and exports.
2. Supply/select specific compatible seals, retention and joining with process-
   specific data, dimensional tolerances, flange response and retained preload.
3. Complete matched whole-chamber/header/throat/nozzle hot-gas and actual-sector
   coolant heat transfer/hydraulics, phase/domain checks, cooled rib/roof/bimetal
   response, and applicable material data. Do not map sectors to rectangles or
   arbitrary hydraulic-diameter circular correlations without justification.
4. Couple actual short/curved/plenum losses and warmed injector capacity to the
   feed/CEA/thermal operating point; regenerate geometry from the same solution.
5. Qualify the normal managed engine workflow, save/reload/export and multiple
   thrust cases; reject infeasible/unsupported cases, not force target closure.
6. Physical validation needs genuine matching measurements, uncertainty, criteria
   and qualified review. Software verification does not supply missing evidence.

These are open implementation/engineering requirements, not just pending tests.
R08 remains HOLD until the user accepts the full goal's achievement.

## Preservation

Normal authenticated read-only HTTP reconfirmed owner commit
`638d6ea3-4057-4b90-8dd4-8fc956b4772d`,v4, canonicalSHA256
`7504cf9bf0b6371ea9af5228df5b0587dd8b32e08247c2b20d1c88860d977bcf`.
Owner8878 listener remained PID77508. Protected CEA fixtureSHA256 remained
`6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`.
Inherited dirty work, earlier candidates and receipts were preserved.
