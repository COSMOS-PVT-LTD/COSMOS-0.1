# External pipes and circuit topology - preliminary software checkpoint

2026-10-21. Full engine goal is **not complete**; R08 remains HOLD. No live
material inputs, owner design changes, migrations, commits or pushes authorized
by this checkpoint. The existing owner viewer on8878 is not restarted.

## Implemented

- `pipe.circular`: explicit bore, radial wall thickness and length.
- `pipe.elbow`: annular cross-section revolved along a circular centerline;
  explicit bore, wall, bend radius and15-90degree angle. Not touching/mitered
  straight tubes pretending to be a bend. Both ends are actual open bores.
- Native construction in `plugins/geometry/workers/component_worker.py`;
  independent analytic volume, volume centroid, rigidly placed bounds, CSG
  surface constraints and source samples in `component_reference.py`.
  Elbow centroid includes the cross-section Jacobian; it is not simply the
  centerline centroid. Euler characteristic is0 for either through-bore tube.
- Unsupported local-X axial-profile metrology rejects toroidal elbows rather
  than treating them as radius profiles. No curve-normal section is fabricated.
- `component_interfaces.py` inventories actual pipe ends and matches only equal
  circular bores, opposed normals and coincident centers within explicit
  numerical tolerance. Ambiguous mates reject. No hydraulic/seal inference.
- `pipe_routes.py` creates an explicitly proposed axis-aligned U-return using
  actual saved opening positions/radii. It rejects unrelated inspection graph
  IDs, missing ports, unsupported orientations, unresolved spacing and guessed
  reducers. It does not silently scale the engine for a new target thrust.
- `component_circuits.py` follows actual pipe bores, separate head plenums,
  channel/header mates and injector passages. Explicit supply-boundary port IDs
  are required. It checks segregation, all channel/sink reachability, open ends,
  mandatory cut vertices, bypasses and nozzle-inlet-before-upper-collector order.
  A bidirectional connectivity graph is not a pressure-solved flow direction.
- Normal project-scoped read-only HTTP inspection supports optional paired
  `fuel_boundary` / `oxidizer_boundary` query fields. Unknown fields, incomplete
  pairs and invented boundaries reject; posted overrides do not write a model.
- GUI offers those explicit analysis fields and separately counts injector,
  coolant-header and pipe connections. **Geometrically connected** does not
  change **Engine solution: INCOMPLETE**, pressure/seal or validation status.

Principal paths: `systems/geometry/component_model.py`, `component_reference.py`,
`component_interfaces.py`, `component_circuits.py`, `pipe_routes.py`,
`component_sections.py`; `api/component_geometry.py`, `component_interfaces.py`;
`gui/static/component-geometry.js`; the native worker and independent STEP
reader; `scripts/build_engine_pipe_study.py`.

## Explicit proposed layout

`PROPOSED_EXTERNAL_PIPES_1500N.json` is an **isolated geometry hypothesis**, not
installed engineering inputs or a manufacturing drawing. It retains exact four
source opening locations/bore radii and declares provisional wall1.2mm,
return bend centerline radius12mm, two25mm stubs, an exactly calculated intervening
span, and80mm external supply stubs. These are not pressure/thermal sizing.

Seven added pipe bodies produce the intended19-body candidate:

1. Fuel supply boundary -> nozzle-bottom inlet header.
2. Six real parallel sector passages -> upper collector below chamber flange.
3. Upper collector -> straight stub -> elbow -> span -> elbow -> straight stub
   -> segregated injector fuel plenum.
4. Separate oxidizer supply boundary -> segregated injector oxidizer plenum.

Target inventory:90 actual openings;16 head/plate mates,12 header/channel mates,
eight pipe mates; two declared external supply boundaries and16 injector
discharges. No tank, regulator, connector/thread, welding, seal/gland or fastener
acceptance is implied by those supply boundaries. The original cold hydraulic
injector remains a retained baseline replay, not a warmed-fuel injector solution.

## Negative evidence and corrections

`output/connected-engine-pipes-2026-10-21-v1/` remains FAILED. Exact pipe-only
diagnostic counted139062 triangles, including128982 from two elbows. With the
preceding126336-triangle engine, this exceeded the unchanged200k limit.
The elbow-only mesh normal-angle sampling changed from0.05 to0.1rad. Exact CAD,
linear deflection, per-part volume/centroid/semantic/topology/reverse checks and
assembly capacities were **not** changed. A new79-test campaign passed afterward.

`output/connected-engine-pipes-2026-10-21-v2/` also remains FAILED. Its STL,
STEP dimensions and semantic mapping passed, but independent STEP surface
meshing produced4-incident linear edges on three small cylinders. Expected
Euler0 was not changed to the observed1/19/11. No mesh elements were deleted or
vertices welded. Increasing global circle resolution did not resolve all faults
and exceeded the sampling budget; per-body visibility alone also did not fix it.

