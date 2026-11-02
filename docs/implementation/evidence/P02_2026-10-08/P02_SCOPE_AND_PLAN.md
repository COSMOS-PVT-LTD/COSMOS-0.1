# P02 scope and execution record

Date: 2026-10-08. Target: this Mac, macOS arm64. Baseline Git HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987` (dirty checkout preserved).

Authority: modernization package P02 prompt, execution sequence, NGG contracts, geometry QA and release gates. P00 G0 permits this independent feasibility investigation. P01 G1 remains pending owner review; proceeding here does not approve UI designs or authorize P03.

1. Capture source integrity; inspect pinned official source and licenses.
2. Resolve the managed/native ABI and transitive dependency closure.
3. Build an isolated C# headless worker and, where supported, native runtime from source.
4. Exercise analytic primitive fixtures, union/difference/intersection, STL export and independent reimport at three voxel sizes.
5. Test process startup/shutdown and negative paths. Record latency, memory, artifact hashes and limitations.
6. Deliver manifest, license matrix, logs and a bounded feasibility decision.

All new work stays under this evidence directory or a dedicated temporary build directory. No production linkage, new engine geometry, architecture migration, dependency changes to COSMOS, commits, pushes or merge operations. Fixture tolerance measures software feasibility only, not manufacturing suitability or physical validation. Licensing findings are engineering due diligence, not legal advice.
