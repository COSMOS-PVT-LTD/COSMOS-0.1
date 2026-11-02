# Revised CAD, matched wall/feed and seal checkpoint

2026-10-21. The revised **CAD work package** is generated and software-verified.
The **full engine goal is not complete**: whole-engine hot-state closure and
sealed pressure-boundary acceptance remain open. R08 HOLD. No original-project
write, live-data migration, restart of8878, commit, push or hardware release.

## Accepted isolated revised CAD

Normal saved-model -> interface HTTP inspection -> managed native job ->
independent STEP/STL QA -> artifact download -> browser preview was exercised.
The existing model/authority/native layers are preserved; no replacement CAD
architecture or automatic solid fusion was introduced.

Artifacts: `output/connected-engine-revised-head-2026-10-21-v1/`:

- `component-specification.json`, `model-envelope.json`, `source-replay.json`:
  exact retained cold-study baseline, not a new CEA or hot operating solve.
- `interface-inspection.json`: 98 openings, 16 distributor/plate connections,
  12 header/channel connections, 12 external pipe connections. Only two declared
  tank-feed boundaries are unconnected. Fuel passes through regeneration before
  the injector head; LOX is directly supplied. The circuits remain segregated.
- `native-job.json`: COMPLETED, source-current generated candidate; independent
  STEP and STL pass; **16 metal bodies, 177728 triangles**. Engineering acceptance
  NOT_PERFORMED; engineering-export eligibility remains false.
- `PRELIMINARY-CONNECTED-SEPARABLE-HEAD-source.brep`, `...export.step`,
  `...export.stl`; exact file hashes in `artifact-sha256.json`.
- `ui-revised-16-body-preview.png`: browser retained-mesh proof, SHA256
  `c310b383cf60a28341a382f0ba81b3c13b5778f00566ae35b7963ca76b5073c2`.
  Browser error/warning log was empty at inspection.

Identities:

| Object | Identity |
| --- | --- |
| Project | `1a3d02a7-e5f8-4253-8898-77842aa5a9df` |
| Component model | `82401d35-1292-5abd-b016-9c90e2d364c7` |
| Model commit | `fd44b9e0-bc8b-4664-a8ac-3886f053363b` |
| Cold replay baseline | `2d95d77a-cd62-4fe4-8d8c-71b91a551858` |
| Build | `32c205f4-6da4-59c3-883f-16c5d2154fab` |
| Job | `c6712828-0a6b-46a0-b0b5-b447d1c6bddd` |

Task-owned viewer: `http://localhost:8895/app/workbench/native-geometry?project=1a3d02a7-e5f8-4253-8898-77842aa5a9df`.
It is separate from the unchanged owner viewer8878 and historical8892-8894.

### Mechanical concept implementation

`systems/geometry/separable_head_cad.py` implements the approved source-bound
layout. The collector moves into exactly27mm of the original cylindrical gas
entry. Trimming that chamber segment preserves gas volume; convergent, throat,
saved divergent stations, injector bore radii/counts and plate/head axial
positions are unchanged. The head, plate and collector have matching95mm outer
radius /85mm bolt-circle radius /3.2mm clearance radius /eight-bolt patterns.
Both mounting interfaces have8/8 equal-bore axes. The obsolete separate collar
is suppressed only in the new isolated candidate, never deleted from history.

The collector has a real front-web outlet outside the main chamber wall and
cooling-channel band. A nine-piece, four-elbow fuel return routes outside the
enlarged flange; two additional supply stubs retain the selected source bores.
All six cooling passages remain actual metal cuts. Separate illustrative fluid
domain export is explicitly disabled; this is why16metal bodies replace the
preceding19body representation, not missing channels.

Additive native operations in `systems/geometry/component_model.py`:

- `manifold.cooling_front_supply`: actual front-web outlet with channel/bore
  collision constraints, preserving back-supply compatibility.
- `interface.bolt_pattern`: uniform solid/annular operands including inclined
  injector bores; conservative whole-axial-range bore-clearance checks.
- `interface.face_groove`: true blind annular end-face cut, material lands,
  blind-floor, cavity and inclined-bore clearance checks. No seal inferred.

`component_reference.py` and `component_worker.py` implement independent exact
volume/SDF/semantic and native-cut behavior for these geometries. Joint inspection
now exposes actual mounting-stack lands/axes and blind grooves. The browser
renders these separately from pressure/seal acceptance.

The first unqualified development attempt exceeded the unchanged200k triangle
cap (`output/separable-head-unqualified-smoke-2026-10-21-v1/`). The second uses
0.1rad angular tessellation for fastener-bore bodies, as already used for elbows;
linear deflection, source CAD, all independent QA tolerances and resource caps
are unchanged. It passed fresh primitive qualification and then the actual
assembly's independent QA. The failed attempt is retained, not resealed.

## Matched wall/feed implementation and exact scope

