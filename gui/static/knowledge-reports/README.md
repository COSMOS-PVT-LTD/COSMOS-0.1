# P11 source-aware knowledge and reports preview

Default off. Enable `COSMOS_NEW_KNOWLEDGE_REPORTS_UI=1` with the existing new shell. Modern routes are `/app/workbench/knowledge` and `/app/workbench/reports`. Legacy intake/upload/chat/search/graph/review remains available at `/app/workbench/knowledge?knowledge=legacy`; all old knowledge APIs remain unchanged.

No corpus is seeded into user data by this feature. Navigation reads existing equation/source/assumption repositories and audit events, scoped to the existing knowledge workspace project. The filter searches titles, filenames and equation text without invoking a provider. Each source window contains at most 20 records. Existing semantic retrieval is still in legacy Maharshi. Global knowledge scope is the existing shared-corpus policy, not new multi-tenant isolation.

Claims use exact existing document-to-vault identity. Originals up to 4MiB are checked against their recorded hash; larger originals are explicitly not checked by this bounded preview. No guessed title/semantic match becomes a source citation. Show actual citation, page/section, version, recorded review and linked assumptions. Missing, mismatched or unreviewed evidence remains unavailable/pending. Recorded knowledge approval and test fixtures are not qualified human engineering acceptance. Unit metadata and model applicability are not inferred.

Reports require a current actual P09-backed P10 thermal receipt. They embed exact comparison/dataset/QA bytes, study/run/artifact/revision IDs, source/export/model/solver hashes, SI inputs, convergence/conservation/verification/discrepancy/uncertainty states, supplementary knowledge and limits. Knowledge attachment does not establish scientific applicability. Stale or missing inputs block a new report; history remains immutable. New review intent is separate from the original record and never grants acceptance. Reports are actor-owned, limited to 16 per actor/16 actors and ephemeral across server restart; download packages for retention.

Exports are canonical JSON, readable Markdown, escaped self-contained HTML and deterministic ZIP with file-checksum manifest. PDF is not added. Native geometry and binaries are not redistributed in report packages. The original `canonical_json` string's UTF-8 SHA-256 is the report ID. Preserve it: reserializing JavaScript display numbers may change byte identity. Rendering is pinned by version and source SHA-256; identical immutable inputs, title and renderer produce identical package bytes. An offline package is a historical snapshot, not a claim of current source freshness or a signed engineering publication.

## Isolated Mac launch

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
cosmos_p11_preview="$(mktemp -d /tmp/cosmos-p11-preview.XXXXXX)"
COSMOS_NEW_SHELL=1 COSMOS_NEW_KNOWLEDGE_REPORTS_UI=1 \
COSMOS_NEW_VV_UI=1 COSMOS_NEW_SIM_UI=1 COSMOS_NGG=1 \
COSMOS_NGG_RUNTIME_CONFIG="$PWD/docs/implementation/evidence/P08_2026-10-09/local-runtime.json" \
.venv-remediation/bin/python -m gui --root "$cosmos_p11_preview" --port 8835 --browser
```

Sign in using the local bootstrap Administrator profile. The default development account is `cosmos-admin` / `COSMOS-Dev-2026!`; these are not production credentials. In the isolated root, use legacy Maharshi for your authorized sources. Build the qualified OCCT sphere, create/run the P09 study, declare criteria and assess its P10 independent analytic comparison, then generate the report. Source inputs are not fabricated when the corpus is empty. Native manifest paths are Mac-local; missing or changed binaries fail closed and require requalification.

Stop your preview with Ctrl-C. Retain needed report packages first. Roll back by restarting without `COSMOS_NEW_KNOWLEDGE_REPORTS_UI`; the old Maharshi page returns and the new Reports/API/catalog entry is absent. No project migration, solver-default change or data deletion is performed. P12/G9, authentic independent reviewer signatures, physical validation and production readiness remain separate gates.