`scripts/diagnose_component_step_mesh.py` reproduced the faults. Resolving actual
imported annular-tube curvature locally produced33178 nodes with no nonmanifold
or orientation errors in the diagnostic. The production reader now applies this
local sizing only to independently recognized two-cylinder/two-plane annular
tubes. All100k total-node,30k body-node, topology and fidelity limits remain.
The new displaced-slender-pipes native regression passed. The fresh full
`pipes-v3` campaign passed80 tests:35 component-native,7 component HTTP,
7 preserved nozzle/HTTP and31 original native fixtures, with no failures/skips.
Its164 exact native identities were revalidated after sealing. Earlier receipts
were not resealed for changed reader code; they are historical evidence.

## Accepted isolated19-body candidate

`output/connected-engine-pipes-2026-10-21-v3/` is the accepted software candidate.
Its STEP reimport and STL topology/fidelity/semantic checks passed. The actual
STL has169680 triangles, below the unchanged200000 ceiling. All19 part identities
are retained; the geometry is neither fused automatically nor manufactured.

- Project: `566e6e99-d458-4625-9530-2295c0fb7043`
- Model: `b30102e9-c7d7-50ce-b9b9-04000c86f81e`
- Model commit: `e57154f1-89ba-47f0-afe7-098c7736f1e1`
- Cold replay baseline: `c02d2a22-2869-4464-a6e9-53cdb0fa6972`
- Native job: `7fee8dff-7770-4c80-8060-ec461fbd1fa0`
- Build: `ed56ee52-840d-5727-a92d-a7d508dc16a8`

Viewer:
`http://localhost:8893/app/workbench/native-geometry?project=566e6e99-d458-4625-9530-2295c0fb7043`.
The task-owned server remains running. Use localhost to avoid the owner's
127.0.0.1 browser-cookie host. This is a new isolated root, not an installed
revision or replacement of the owner's project. Artifacts include actual
BREP/STEP/STL, model/source replay/QA/review records, exact preparation/runtime
identities, circuit inspection and a pipe-flow applicability handoff.

The verification skill drove the complete saved-model -> read-only API ->
response -> retained preview check:

| Boundary | Verified evidence |
| --- | --- |
| UI loads exact model | Model commit above displayed as CURRENT saved source |
| UI -> API | Explicit1e-6m tolerance and paired actual boundary IDs; no model write |
| API -> source -> response |90 openings,16 injector mates,12 header/channel mates,8 pipe mates,2 supply boundaries; circuits geometrically connected |
| Independent native output | STEP and STL passed for the actual19-body case, not just small family fixtures |
| Response -> browser | Same counts/status displayed; actual retained19-body mesh rendered with pipes visible; current-page browser error log empty |

UI proof: `ui-circuit-proof.png`, `ui-19-body-preview.png` in that output folder.
The screenshot is display evidence, not dimensional metrology or hardware proof.
The UI explicitly says **Engine solution: INCOMPLETE**, pressure NOT_CALCULATED,
seals NOT_ASSESSED, physical validation NOT_PERFORMED.

Additional checks:1225 targeted Python regressions (84.35s),436 JavaScript tests,
26 focused pipe/interface tests (then17 circuit/router/HTTP tests after the
route-order check), scoped Mypy and Ruff. The subsequent reader correction is
covered by the80-test native campaign and its explicit slender-pipe regression.
These are not a full-repository, remote CI, production or experimental result.

Preservation: read-only HTTP reconfirmed owner r18/v4, commit
`638d6ea3-4057-4b90-8dd4-8fc956b4772d`, canonical hash
`7504cf9bf0b6371ea9af5228df5b0587dd8b32e08247c2b20d1c88860d977bcf`.
Owner8878 stayed on PID77508; protected CEA fixture hash remains
`6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`.

## Remaining integration and acceptance

- Quantify appropriate entrance/bend/plenum/distribution losses from applicable
  geometry/correlation or evidence. Do not invent a valve/loss to consume feed
  pressure. Several short stubs/span do not satisfy the existing fully-developed
  circular feed-cell L/D>=10 assumption; mapping them blindly is unsupported.
- Finish full chamber/convergent/throat/nozzle thermal coverage, heated-fluid
  properties, cooled rib/roof/bimetal response and condition-matched material
  data. Research-only material approval is not an installation/allowable grant.
- Finish upper-header bolting, chosen seal/gland and attachment geometry,
  preload/flange/tolerance/contraction/leak checks. The1.2mm pipe wall is not an
  assessed pressure boundary; joining and support loads remain open.
- Integrate feed/injection/CEA/heat-loss/operating closure and regenerate from
  that exact solution, then qualify multiple thrust cases and managed workflow
  persistence/export/UI acceptance. Unfeasible/unsupported cases must reject.
- Experimental validation still requires actual evidence and qualified review.

No full-engine, production, manufacturing or hot-fire acceptance is claimed.
