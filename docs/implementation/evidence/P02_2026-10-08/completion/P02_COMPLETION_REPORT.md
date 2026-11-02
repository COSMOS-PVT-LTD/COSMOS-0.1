# P02 completion: isolated source-built feasibility candidate

Date: 2026-10-08. Base commit: `293223ebef190eaa647e67dc581eb186b2b5d987`, plus the preserved dirty checkout.

## Decision

**PASS for the isolated local source-built worker with the explicitly documented export profile.** This supersedes the phase decision in the original `P02_FEASIBILITY_REPORT.md`, not its observations. The original decision is retained in `P02_PRE_COMPLETION.json`. The unconditioned upstream export still fails; the product must not use it directly.

P01 owner acceptance is now recorded. P03 can proceed independently. Production PicoGK integration, redistribution, CAD-ready geometry and physical validation remain **not approved**. P06/P07 still require their contracts, architecture and release/platform gates.

## Repair and acceptance boundaries

`export_adapter.py:condition` removes only triangles whose computed cross-product area is **exactly zero**. It applies no positive area epsilon, vertex welding, geometric displacement or smoothing. Each subtraction export removes 22 collapsed faces; six nonfinite normals belong only to those removed faces. Retained vertex arrays must remain exactly equal. Retained normals are recomputed from their unchanged vertices. The adapter rejects nonfinite surviving normals, excess degeneracy, malformed/unlabelled STL and overwrite attempts. Its 1% degeneracy ceiling is a refusal safeguard, not a relaxed geometry tolerance. This is an explicit COSMOS feasibility adapter, not an upstream kernel fix.

`complete_feasibility.py:execute` permits one recorded resolution refinement for the already diagnosed 1 mm intersection. The initial failed QA remains in the result. The request remains 1 mm; the successful artifact explicitly records 0.5 mm. It does **not** claim a passing 1 mm intersection or hide a fallback. Production policy and cost approval for refinement are future work.

The predeclared acceptance formulas are unchanged: relative volume error at most `2*(h/r)^2 + 0.0005`, centroid error at most `2*h`, and forward analytic SDF residual at most `1.5*h`. Refinement applies those formulas at the actual finer resolution. The same independent STL parser/topology checks are used. Surface samples are not certified Hausdorff distance. Manufacturing tolerances, self-intersection certification, B-rep/STEP, simulation handoff and real engine geometry are outside this fixture set.

## Executed results

| Check | Result |
|---|---|
| Source-built candidate, 7 operations × 3 requested resolutions | 21/21 accepted; 22 attempts, one explicit refinement |
| Raw source-built rerun | 17/21; the same 4 known failures reproduced |
| Invalid requests / missing native runtime | 17/17 typed rejections, no artifact publication |
| Native lifecycle | 5 repeated cycles; zero recorded allocations/bytes after scope |
| Early termination and retry | Pass before request ingestion only; not mid-compute cancellation proof |
| Independent parser/QA unit tests | 10/10 |
| Export adapter / refusal / lineage tests | 6/6 |
| Three-resolution convergence groups in raw rerun | 4/4 decreasing volume-error groups; does not erase topology failures |

`accepted_benchmarks.json` retains every request, attempt, transformation, error ceiling, QA result, process event and external memory observation. `raw_retest.json` deliberately has `allPass:false`; its exit code 1 is expected evidence of unchanged raw defects. `ARTIFACT_MANIFEST.json` provides portable copies and hashes of the accepted and relevant failed exports. Independent re-audit is required before publication; no accepted export is labelled CAD-ready.

## Source, license and platform limits

The source pins, native build logs, notices and package hashes remain in the parent `dependency_manifest.json`, `P02_LICENSE_MATRIX.md`, `P02_BUILD_AND_REPRODUCE.md` and `licenses/`. No toolchain, managed source, native runtime or production dependency was replaced in this completion.

The candidate uses the minimal local source runtime rather than the unclosed prebuilt Boost/ICU/lzma/zstd bundle. OpenVDB is Apache-2.0 at the pinned revision. Static GLFW/ImGui and dynamic oneTBB/allocator dependencies remain explicit. Full upstream viewer/compression and ShapeKernel runtime behavior were not established. The source binary deployment target is macOS 26.0; the observed machine is arm64 macOS 26.5.2. This is not cross-platform, relocatable, signed or notarized distribution evidence.

Release blockers remain: complete binary/asset SBOM and notices (including embedded Jost OFL and native Skia closure), supported-platform CI, native relocation, signing/notarization and packaging. Do not reinterpret this bounded feasibility PASS as G5/G6/G9 acceptance.

## Reproduction

Use the parent build recipe to recreate the pinned source worker. Existing local paths, while available:

```sh
.venv-remediation/bin/python docs/implementation/evidence/P02_2026-10-08/completion/complete_feasibility.py --dotnet /tmp/cosmos-p02.rOuMVo/dotnet9/dotnet --worker /tmp/cosmos-p02.rOuMVo/source-worker/P02Worker.dll --output /tmp/cosmos-p03.pfPm6s/p02-new-reproduction
.venv-remediation/bin/python docs/implementation/evidence/P02_2026-10-08/completion/test_export_adapter.py
.venv-remediation/bin/python docs/implementation/evidence/P02_2026-10-08/test_mesh_audit.py
.venv-remediation/bin/python docs/implementation/evidence/P02_2026-10-08/completion/finalize_completion.py --verify
```

Choose a fresh output directory on every native rerun. Scratch build paths are not shipped dependencies. The final verify command uses retained artifacts and does not invoke the native worker. The original feasibility finalizer is historical and must not overwrite the superseding phase decision.
