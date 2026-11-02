# R08 engineering geometry QA and interoperability

Authority: user explicitly requested R08 implementation on 2026-10-25. This supersedes the earlier R08 hold, not the separate manufacturing/physical/release gates. Preserve the frozen layers, existing component generators, owner stores, running viewers and historical receipts. No commit/push or migration is authorized.

## Story and baseline

Exact saved component → predeclared intended-use policy → explicit OCCT/PicoGK attempts → cancellable qualification job → retained evidence → independent authenticated review → guarded analysis-only export/handoff.

Existing component formula/topology/semantic checks, Gmsh STEP reimport, native allocation limits, durable jobs and independent-review patterns are reused. Gmsh and OCP share OCCT; separate APIs/processes are not separate kernels. New direct mesh comparisons must use actual encoded triangles, not two sets of distances to a common analytic reference. Existing VDB/STL and BREP/STEP formats remain distinct; no implicit-to-analytic STEP conversion.

Baseline: 39 existing targeted geometry/runtime tests passed, zero skips (`output/r08-baseline-2026-10-25.xml`). The checkout is dirty from prior development; all unrelated changes are preserved. Existing PicoGK v4/OCCT runtime receipts must remain current because this is an additive qualification service, not a generator rewrite.

## Requirement implementation sequence

1. GEO-01: immutable model-bound, predeclared SI policies, per-part limits, sourced area references and local critical-feature witnesses. Reject missing/extra bodies, unspecified tolerances and unsupported acceptance claims.
2. GEO-02/05: consume only exact successful generator/reimport evidence and verify original retained hashes, units, placement/role inventories, analytic integrals, area references, topology, semantic mapping and source/export separation. Unsupported certified mesh self-intersection claims fail closed.
3. GEO-04: supervised bounded AABB-tree nearest-point queries against actual full-resolution triangles, deterministic area-stratified bidirectional samples, maxima/percentiles and bounded outlier records; explicit critical witness-span checks. These are sampled witnesses, not certified Hausdorff distance or global minimum wall thickness.
4. GEO-03: explicitly selected three-resolution PicoGK studies of the same saved model, retain all resolution/process/deviation observations. No automatic refinement, tolerance relaxation or retroactive policy. Missing/infeasible evidence is not silently passed.
5. GEO-06: revision-bound whole-part and existing analytic face selections, explicit materials/mesh intent, remap proposals without inherited acceptance. No engine volume mesh or solver is implied.
6. GEO-07: exact evidence/head/hash-bound independent project-engineer acceptance/rejection and analysis-only package export. Failed/incomplete/stale/cancelled/unreviewed candidates cannot receive accepted export. Synthetic accounts are software fixtures only, never actual engine sign-off.
7. Project API and existing component workspace controls, immutable history/downloads/cancel/retry, separately source/runtime-byte-bound worker admission. Verify the full isolated UI/API/storage/response story and regression preservation.

## Decisions and limits

No universal engineering tolerance or material/mesh defaults will be installed. Real engine acceptance requires user/reference-supplied intended-use criteria and a genuine independent reviewer. Software qualification uses clearly labelled manufactured fixtures. A local witness span is not minimum-thickness certification. Certified arbitrary mesh self-intersection, automatic healing, arbitrary format conversion, manufacturing approval and physical validation are outside this qualified profile and cannot be requested as successful checks. Existing exploratory originals stay available under their original labels.

## Software completion

All seven requirements have implemented paths within the declared bounded component/software-analysis profile. 801 distinct targeted local checks passed; existing generator receipts remain current. See `IMPLEMENTATION_REPORT.md` for the requirement map, exact reports, direct-distance/refinement scope and full-story verification, and `OPERATOR_RUNBOOK.md` for use and still-required engine inputs. R08 **engine intended-use qualification is not closed**: no real-engine tolerance policy, policy-bound full-engine refinement study or authentic independent acceptance was fabricated. R09 was not started.
