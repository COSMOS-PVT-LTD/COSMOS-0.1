# P12 release hardening — evidence-backed handoff

Date: 2026-10-11. Repository: COSMOS-PVT-LTD/COSMOS-0.1. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

**Phase status: PARTIAL. G9 production release: BLOCKED. Local research preview checks: PASS.** This distinction is intentional. Executed local tests and inventory do not establish distribution approval, independent security/engineering acceptance, operational readiness or physical/hot-fire validation.

## 1. Baseline and preservation

HEAD remains `293223ebef190eaa647e67dc581eb186b2b5d987`. Work began in the dirty P11 checkout, not a clean release commit. `baseline.json` pins 3,181 git-listed files; the P11 predecessor seal covers 3,202 files. Existing scientific changes, datasets and prior native evidence belong to the user and were preserved.

The only previously existing product/governance files changed by P12 are `.github/workflows/ci.yml`, `.gitignore`, `SECURITY.md`, `api/authentication.py`, `gui/server.py`, `gui/static/app.js`, `gui/static/rbac.js`, and `scripts/build_macos_app.sh`. P12's own initial plan was extended after observed browser failures. Exact before copies and phase-only changes are retained in `before/` and `p12-scoped.diff`. The original `dist/COSMOS 0.1.app` remains unchanged. The CEA synthetic test cache was restored byte-for-byte after tests. Old environments and qualified native bytes were not upgraded or deleted.

