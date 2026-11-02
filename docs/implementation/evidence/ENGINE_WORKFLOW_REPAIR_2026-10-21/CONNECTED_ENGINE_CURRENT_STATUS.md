# Connected engine implementation checkpoint — full goal not complete

2026-10-21; checkout HEAD293223e plus preserved inherited/local work.
No commit, push, migration, manufacturing release or R08 work performed.
The user-requested running8878 viewer was not stopped or reloaded.

Latest superseding checkpoint: `GROOVE_FIT_AND_INTEGRAL_CONCEPT_CHECKPOINT.md`.
The user approved the five-groove isolated study and integral collector/jacket
investigation. Actual16-body CAD with all five blind grooves passed STEP/STL
at182768triangles;93native checks,314geometry/system and439JS tests passed.
Both faces were inspected in the fresh isolated8896 viewer. A separate,
explicitly UNQUALIFIED native integral probe has one metal solid and one
connected coolant void with conserved source volumes; it is not yet admitted as
an integral engine component or a manufactured bimetal. Seal selection, full
hot-state/pressure readiness and R08 remain unaccepted/HOLD.

Preceding checkpoint: `REVISED_CAD_MATCHED_FEED_CHECKPOINT.md`.
The approved separable-head CAD is now generated:16metal bodies,177728triangles,
independent STEP/STL pass, two8/8mounting interfaces, connected fuel/LOX routes,
and browser proof on isolated8895. Fresh91-test native campaign passed.
Matched wall/liquid/injector branch software is verified within its explicit
constant-area/source-response scope, not yet the complete native sector-cooled
engine. `PROVISIONAL_SEAL_PROPOSAL.md` records actual lands, candidate families,
pending isolated groove/joining choices and missing service data. Full hot-state
closure and sealed pressure joints remain unfinished; R08 HOLD.

Latest external-pipe/circuit checkpoint:
`EXTERNAL_PIPE_AND_CIRCUIT_CHECKPOINT.md`. The new isolated19-body candidate
passed actual STEP/STL QA and browser verification. Its geometric fuel-through-
regeneration and direct-LOX routes connect; this does **not** complete the
pressure/thermal/material/joint/engine solution. R08 remains HOLD.

Latest joint/approved revised-layout checkpoint:
`JOINT_GEOMETRY_AND_REVISED_LAYOUT_CHECKPOINT.md`. An actual19-body candidate
with matching upper-header bolt cuts passes STEP/STL QA at177776 triangles.
The8/8 collar axes match, but the existing injector has zero annular face land
and the header/channel gas-to-coolant lands are1.5mm. The user approved an
isolated revised mechanical concept; its source-bound layout planner is tested,
The earlier planner-only status is superseded by the generated revised CAD
checkpoint above. Full engine closure remains open.

## Implemented and exercised

| Unit | Implementation / current evidence |
| --- | --- |
| Separate injector fuel/LOX head | `manifold.dual_annular`: actual disjoint enclosed annular cavities, cap supply ports and matching outlet arrays; source-bound distinct cold hydraulic diameters/counts |
| Radial injector alternative | `injector.biprop_radial_doublet`; inner fuel/outer oxidizer feed rings; original tangential family preserved |
| Mounting collar primitive | `interface.bolted_flange`, explicit bore/bolt circle/clearance holes; not a qualified pressure joint |
| Cooling inlet/collector | `manifold.cooling_annular`: central gas bore, enclosed coolant annulus, circular supply/return cap port and real sector-channel cap openings |
| Actual interface inspection | Exact saved model/baseline HTTP read; world positions, normals, areas and sector-corner matching; unresolved supply/pipe/seal status retained |
| External pipes / circuit topology | Straight and true toroidal elbow primitives; seven pipe bodies; exact circular port mating; explicit supply boundaries, segregation, required cuts and lower-inlet-to-upper-collector route-order checks |
| Heated liquid properties | Immutable bounded T/P/h/rho/Cp/mu/k table; strict retained NIST isobar adapter, no extrapolation or cold-value fallback |
| Temperature-dependent wall | Source/condition-bound k(T) planar gas/wall/coolant balance; not cooled-rib/roof/bimetal stress |
| Isolated material research | Hash-pinned original-unit transcription, exact-condition or explicitly unmatched same-alloy comparisons; no installation/allowable mode; see `MATERIAL_RESEARCH_CHECKPOINT.md` |
| Heated feed segment | Sourced h(T,P), kinetic-energy balance, circular-pipe friction/acceleration loss and explicit minor-loss basis |
| Feed/injector branch closure | Explicit ordered circular cells, prescribed heat, given chamber pressure, heated manifold density and injector capacity solved together; no target-forcing loss |
| Joint/seal foundations | Contact-limited axial preloaded bolt-group screen and nominal squeeze/fill gland math; not native gland geometry or seal qualification |
| Matching bolt cuts / joint lands | `interface.bolt_pattern`, exact actual-source collar/header alignment, conservative annular lands and injector discharge/zero-attachment-land inspection; no qualified seal/load path |
| Approved isolated revised concept | Source-bound preparer, front-outlet collector, enlarged matching head/plate/collector bolt patterns and four-elbow return; actual16-metal-body STEP/STL and browser pass; no qualified seals |
| Matched wall/feed branch | Explicit constant-area flow-normal source response, k(T) wall/liquid heat and pressure solve plus heated injector closure; not whole-engine sector/chamber coupling |
| Blind groove primitive | Real blind cut with floor/land/port clearance and independent native QA; actual engine candidate deliberately has no selected seal or groove installation |