New `physics/feed/matched_liquid_cell.py` solves wall heat, liquid enthalpy,
pressure loss, kinetic-energy change and temperature-dependent conductivity in
one bounded solution. It consumes explicit geometry-matched transfer responses,
not arbitrary circular correlations inferred from hydraulic diameter. It supports
identical constant-area flow-normal passages and strict source/property/material
domains. Coolant-contact wall reaching the conservative sourced saturation
temperature is rejected; no local boiling or cold-property fallback is supplied.
Result provenance retains fluid-source hashes, geometry graph, material condition,
conductivity-source hash and transfer-response source hash.

New `systems/cycle/matched_feed_branch.py` solves this heated series route against
the liquid injector's actual **outlet** pressure/density and unchanged area/Cd at
a specified chamber pressure. Heat is recomputed from gas/wall/coolant conditions,
not prescribed to force a desired answer. No artificial pressure resistance,
valve, target-thrust scaling or injector resize is introduced.

This is a real bounded numerical branch implementation, **not full integration
of the engine's current sector-channel CAD**. It is not exposed as a solved
rocket-workflow stage. Explicit remaining software/model work:

1. Applicable native sector-passage flow-normal geometry/transfer/loss models,
   including slopes/knuckles, entry effects and flow splitting. Axial section
   areas from `component_cooling.py` must not be silently substituted.
2. Source-matched thermal coverage for the relocated gas-entry collector, entire
   chamber, convergent, throat and divergent; hot-side boundary/heat withdrawal
   and warmed-injection enthalpy must participate in the same combustion/nozzle
   operating solve. The existing divergent-only rectangular solver is not this.
3. Applicable short/elbow/header/valve/control characteristics for the retained
   physical feed route, rather than treating every small CAD piece as a long
   fully-developed straight pipe.
4. Exact-condition liner/jacket conductivity, strength and temperature basis;
   rib/roof/bimetal conduction and cooled-wall stress, thermal contraction and
   joining. Approved research material names are not service allowables.
5. Exact-source accepted operating-result -> regenerated hydraulics/CAD -> normal
   saved engine-review integration with conservation, target and coverage tests.

No actual methalox hot-state result or thermal feasibility is claimed by the
manufactured analytic tests. Physical validation still needs actual measurement
evidence and qualified evaluation; these software gaps also remain independently
of the missing experiments.

## Sealed-joint status and approval boundary

`PROVISIONAL_SEAL_PROPOSAL.md` is the requested sourced proposal. It includes
visually inspected original supplier material, exact current face lands, separate
fuel/LOX barriers, provisional groove-envelope options and the required supplier,
thermal/preload, compatibility and leak-test data. The current candidate has
**zero grooves and no selected seal**. Generic blind grooves are implemented and
native-tested, not falsely installed as qualified seals.

Two decisions were requested: whether to explore the five proposed groove
envelopes in isolated CAD, and integral collector/jacket versus a redesigned
separable local seam. No owner installation or hardware acceptance is implied.
Both header/channel inner lands remain1.5mm; the collector gas-to-coolant wall
remains0.7mm. Those pressure boundaries are not fixed by the new outer flange.

## Verification record

- Fresh `revised-head-v1` native campaign:46component +7component HTTP
  +7preserved nozzle/HTTP +31fixture regression = **91 passed, none skipped**.
  `docs/implementation/evidence/R07_COMPONENTS_2026-10-20/runtime-qualified-revised-head-v1.json`
  pins164 runtime identities and new software receipts. Historical receipts stay
  unchanged. Fixture tests ran without competing native qualification jobs.
- `matched-revised-head-unit-v2.xml`:74focused wall/feed/joint/revised-layout
  tests passed. These overlap the wider geometry suite; do not sum counts.
- `revised-geometry-unit-v2.xml`:301geometry/system tests passed,423deselected.
- `matched-feed-final-v1.xml`:11matched-cell/branch tests passed after final
  physics metadata/provenance changes. Analytic heat/enthalpy/P balance,
  source/domain failures, hot-boundary/flow changes and parallel scaling covered.
- `matched-injector-density-v1.xml`:one additional manufactured variable-density
  branch regression passed. Independently computes warmed orifice capacity and
  rejects substituting the original cold density into the accepted flow result.
-439JavaScript tests passed, including revised stack/groove status presentation.
- Ruff passed for the13targeted source/test files; mypy passed9targeted source
  files. No broad full-repository test or new remote CI claim is made.

Two mistyped Python test paths and a Node directory invocation collected no
useful scope; corrected commands produced the results above. Native sealing was
first attempted before fixture XML existed and correctly refused; after the31
fixture tests completed the unchanged campaign sealed successfully. These are
not passing test evidence and no missing group was bypassed.

## Preservation

Read-only authenticated owner HTTP check reconfirmed design
`6524df5d-46f9-5b74-b214-8f5ada56acf6`, r18/v4, commit
`638d6ea3-4057-4b90-8dd4-8fc956b4772d`, canonical SHA256
`7504cf9bf0b6371ea9af5228df5b0587dd8b32e08247c2b20d1c88860d977bcf`.
Owner8878 remains PID77508. Protected `cache/cea/test_key.json` remains SHA256
`6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`.
HEAD remains293223ebef190eaa647e67dc581eb186b2b5d987; inherited dirty work is
preserved. No goal-completion or physical/manufacturing accuracy claim.