`source-integrity.json`, `predecessor-integrity.json` and the final `artifact_hashes.json` record preservation and the final candidate, including ignored phase evidence and final app bytes. Verification command:

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
.venv-release-p12/bin/python docs/implementation/evidence/P12_2026-10-11/finalize_evidence.py --verify
```

No commit, push, PR, workflow dispatch, tag, release, deployment, DNS change or mailbox provisioning was performed.

## 2. Implemented vertical slice

| Path | Implementation and boundary |
| --- | --- |
| `infrastructure/release/security.py` | Opt-in `local-preview`, private generated first-login credentials; strict JSON; loopback/Host/origin/body/framing limits; 8 connection threads, bounded admission wait, overload 503 and recovery. Unknown production profiles refused. |
| `api/authentication.py` | Additive bootstrap-password parameter; no legacy credential reset or silent migration. |
| `gui/server.py` | Preview-only guards, timeout and response headers; private first-login guidance hides the old shared password. Default development behavior stays compatible. |
| `gui/static/rbac.js`, `gui/static/app.js` | Existing frontend permissions safely initialize in either script order. Backend authorization and permission definitions do not change. |
| `infrastructure/release/inventory.py` | SHA-256 source/contract registry, installed distribution file hashes and retained notices. Metadata license names are not legal approval. |
| `infrastructure/release/launch_preview.py` | Exact source/Python binary checks, explicit private profile, defaults-off modern/native flags. Source-linked, external Python/native runtime, not standalone. |
| `scripts/build_release_preview.py`, `scripts/build_macos_app.sh` | New separate Mac arm64 bundle; refuses overwriting an existing output. Legacy bundle/build remains available. |
| `requirements-release-macos.txt` | Separate exact environment; patched image/PDF/development packages, unchanged CEA 3.3.4 and NumPy 2.4.6. Existing requirements/environment unchanged. |
| `.github/workflows/ci.yml` | Added arm64 Mac profile/package/advisory checks, extended existing typing scope. Defined locally; candidate job has not run remotely. |

New boundary tests are in `tests/unit_tests/infrastructure/test_release_hardening.py`, `tests/integration_tests/gui/test_release_preview_http.py`, `tests/js/release_rbac.test.cjs`, and `tests/ui/release_hardening/`. No equations, accepted physics values, numerical methods, frozen model contracts, geometry kernels, state ownership or scientific defaults were changed.

## 3. Executed tests

Exact commands, counts and skip reasons are in `test-summary.json`.

| Check | Recorded result |
| --- | --- |
| Pre-P12 Python baseline, old environment | 2,736 passed, 76 skipped |
| Final full Python suite, separate preview environment | **2,803 passed, 74 skipped** (`python-release-final.xml/.log`) |
| Focused profile/package/HTTP boundaries | **45 passed** (`focused-final.xml/.log`); subset of full suite |
| Qualified native geometry/simulation/comparison regressions | **67 passed, 2 skipped** (`native-final.xml`); two P08 flag-specific tests then **2 passed** (`native-p08.xml`) |
| JavaScript actual-source tests | **134 passed**, zero failed (`javascript-release.log`) |
| Fresh packaged browser journey | **7 passed**, zero retries/flaky/skipped; no page errors or failed assets (`browser-tests.json`) |
| Actual Cocoa/WebKit native window | PASS; login DOM/private guidance observed, no browser fallback (`native-window-final.json`) |
| Ruff / scoped Mypy / strict TS contracts | PASS; Mypy 351 source files; seven existing TS consumers. Not a claim of whole-GUI Python typing. |
| Scientific HTTP parity | Five cases exactly match P11, zero tolerance, identity/time metadata excluded (`physics-parity.json`) |
| Pip consistency, shell syntax, plist and CI YAML | PASS; YAML/structure is not remote candidate execution |

Optional skips are recorded, not interpreted as passing features. Native tests reuse the exact qualified P08 manifest and 99 native file hashes; only the evidence output directory changes. Fresh P12 fixture outputs are in `native-regression/`; prior artifacts were not reused as newly executed evidence.

The first native invocation mistakenly targeted an existing predecessor fixture directory; overwrite refusal stopped it and the run was interrupted. The corrected invocation used a new P12 evidence directory. The predecessor seal verifies no historical artifact changed. Initial browser harness/launch-path failures and genuine saturation/RBAC failures remain in diagnostic logs; successful final results do not erase them.

## 4. Actual end-to-end provenance

The packaged Chrome journey built a qualified OCCT sphere fixture, attached its exact artifact to P09 steady spherical conduction, completed P10 analytic comparison and generated a P11 immutable report. This is a representative software research fixture, not a detailed engine, arbitrary solver or physical experiment.

`packaged-report.json`, `packaged-dataset.json`, `packaged-comparison.json`, `packaged-geometry-qa.json`, `packaged-native-handoff/source.brep`, `packaged-native-handoff/export.step` and `packaged-review-package.zip` retain exact lineage. Source, export, canonical report, dataset, geometry QA, renderer and archive-manifest hashes were checked. Offline ZIP re-render reproduces the downloaded bytes. `provenance-integrity.json` records the proof. The report has no invented knowledge claims, experiment or independent approval.

## 5. Packaging and supported platform

Built app: `dist/P12-release-preview/COSMOS 0.1 Release Preview.app`.

`unsigned-payload.json` proves identical unsigned contents across two builds at the same absolute source/Python paths. `package-source-manifest.json` pins **881 source files**. An ad-hoc signature was applied only to the new preview and passes `codesign --verify --deep --strict`. `package-integrity.json` seals the signed bytes. Gatekeeper assessment **rejected** it (`gatekeeper-assessment.log`). Ad-hoc integrity is not Developer ID identity, notarization or authorization to distribute.

| Target | Qualification |
| --- | --- |
| This Mac: Apple M1, arm64, macOS 26.5.2, 8 GiB, CPython 3.11.4 | Local source-linked browser journey and actual Cocoa login smoke executed. Not a portable installer or supported lower-OS range. |
| Qualified C#/dotnet/native geometry runtime | Existing exact manifest/worker/source hashes exercised. Absolute temporary dependency prefixes; relocation/signing/source/license/security closure unresolved. |
| Mac Intel / other macOS releases | Not qualified; no release claim. `LSMinimumSystemVersion` metadata does not establish compatibility. |
| Windows | Packaging/native journey NOT RUN; release BLOCKED. |
| Linux | Legacy Python CI exists on baseline HEAD; modernization/native distribution not qualified; release BLOCKED. |

Installed dependency hashes are an inventory snapshot, not a launch-time check of every dependency. External runtime availability and mutation remain limitations. No native binary, user credential or user project is inside this source-linked bundle.

Launch, credentials and rollback are documented in `documentation/development/COSMOS_P12_RELEASE_PREVIEW.md`. Keep this checkout, exact environment and qualified native runtime available. The launcher refuses source drift. The original development app remains a development configuration with a known password, not a production alternative.

## 6. Security and license findings

`release-audit-final.json` reports **zero known advisories for the separate preview Python environment at audit time**, not zero vulnerabilities globally. Pillow 12.3.0, pypdf 6.20.0 and patched development/install tooling were selected there. The unchanged legacy/native-worker environment still has advisory findings in Pillow, pypdf, pytest, pip and setuptools. External qualified **VTK 9.3.1** has three reported advisories (PYSEC-2025-224/225/226; audit lists 9.5.1 as a fixed version). Updating a qualified kernel requires a separate compatibility and geometry requalification; this run did not silently substitute it.

Bandit over explicit application/scientific packages retained 44 findings: 33 LOW, 11 MEDIUM, zero HIGH. The controlled profile-update SQL uses literal column names and parameterized values; the preview supplies a loopback native-window URL. Nine XML parsing findings remain OPEN pending hardened/resource-bounded untrusted Office import qualification. These are not blanket-waived. `security-review.json` has per-finding triage. This is not an independent penetration test, hostile-document clearance, OS/interpreter CVE audit, or production security signoff.

`secret-scan.json` found zero targeted literal token patterns and no generated preview password in phase evidence. It is not a full Git history/all-secret detector. Unique login files remain outside repository evidence.

The authoritative inventory is **`inventory-release-final/`**: CycloneDX 1.5 schema validated, **208 components**, **97 installed Python distributions** across preview/qualified CAD/unchanged worker environments, **99 native file hashes**, retained notices, managed/source/npm references and official schema hashes. Earlier `inventory*` directories are diagnostic snapshots, not the final frozen registry. Installer/resolver archive hashes are in `release-resolver-final.json`, `schema-install-report.json`; installed-tree hashes are distinct from original wheel provenance.

`inventory-release-final/license-gaps.json` keeps distribution approval false. Missing/ambiguous metadata/notices, Gmsh GPL compatibility, OCCT exception obligations and embedded/transitive PDFium/Skia/VTK/Boost/ICU/compression/font/source closure need qualified review. No legal approval is inferred from package names or a top-level license. CPython 3.11.4 and OS/runtime patch/redistribution closure are not qualified.

## 7. Measurements and release budgets

Small local fixture measurements are in `browser-measurements.json`, `stress.json` and `responsive.json`: startup about 1.47 s, route loads 157–329 ms, geometry build/inspection 14.84 s, one solver run plus two plots 153 ms, two byte-identical report exports 23 ms. Serial project-load p95 was 12.98 ms. A 32-request concurrent sample completed with 32 HTTP 200 responses, maximum 103.50 ms, under the declared `max(1000 ms, 20 × measured serial p95)` local fixture budget. Saturation 503/recovery is separately covered by the boundary test.

Sampled server RSS was 33,505,280 bytes. It excludes native workers, the browser/native window and whole-system peak. Focus interactions and bounded page widths were checked at 1440/1024/390 px; axe found no scoped WCAG A/AA violations in dark/high-contrast for five workspaces and keyboard focus checks passed. This is not complete application accessibility certification, screen-reader qualification, sustained viewport/solver throughput or representative large-model performance. Whole-system peak and supported-target performance budgets remain release qualification work.

## 8. Rollback, migration and retention

`rollback-drill.json` proves same private root restart without modern/native flags, unchanged persisted project SHA and unique bootstrap credential, working legacy knowledge route and modern API 404 responses. No destructive schema down-migration or legacy-user account reset occurred. Boundary tests refuse silent reuse of a legacy authentication root.

Research run/comparison/report history is in-memory and intentionally lost on restart. The downloaded exact ZIP and native evidence were retained before rollback. This does not establish general migration of arbitrary historic user datasets or durable report publication. The isolated fixture contained no user-supplied knowledge documents; prior repository/user originals remain covered by preservation checks.

## 9. Repository CI and signoff

`github-ci.json` confirms the latest baseline HEAD CI succeeded: run `37204671617` at `https://github.com/COSMOS-PVT-LTD/COSMOS-0.1/actions/runs/37204671617`. It covers committed baseline bytes, **not this dirty P00–P12 candidate**. The new Mac job and complete candidate must run after authorized publication. No remote execution or merge is implied by local green tests.