Principal paths: `systems/geometry/component_model.py`, `component_reference.py`,
`component_sections.py`, `component_interfaces.py`, `component_workspace.py`;
`plugins/geometry/workers/component_worker.py`; `api/component_interfaces.py`,
`api/component_geometry.py`; `gui/static/component-geometry.js`;
`physics/fluids/liquid_table.py`; `systems/propellants/nist_liquid.py`;
`physics/heat_transfer/temperature_wall.py`;
`systems/materials/research.py`; `scripts/prepare_material_research.py`;
`physics/feed/heated_liquid_segment.py`; `systems/cycle/heated_feed_branch.py`;
`physics/solid_mechanics/bolted_joint.py`, `seal_gland.py`.

The new thermal/feed kernels are verified building blocks, **not yet a fully
integrated engine solution in the normal rocket workflow**. Existing statuses
must not be changed to complete merely because a primitive now exists.

## Preceding retained12-body candidate

`output/connected-coolant-headers-2026-10-21-v1/` contains the full explicit
proposal, captured source replay, model, interface report, retained native job,
review context, BREP, STEP, STL and artifact hashes. It is an isolated geometry
study using the retained approved cold baseline, **not a new CEA/hot operating
solve or owner-project edit**.

- Project `e8ec2976-4498-4ff8-9eb3-9a4438c4bd23`
- Baseline `0b8b6bd9-292b-4924-ace5-ccd349c5f106`
- Model `b85484a0-df59-57e5-8f42-513e98a06ca9`
- Model commit `3823c0d6-e267-4b10-9bfa-974de453398a`
- Native job `ed421258-8a01-4691-81a5-1fda83c464c2`
- Build `6f9219fb-7f1f-5fb2-8a67-1b6b494f6819`
- **12 bodies,126336 STL triangles, STEP/STL declared software QA PASS**
- **76 actual openings:16 distributor/plate mates,12 header/channel mates,
  four unconnected external fluid ports,16 injector discharges**
- No shared fuel/LOX mixing plenum. Coolant is not silently assigned a fluid by
  geometry inspection; engineering circuit/state assignment remains separate.
- Enclosure radius reduction and removal of the interfering plate collar are
  explicit isolated proposal alternatives, not modifications to the owner case.
- Upper header bolt pattern is **not yet cut/sized**. Source collar attachment,
  all seals/glands, external pipes and hot strength remain unqualified.

Latest exploratory dimensions are in
`PROPOSED_COOLANT_HEADER_LAYOUT_1500N.json`. CAD is not manufacturing or hot-fire
approved. The lower header extends the central bore; corresponding gas/plume and
pipe exposure must be assessed before accepting a physical layout.

The task-owned isolated viewer is at
`http://localhost:8892/app/workbench/native-geometry?project=e8ec2976-4498-4ff8-9eb3-9a4438c4bd23`.
Use localhost, not the owner's127.0.0.1 cookie host. The obsolete task-owned8891
study server was gracefully closed after the replacement candidate passed; its
data/artifacts remain intact. Owner8878 stayed running.

That runtime/model checkpoint is historical after the new pipe/reader changes.
The current isolated candidate is19 bodies at localhost8893, project
`566e6e99-d458-4625-9530-2295c0fb7043`, model commit
`e57154f1-89ba-47f0-afe7-098c7736f1e1`, native job
`7fee8dff-7770-4c80-8060-ec461fbd1fa0`. It has169680 STL triangles and90 actual
openings:16 injector mates,12 header/channel mates,8 pipe mates and2 declared
external supply boundaries. See the latest checkpoint for identities/artifacts.

## Verification at this checkpoint

- Latest pipe work:1225 targeted Python regressions,436 JavaScript tests and a
  newly sealed80-test native `pipes-v3` campaign passed.164 exact native runtime
  identities remain current. Actual19-body STEP/STL and browser flow passed.
  Negative candidates v1/v2 remain FAILED; no topology/fidelity/capacity limits
  were relaxed to accept v3. Full-engine/hardware acceptance remains open.
- After material research implementation: **1199 passed**, 79.70 s, in the
  targeted regression scope below; **52 focused material/wall tests** also
  passed. Study XML is in `output/material-research-bounded-2026-10-21-v1/`.
  Eight actual isolated study checks passed: four bounded research balances,
  four expected domain rejections. No engine material window was installed.
  Final material study `v2` adds 13 selected implementation hashes; all 52 focused
  tests, the eight study checks, Mypy and Ruff passed again after that addition.
