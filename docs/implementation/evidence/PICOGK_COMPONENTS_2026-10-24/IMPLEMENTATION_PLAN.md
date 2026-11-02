# PicoGK-led component generation plan

User authorization: "yeah do whatever is needed to implement picogk" (2026-10-24).
Scope: extend the existing geometry-worker architecture for real saved engine components; preserve OCCT, owner data and historical receipts. R08 is not started. No production redistribution or physical/manufacturing acceptance is authorized or implied.

## Verified starting point

- HEAD 293223ebef190eaa647e67dc581eb186b2b5d987; dirty working tree contains prior development. Preserve it.
- `Program.cs` currently accepts bounded sphere/Boolean implicit fixtures and STL only.
- `ComponentPlan` provides source-bound profiles, bores, cavities, cooling, pipes and rigid placements; the existing editor/build/QA/viewer and durable coordinator are reusable.
- Existing analytic component contracts remain analytic. A separately versioned implicit build policy must derive its own field graph from saved source parameters, not relabel a mesh or BREP as PicoGK output.
- Old combined runtime is stale/incomplete; temporary .NET root reports no installed SDK/runtime. Reuse native bytes only after historical digest verification and record any relocation as a new artifact.
- Baseline: 53 component/driver/runtime-admission unit tests passed (`output/picogk-component-baseline-2026-10-24.xml`).

## Work sequence

1. Restore pinned local .NET/PicoGK dependencies under an ignored persistent task directory. Verify hashes and license provenance; no global package installation.
2. Implement an isolated PicoGK component worker and a separately versioned implicit request/adapter/policy. Generate from saved profiles/cutters/placements, not OCCT mesh conversion. Preserve part identities and source/native/mesh provenance.
3. Reuse durable job lifecycle, explicit numerical settings, topology and per-part independent mesh reimport/formula checks. Add resolution studies and negative/lifecycle tests. Treat small unresolved features or failed QA as failures, never automatic accepted exports.
4. Integrate explicit PicoGK generation controls and retained attempt inspection into the existing component workspace and shared viewer. Keep analytic BREP clearance/drawing tools limited to compatible OCCT sources.
5. Qualify the new runtime and browser flow on isolated data, generate a real saved engine-component example, and report achieved scope and remaining limits with exact evidence.

## Completion: 2026-10-25

All five scoped implementation steps are complete for local research use. Persistent restored dependencies, direct native fields/mesh generation, independently checked durable artifacts, project-authorized UI and the actual saved 16-part browser workflow are implemented and verified. Runtime `pico-runtime-v4/runtime.json` is current-byte-bound; historical profiles are preserved. The actual large model also passes the unchanged 1GiB process guard and independent reduced-display checks after a bounded-memory display prepass. No source geometry, acceptance tolerance or resource ceiling was relaxed to obtain this result.

837 distinct targeted local checks passed; the exact saved-model job completed and its VDB/STL plus checked display diagnostics were retained. See [implementation and verification](IMPLEMENTATION_AND_VERIFICATION.md) for exact paths, hashes, failed-attempt history, test reports, the running isolated viewer and screenshot.

This completes the PicoGK integration task, not a full engine/hardware release: pressure joints, supplier seals, material/hot-flow/structural and physical readiness retain their separate gates. No owner data migration, original viewer restart, commit/push, or R08 transition was performed.

## Contract decision

Keep existing analytic model/save/build paths and their qualified runtime untouched. Add a separate opt-in PicoGK component build domain using the same saved component model as design intent and a derived IMPLICIT_FIELD graph. No automatic PicoGK-to-analytic-STEP conversion, manufactured tolerances, physical validation or simulation publication. This follows the dual-backend representation separation in the modernization specification; it is additive, not a frozen-layer replacement.

The new component STL encoding is distinct from the old sphere-fixture profile: it excludes only exactly zero-area triangles after explicit float32 metre conversion, records counts per part and never welds/smooths/removes positive-area faces. Grid-aligned planar components can have a larger zero-face fraction than spheres. That fraction is reported, not substituted for dimensional or topology acceptance. Full surviving topology, genus, orientation and sampled dimensional checks remain mandatory. The old fixture policy and its 1% refusal threshold are unchanged.