`release-signoff.json` records automated checks and missing role acceptances. Release owner, security/legal/platform and engineering acceptance are pending. User approval of earlier phases does not authorize release signoff, production/hardware use or commercial distribution. `G9_GATE.json` stays BLOCKED, with exact closure criteria.

## 10. Domain recommendation and next actions

Use the purchased company domain for a monitored role mailbox: **`security@cosmospvtltd.com`**, not an individual engineer's address. Select the company's email provider; provision the mailbox/shared inbox, verify required provider mail records, enable MFA, assign an owner and backup and test external inbound/outbound delivery. Once working, publish a security-reporting page and replace SECURITY.md's explicit `NOT_CONFIGURED` state with the real tested channel. A domain or website does not create email service. No mailbox, DNS, paid service or company website was changed here. Guidance: [custom-domain email setup](https://support.google.com/a/answer/6142901) and [CISA MFA](https://www.cisa.gov/audiences/small-and-medium-businesses/secure-your-business/require-multifactor-authentication).

Before G9 can pass: remediate/requalify worker/native advisories and untrusted imports; close legal/embedded notice gaps; select a supported patched runtime and qualify standalone installation/signing/notarization/target platform/performance; publish the exact candidate with authorization and obtain green candidate CI; establish the private reporting channel and obtain qualified human acceptances. Physical readiness separately requires actual measurement evidence and evaluated uncertainty/acceptance comparisons, not synthetic data or these software tests.