- Targeted Python regression **1156passed**,101.24s: unit Physics, Systems, API,
  Plugins, Core plus component-cooling/interfaces, design-analysis and managed
  project authority HTTP tests. Not the complete repository/remote CI suite.
- All JS tests **435passed**,0failed/skipped.
- New native campaign `coolant-v1`: **75passed**,0failed/skipped
  (30component,7componentHTTP,7nozzle/HTTP,31fixture regressions).
  Exact164 runtime identities revalidated. Receipts and XML are under
  `docs/implementation/evidence/R07_COMPONENTS_2026-10-20/`.
- Real12-body engine study independently passed after that campaign; the
  generic family fixtures alone are not being substituted for this actual case.
- Mypy success on12 focused production files; scoped Ruff and tracked diff
  whitespace checks passed. No remote CI, hardware or whole-program claim.
- Methane numerical study:111.15–133.15K,5–8bar absolute;161 retained table nodes
  and132 independent off-grid NIST comparisons. Maximum sampled relative errors:
  rho5.60e-6,Cp2.07e-5,mu7.43e-5,k3.57e-6; maximum h error1.841J/kg.
  `output/methane-liquid-surface-2026-10-21-v2/`. Explicit study domain only;
  no live engineering property window installed, no physical uncertainty bound.

Negative evidence was retained. The first interface assembly exceeded the
generic2MiB reader-response cap. Only the component witness-response capacity
was increased to16MiB, leaving input, memory, timeout and geometry tolerances
bounded. The next actual assembly exposed a rigid-placement cap-plane reference
classification bug; ulp-bounded membership was fixed and translated-open-port
tests added. No reverse-distance/topology tolerance was loosened. Subsequent
native campaigns and the actual assembly passed. A feed-branch test initially
compared against a no-pipe-loss target; it now uses the independent exact
Poiseuille/orifice quadratic, not a widened assertion tolerance.

## Remaining work in dependency order — R08 remains HOLD

- [x] Approve the named material **research basis** only (user approval recorded
  2026-10-21; no live input, recipe, allowable or hardware approval).
- [x] Implement isolated material staging/comparisons with retained source and
  statistic identity. Eight prescribed-fixture study checks passed; missing
  engine curves remain missing.
- [ ] Complete source/
  process/condition/orientation/temperature datasets. See
  `LPBF_HIP_MATERIAL_DATA_PROPOSAL.md`. Isolated research is authorized; installation
  or qualified allowables are not.
- [ ] Complete applicable whole chamber/convergent/throat/nozzle gas-side
  thermal states and matched passage thermal/hydraulic model. Native sloping
  angular sectors are not flow-normal rectangles/circular pipes. No silent
  hydraulic-diameter model substitution is accepted.
- [ ] Couple hot-fluid properties, k(T), cooled ligament/rib/roof and bimetal
  response, material domains and uncertainty. Verify spatial/coupling refinement
  and local phase/boiling applicability before accepting heat pickup.
- [x] Build isolated external pipe/bend geometry, mate all four external engine
  openings, and verify the explicitly assigned fuel/LOX circuit topology.
  The two remaining open pipe ends are declared supply boundaries, not designed
  tanks/regulators/connectors. This is not a warmed-fuel flow solution.
- [ ] Derive pipe/entrance/bend/plenum/distribution losses from applicable
  geometry/characteristics, including short developing sections; no invented
  balancing loss or automatic fully-developed mapping. Integrate actual warmed-
  fuel properties and regenerate injector/pipe dimensions from that solution.
- [ ] Cut/size the upper-header bolt pattern and selected seal/gland geometry;
  specify attachment, actual bolt/seal materials, dimensional tolerances,
  retained preload, cryogenic contraction, flange bending and leak/proof basis.
  Geometric matching cuts are now built and qualified in isolation. Strength
  sizing, seal/gland selection, joining and the approved revised concept remain
  open; an8/8 axis match is not completion of this work package.
- [ ] Integrate full feed/heated injection/CEA/hot-wall/nozzle operating closure,
  conservation/target checks and exact source-matched geometry regeneration into
  the normal managed rocket workflow. Existing divergent-only closure remains
  a limited model, not full chamber cooling.
- [ ] Verify multiple requested thrust cases by new calculations within source/
  model/geometry capacities. Do not uniformly scale this nominal concept or
  guarantee every thrust is feasible. Unsupported/infeasible cases must say so.
- [ ] Complete managed workflow persistence/restart/export and GUI acceptance
  for the integrated solution. Reload the user's viewer only with authorization.
- [ ] Physical readiness: genuine compatible measurements, uncertainties,
  predefined criteria and qualified evaluation. No such engine evidence exists.

## Preservation

Read-only normal HTTP check reconfirmed owner design r18,v4, commit
`638d6ea3-4057-4b90-8dd4-8fc956b4772d`, canonicalSHA256
`7504cf9bf0b6371ea9af5228df5b0587dd8b32e08247c2b20d1c88860d977bcf`,
unchanged. Owner8878 listener remained PID77508. Protected CEA fixtureSHA256
`6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`
also remained unchanged. Earlier proposals, failures, native receipts and
candidate files were not rewritten as current successful evidence.
