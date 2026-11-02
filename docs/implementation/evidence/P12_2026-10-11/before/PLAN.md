# P12 file-scoped release hardening plan

Baseline: actual dirty Mac checkout, HEAD `293223ebef190eaa647e67dc581eb186b2b5d987`. Verify P11's 3,202-file seal first. Preserve pre-phase source, prior evidence, user data and the existing `dist/COSMOS 0.1.app`.

## Scope and reuse

1. Reuse existing authentication, GUI/application launcher, qualified geometry runtime, P09/P10/P11 contracts, Python/JS/browser tests and CI. Do not change equations, solver settings, accepted results, architecture or default feature flags.
2. Add a strictly opt-in **local release-preview** security profile: private generated first-login credentials, reject legacy data-root reuse, loopback/Host/origin/framing/request bounds. Default development behavior stays compatible. Add focused failure tests. It does not authorize production/hardware use or introduce an external service.
3. Add release tooling under `infrastructure/release/` and `scripts/`: exact source/contract freeze registry, installed Python/managed/native/tooling inventory with hashes and retained notices, reproducible Mac **source-only, external-runtime** preview bundle. Preserve the current bundle; build to a new unique output. Explicitly exclude native redistribution, private datasets, user state, credentials and third-party source. Ad-hoc signing is not Developer ID/notarization.
4. Extend CI with platform-focused source/profile/package checks. Record the actual current GitHub baseline separately from this uncommitted candidate. No automatic commit, push, workflow dispatch, tag, release or deployment; remote candidate CI requires publication authority.
5. Execute full/focused regressions, qualified native tests, a fresh cross-workbench Chrome journey, transport negative tests, restart/feature rollback with project/source bytes preserved, bounded stress and accessibility. Measure startup/project loads/viewport/geometry/export/solver plots/process memory on this Mac. Set only scoped local fixture budgets from measured baseline; no unsupported hardware/platform performance claim.
6. Run dependency audit and source/secret/security checks without changing the user's environment. Record findings, missing notice/source closure and platform support. Do not infer a license approval, official security contact or human signoff.
7. Retain release evidence, test summary, SBOM/notice inventory, rollback drill, frozen registry, documented platform matrix, changes and G9 decision. Seal the full candidate with predecessor before overlays.

## Gate and known blockers to verify

P12/G9 requires objective CI, packaging, SBOM/license, rollback and documentation evidence. Current green remote CI covers only HEAD, not modernization bytes. Default credentials and the old source-linked unsigned app are development artifacts. Prior native evidence contains unresolved distribution/embedded-asset license closure and absolute temporary runtime paths. SECURITY.md's contact is a placeholder; ask for the official channel while independent work continues. Windows/Linux/native redistribution, authentic independent review, measured experiment and production release must remain blocked if their required evidence is absent. A successful local preview is not a complete release.

## Dependencies

P11 immutable reports + P10/P09 verification + P08 qualified local runtime + P04/P05 legacy routes → opt-in security profile / contract registry / local package → isolated journeys and rollback → release evidence and G9 decision. No P13 or hardware operations.
