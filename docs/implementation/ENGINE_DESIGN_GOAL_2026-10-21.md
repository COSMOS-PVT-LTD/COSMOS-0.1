# Active engine design-to-native-CAD goal — R08 HOLD

Latest2026-10-21 checkpoint:
`evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/CONNECTED_ENGINE_CURRENT_STATUS.md`.
The latest approved groove-fit / integral-concept subtasks are recorded in
`evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/GROOVE_FIT_AND_INTEGRAL_CONCEPT_CHECKPOINT.md`:
all five blind grooves are generated and native/browser verified; a separate
unqualified integral-metal / connected-coolant probe passed geometry diagnostics.
No supplier seal, bimetal bond, manufacturing or full hot-state acceptance is
implied. The full goal remains open and R08 HOLD.
The approved revised concept now has an independently checked16-metal-body CAD
candidate, matching head/plate/collector bolt patterns, actual front collector
outlet and rerouted fuel return. New matched wall/liquid/injector branch software
is verified within a bounded constant-area/source-response domain, not yet the
full native sector-cooled engine. Joint inspection exposes missing sealing and
pressure qualification. Full hot-state integration remains open; see
`evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/REVISED_CAD_MATCHED_FEED_CHECKPOINT.md`.
The named LPBF/HIP basis is approved for research only, not installed allowables.

Authority: user request2026-10-21. Goal remains active until demonstrated and the
user accepts achievement. Do not advance R08, claim full completion, change the
frozen layer boundaries, overwrite live revisions or invent physical evidence.

## Acceptance work packages

1. Diagnose the actual saved methalox recalculation and status semantics. Preserve
   exact r18 source before testing. Distinguish available model scope, configured
   inputs, execution failure, numerical verification and physical validation.
2. Repair normal managed-workflow execution: one captured analysis command,
   persisted engineering inputs, per-stage missing-input requests, independent
   stage execution, complete review/diagnostics even when some inputs are absent.
3. Reconnect selected PF/GG cycle and solved operating-point capabilities to the
   rocket workbench. Preserve immutable downstream solve provenance; do not make
   a circular graph or call cycle-class selection a solved balance.
4. Close scientific gaps relevant to this design: explicit sourced CEA transport,
   frozen-expansion failure diagnosis, suitable wall-stress regime, input and
   material/property applicability. Verify against independent primary references.
5. Prepare a sourced preliminary methalox proposal for user approval: burn
   duration, feed pressures/loss assumptions, injector hydraulics, coolant routing,
   material alternatives and property ranges. User authorized preparation only,
   not silently installing the proposal as accepted design inputs.
6. Run the approved inputs through baseline, feed/operating/thermal/structure
   calculations. Refuse unsupported states. Quantify performance targets,
   conservation, convergence, sensitivity and coverage rather than only green UI.
7. Complete native engine/component geometry coupling: exact calculated source
   lineage, chamber/throat/nozzle, injector varieties, matching internal cooling,
   and explicit missing manifolds/joints/plumbing. Do not call illustrative CAD
   hydraulically or thermally designed. Contract new topology before implementation.
8. Verify native units, B-rep validity, topology, STEP reimport, mesh accuracy,
   boundaries and source changes. Preserve original candidates/review history.
9. Verify the actual GUI create/edit/save/recalculate/build/download/restart flow
   and regressions. Document unsupported domains and all remaining gaps.
10. Physical accuracy/acceptance requires measurements with uncertainty, matching
    conditions and qualified review. Software convergence/CAD QA cannot satisfy
    that gate. Ask the user to accept the software goal explicitly before R08.

## Entry evidence

HEAD293223ebef190eaa647e67dc581eb186b2b5d987,316 dirty paths; preserve them.
Project01cd79e6-3923-4eca-ae1f-544cc30d8901,
design6524df5d-46f9-5b74-b214-8f5ada56acf6,
r18 saved v4 commit638d6ea3-4057-4b90-8dd4-8fc956b4772d.

Actual failures: material ID absent; thermal viscosity absent; structure blocked
by material failure. Injector/cooling configurations absent. Phase3/performance,
chamber and nozzle are CURRENT. Frontend sequential run stops on Phase4 failure
before review. Frozen graph/config/UI still claim all cycles unimplemented, while
R06 supplemental selected PF/GG and operating solvers exist. Consistency currently
compares Boolean dependency flags to the string`"false"`, skipping real failures.

This is a work register, not evidence that the work packages are complete.

