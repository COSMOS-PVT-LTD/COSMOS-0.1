# P11 file-scoped plan — 2026-10-11

Baseline HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987` with prior working-tree changes. P10's 3,116-file seal was verified before modifications. Preserve prior bytes and evidence; use a new overlay.

## As-built reuse and scope

- Existing `knowledge/workspace/session.py`, vault, equation/assumption repositories and foundation audit provide intake, sources, review, retrieval and equation metadata. Preserve the legacy Maharshi page, upload/chat/graph/review and APIs. Do not introduce an LLM, new search engine or seed fabricated sources into user data.
- Add `knowledge/workspace/evidence_navigation.py` as a read-only bounded projection. Claims are existing equation entities. Bind exact document identity to a scoped vault source, check original bytes, display recorded review events and linked assumptions/applicability. Missing or tampered evidence is explicitly unavailable. A repository approval is not independent engineering acceptance.
- Add `validation/reporting.py`: actor-owned immutable reports from a current P10 thermal receipt and its actual P09 run/study/mesh/geometry QA. Preserve exact canonical JSON and hashes, status dimensions, methods, settings and source code references. Embed selected knowledge evidence only when source integrity is established. Render deterministic Markdown/escaped HTML and a deterministic ZIP review package; reuse the existing knowledge HTML exporter. No native geometry distribution or PDF renderer is added.
- Add `api/knowledge_reports.py`, `gui/knowledge_reports_ui.py` and `gui/static/knowledge-reports/` behind default-off `COSMOS_NEW_KNOWLEDGE_REPORTS_UI`. Modern Maharshi navigation and Reports route share shell/design-system controls. Keep legacy knowledge reachable explicitly; report history/inspection must not mutate active engineering inputs.
- Modify only `gui/server.py` and existing CI lint/type scope where needed. No physics, numerical defaults, P09/P10 contracts or frozen architecture replacement.

## Vertical-slice acceptance

1. Navigate an existing claim to source/checksum, equation, assumptions/applicability and actual recorded review; show unavailable evidence without inventing citations or signoff.
2. Create a report from a current actual geometry-bound P09/P10 comparison, with exact input revisions/methods/artifact/run/status/provenance and pending acceptance preserved.
3. Rebuild the same report/package byte-identically; verify manifest hashes, exported canonical bytes and escaped untrusted text. History, source staleness, tampering and actor/role/transport refusal receive negative tests.
4. Execute unit/HTTP/full regression, JS/type/lint, real browser/accessibility/layout/performance and source-to-claim fixtures. Retain report package, provenance integrity and before/after images. Record a phase software acceptance decision; P12/G9 and human/physical readiness remain separate.

## Dependency and boundaries

P04 shell → existing Maharshi projection; P09 immutable actual study + P10 hashed receipt → reproducible report → P12 release hardening. Knowledge sources are not automatically applicable to a simulation merely because a user attaches them. Sources/knowledge review events inherit existing persistence limits; reports are bounded ephemeral preview state and must be downloaded for retention. Durable signed engineering publication is not implemented in this slice.
