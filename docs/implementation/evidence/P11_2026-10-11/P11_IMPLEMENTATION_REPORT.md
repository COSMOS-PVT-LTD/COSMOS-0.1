# P11 — Source-aware knowledge and reproducible research reports

Date: 2026-10-11. Baseline HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987`.

Decision: **PASS for the scoped P11 software vertical slice**, subject to the accompanying `P11_GATE.json` and verified `artifact_hashes.json`. This is not G9 release approval, qualified human acceptance, physical validation, or rocket-engine qualification. P12 has not been executed. No commit, push, PR, or merge was performed in this phase.

## Verified baseline and architecture

The complete phase instructions and applicable governance, UX, workbench, architecture and acceptance specifications were read before implementation. `PLAN.md` records the file-scoped decision. The existing working tree already contained earlier modernization and scientific changes. `baseline.json` pins its actual file bytes and commit; the predecessor P10 seal covered 3,116 files. The pre-change regression passed 2,685 tests with 76 skips.

The frozen architecture remains intact. Knowledge navigation is a projection of existing repositories, not a second scientific store. Report generation composes immutable P09 study/dataset and P10 comparison contracts. The GUI makes authenticated API calls and does not evaluate physics or run a new solver. No existing functioning module was removed or replaced. No architecture deviation or new external dependency was introduced.

| Reused capability | Exact implementation | P11 use and status |
|---|---|---|
| Knowledge intake, jobs, persistence, retrieval and review | `knowledge/workspace/session.py` | Preserved; modern navigation reads existing entities and source records. Root-backed session uses its existing vault/SQLite persistence; in-memory sessions retain their existing limits. |
| Original source bytes | `knowledge/workspace/vault.py` | Existing original/checksum interface, bounded integrity inspection. |
| Existing engineering equations and assumptions | Existing session foundation repositories | Exact entity/document identity and linked assumption metadata; no inferred unit, citation or applicability. |
| Existing knowledge HTML export | `knowledge/exporters/html_exporter.py` | Reused for the escaped canonical appendix. Existing PDF extraction-fixture writer is not a general engineering publisher. |
| Geometry-bound immutable simulation | `simulation/contracts.py`, `api/simulation_workbench.py` | Study/run/model/solver source hashes and SI settings retained without modifying these modules. |
| Immutable comparison evidence | `validation/service.py`, `api/comparison_workbench.py` | Current actual P09-backed thermal receipt, criteria and uncertainty retained. |
| Accepted native artifact and QA | `api/ngg_workbench.py` | Exact artifact source/export and geometry snapshot/QA identity checked. |
| Shared shell and controls | `gui/app_shell.py`, `gui/static/design-system/components.js` | WorkbenchTabs, ProjectTree, ParameterTable, EvidenceLink, ErrorDetails and ReviewSignoff reused. |

## Implementation inventory

| Files | Implemented status |
|---|---|
| `knowledge/workspace/evidence_navigation.py` | Read-only source/claim projection; existing project scope, 20-row paging, bounded text filter, strict IDs, exact claim-to-document-to-source identity, original integrity, citation/equation/version/units, assumptions and actual audit events. |
| `validation/reporting.py` | Actor-owned immutable canonical report records, separate review intents, live freshness inspection, deterministic JSON/Markdown/HTML/ZIP and file-checksum manifest. |
| `api/knowledge_reports.py` | Authenticated loopback/same-origin bounded transport, strict request fields, role/ownership checks and safe attachment downloads. No production acceptance endpoint. |
| `gui/knowledge_reports_ui.py`, `gui/server.py` | Default-off flag, shell integration, lazy service, modern Maharshi/Reports routes and catalog entry; legacy knowledge page/APIs remain accessible. |
| `gui/static/workbench/knowledge-reports.html`, `gui/static/knowledge-reports/` | Source search/inspection, exact evidence links, search draft undo/redo, report creation/history/lineage/downloads, separate preview review intent, pending acceptance, theme/focus/responsive recovery. Typed display contract and Mac launch/rollback README included. |
| `.github/workflows/ci.yml` | Adds the new knowledge projection to the existing Mypy scope. Existing Python/JS/Ruff checks discover the new code/tests. Remote CI was not triggered or verified. |
| `tests/fixtures/knowledge_reports.py`, new unit/HTTP/JS/UI tests | Source-to-claim, missing/tampered/stale evidence, strict transport/roles/ownership/limits, canonical bytes, renderer identity, escaping, reproducibility, rollback and actual native-browser flow. |

Only two pre-existing files changed during P11: `gui/server.py` and `.github/workflows/ci.yml`. Their exact pre-phase copies are under `before/`. The larger Git diff includes earlier user-owned work and is not attributed to P11. `source_integrity.json` verifies all other baseline bytes and the restored test cache. `predecessor_integrity.json` verifies the unchanged P10 seal through the two-file before overlay.

## Source evidence and scientific boundaries

Claim navigation does not guess source identity from a similar title or semantic match. Its approval display requires an intact original and the existing approved statuses plus the latest applicable audit event being APPROVE. An old approval followed by a later review event is not reused as current approval. Missing originals, checksum mismatch, citations, review or assumptions remain explicit. Original verification is bounded to 4 MiB; larger originals are marked not checked, not accepted. Extracted excerpts are bounded to 2,048 recovered characters and are not asserted to be exact page transcriptions. GLOBAL scope retains the existing shared-corpus policy; it is not new tenant isolation.

The production feature does not seed a corpus, fabricate citations, invoke a provider, or change legacy semantic retrieval. The retained source-to-claim fixture uses **explicit synthetic source, equation, assumption and review records** in an isolated test root. Its recorded approval is a test of navigation contracts, not a real approved engineering source or independent human signoff.

The end-to-end browser report used an **actual qualified OCCT sphere build**, actual accepted source BRep/STEP and QA, actual P09 finite-volume run, and actual P10 independent analytic comparison. No scientific mocks were used for that execution. Unit/HTTP contract tests use retained fixture services and are not counted as fresh native execution.

The report records exact study/run/geometry/artifact IDs, SI settings, model/solver source references, QA, canonical dataset and comparison receipt, criteria, discrepancy, convergence, conservation, software verification, unknown output uncertainty, review intent at creation and limits. Supplementary knowledge does not establish applicability to the simulation. Unknown uncertainty remains null. Experimental validation is `not-performed`, independent acceptance is false and production handoff is blocked.

## Reproducible report fixture and integrity

`report.json`, `report.md`, `report.html` and `review-package.zip` are retained. The ZIP contains exactly those three files and `manifest.json`; it does not redistribute native binaries or geometry. Entries are sorted, stored without compression and use fixed timestamps. The browser download in `downloaded-review-package.zip` is byte-identical. Each manifest file hash and exact canonical JSON byte string was checked. Renderer source identity is pinned at module import and recorded with its version; historical evidence is not silently rerendered by a different renderer.

| Retained identity | Value |
|---|---|
| Report SHA-256 | `1febf012d5d273897c1c731db2a4391b619f8ae0d67a62a096bf9669f38c1f65` |
| Study ID | `5dd82c0e2b5f318db933f0bb601f19e662d2743e51d88107a84cae6b0c9df488` |
| Run ID | `sim-db3a5aa504b741b18ef3388c2da77ce9` |
| Review ZIP SHA-256 | `6b332497e18216274cbf568b358991b44f581bc5bdc26b82031f4d80738aef4b` |

`provenance-integrity.json` records exact source/export/QA/dataset/receipt/renderer checks. `native-handoff/` retains the actual native bytes for audit, outside the review package. `p09-dataset.json`, `p10-comparison.json`, `native-source.json`, `source-to-claim.json` and `synthetic-source-original.txt` preserve the inputs. `signoff-report.json` states the software-only decision without fabricating signed acceptance.

Reports are bounded ephemeral preview state: 16 actors, 16 reports per actor, eight attached claims and eight review intents per report; maximum canonical payload 2 MiB and package 8 MiB. Downloads must be retained before restart. Offline packages are immutable historical snapshots, not live freshness attestations or signed engineering publications. Current report creation refuses stale/missing geometry, study/method or claim provenance. Historical bytes remain unchanged.

## Executed tests

| Check | Result and retained evidence |
|---|---|
| Baseline Python regression | 2,685 passed; 76 skipped — `baseline-tests.xml` |
| Final full Python regression | **2,736 passed; 76 skipped**, 0 failures/errors — `python-final2.xml` |
| Focused P11 Python (included in full count) | **51 passed**, 0 skips/failures — `focused-final2.xml` |
| JavaScript regression | **132 passed**, 0 failures — `javascript-final2.log` |
| Actual Chrome browser | **11 passed**, 0 failed/flaky/skipped — `browser-tests.json`, `browser-final2.log` |
| Ruff | PASS — `ruff-final2.log` |
| Mypy | PASS, **347 source files** — `mypy-final2.log` |
| Strict TypeScript display contracts | PASS — `display-contracts-final2.log` |
| Accessibility | Zero axe WCAG A/AA violations in the P11 workspace in dark/high-contrast themes — `accessibility-*.json`; not blanket application certification |
| Responsive inspection | 1,440/1,024/390 px, five lineage rows and no document horizontal overflow — `performance.json`, `final-view-checks.json`, final screenshots |
| Existing scientific HTTP parity | **Five cases identical to P10, tolerance 0** — `physics_parity.json`, `physics_after.json` |
| Report/source/native/ZIP integrity | PASS — `provenance-integrity.json`, final seal |

The full regression's 76 skips are not passes or qualification proof. The real native-browser test supplies fresh scoped OCCT evidence; it does not rerun every predecessor native fixture. Retained browser timing is a small local fixture, not a large-corpus or whole-app performance budget. `collection-performance.json` measures only the evidence-collector process.

Initial diagnostic failures are retained in the logs. They were resolved: native QA must retain its exact noncompact serializer bytes; same-page claim links need a hashchange handler; workspace themes/focus must use existing shell tokens; the shared table class is `ds-table-scroll`, with a nonwrapping Unit column. Final browser tests cover the scientific/rendering code; the later CSS-only correction has separate read-only three-width and two-theme accessibility proof and leaves report history unchanged.

## Requirements, security and rollback

The scoped evidence supports GOV-001/003/004/005/007/008/009 and UX-001–007; it does not claim blanket completion of every platform requirement. T-017 missing-source behavior, T-015 keyboard access, T-011 stale upstream evidence, T-012 immutable history and feature rollback are tested. The G0–G8 predecessor proof is preserved, not rewritten; this phase records `P11_SOFTWARE`, not a new G9 release pass.

Downloads use safe hash-based names, explicit MIME, nosniff and restrictive CSP. Requests require authentication, loopback transport and same-origin mutation checks, bounded bodies, exact fields and strict identifiers. There is no new file upload, arbitrary path, arbitrary URL fetch, command execution, geometry distribution or production publication. Test-only fixture sources and default development credentials must not be represented as production authorization.

Launch/rollback instructions are in `gui/static/knowledge-reports/README.md`. `COSMOS_NEW_KNOWLEDGE_REPORTS_UI` is default off and requires the existing new shell. Restart without it to restore legacy Maharshi navigation and remove the new Reports/API/catalog entry. No migration or deletion is required. Own isolated test servers are stopped after retaining evidence; the user's application and project data are untouched.

## Readiness and next phase

Ready for **P12_RELEASE_HARDENING** within the recorded research-tool scope. Remaining release work includes actual remote CI, packaging, dependency/license/SBOM and operational/security/rollback evidence. Durable signed multi-user engineering publication and a general engine report/PDF publisher are not delivered by this slice. Experimental readiness still requires authentic measured data, compatible conditions/material properties, measurement and model uncertainty, predefined acceptance criteria and qualified independent evaluation. Green software tests and synthetic knowledge records do not satisfy those requirements.

Verify the handoff without rerunning science:

```sh
PYTHONPATH=. .venv-remediation/bin/python docs/implementation/evidence/P11_2026-10-11/finalize_evidence.py --verify
```