## Progress — 2026-10-21, workflow repair / approved cold study

- User approved the exact preliminary assumptions/candidates. Approval record:
  `evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/PRELIMINARY_INPUT_PROPOSAL.md`.
  Supersedes the preparation-only restriction in work package 5 for those exact
  assumptions; does not approve missing material/thermal/physical evidence.
- One captured managed analysis, persisted engineering inputs, actionable missing
  inputs, independent stage execution and retained incomplete review implemented.
  Existing cycle/operating editors are embedded in the rocket cycle workspace;
  assessments still retain their separate exact-baseline authority.
- Selectable pressure-only closed-end Lamé model added alongside thin-wall;
  source/limits/tests in `evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/THICK_WALL_MODEL_CONTRACT.md`.
  Not a cooled-ligament or hot-material qualification.
- Original r18 source preserved. A separate approved cold-study design is now in
  the same project: `538a39dc-34c8-5261-a93c-933e43983960`. Injector hydraulics runs
  with exact NIST cold manifold states at 6 bar; 8 bar source states are retained
  separately. Duration5s and material candidate limitations are recorded.
- Next scientific work: frozen-CEA failure diagnosis; sourced heated-fluid domain
  and process-specific material curves; matched cooling/structural coverage;
  exact-baseline operating solve and integration of current evidence in review.
- Next native work: separate fuel/oxidizer radii/identity and feed routing, matching
  chamber/convergent/nozzle cooling topology, then new native qualification. Old
  equal-hole/channel concepts must not be called accurate calculated engine CAD.

The full engine/CAD goal is **not complete**. Physical validation remains pending
real evidence. R08 remains **HOLD** until the user's explicit acceptance.

## Latest checkpoint - frozen transport, source-matched CAD and coolant handoff

The earlier next-work entries for frozen CEA transport and distinct hydraulic
bores are now resolved within their documented software domains. All325 new
equilibrium/frozen study points converged. The new qualified native engine-v4
campaign passed67 tests. A source-current8-body assembly was generated with
distinct8-fuel/8-oxidizer ports, chamber, throat, nozzle and separately labelled
illustrative coolant domains. STEP, STL topology and semantic QA passed.

An additive read-only sector-cooling handoff now measures exact saved section
areas/perimeters, axial-plane hydraulic diameters and passage volumes. It binds
model/baseline commits and method hashes, rejects draft/source confusion and
explicitly does not substitute sector CAD into the rectangular thermal solver.
The actual UI/API flow and draft rejection were verified in isolated storage.

A new sourced NIST methane heating-envelope study retains raw phase/enthalpy
evidence and exposes the finite bulk-saturation budget. It does not install a
heated-property domain or claim thermal feasibility. Primary material sources
were inspected without turning typical/example data into generic hot allowables.

The user approved the named LPBF/HIP material research basis only. Isolated
condition-aware staging and bounded comparison studies are implemented; source
and temperature gaps remain explicit. No live catalog/input installation or
hardware allowable was approved. See
`evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/MATERIAL_RESEARCH_CHECKPOINT.md`.

External pipe/circuit implementation now has a retained19-body candidate with
actual STEP/STL QA and browser verification. Exact geometric fuel-through-
regeneration and direct oxidizer routes connect; pressure/thermal/joint closure
and hardware evidence remain open. See
`evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/EXTERNAL_PIPE_AND_CIRCUIT_CHECKPOINT.md`.
The original8878 viewer and saved owner design remain unchanged. R08 stays HOLD.

The latest joint/approved revised-concept checkpoint is
`evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/JOINT_GEOMETRY_AND_REVISED_LAYOUT_CHECKPOINT.md`.
An actual19-body matched-bolt candidate passed STEP/STL,177776 triangles, and
browser inspection. Fresh83-test native qualification and1252 targeted Python /
438 JS tests passed. The original injector's zero face land and1.5mm coolant/gas
lands require real joint design. The user approved the isolated separable-head
concept; its eight-test planner preserves gas volume and exposes pending native
operations. No whole-engine completion, material installation or hardware claim.

Current concrete remaining work and evidence:
`evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/THERMAL_MATERIAL_FEASIBILITY.md`.
Latest test and preservation record:
`evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/STATUS.md`.

User explicitly requested the existing8878 viewer remain running. No further
restart, live migration, original-design overwrite, commit or push was performed.
The new backend handoff is verified in isolation but awaits a future authorized
saved-state restart before it is available in that running viewer.
