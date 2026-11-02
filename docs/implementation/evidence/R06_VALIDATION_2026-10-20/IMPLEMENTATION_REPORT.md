# R06 — propulsion validation-preparation software

2026-10-20. Local dirty checkout at HEAD `293223ebef190eaa647e67dc581eb186b2b5d987`; not a committed/released build or remote-CI receipt. User confirmed **no measurements yet; prepare the validation workflow**. This increment is implemented and locally qualified within the scope below. **Whole R06 remains PARTIAL. Physical validation is NOT_PERFORMED.**

## Implemented scope and exact paths

| Layer | Implementation |
| --- | --- |
| Validation | `validation/propulsion.py`: immutable predeclared SI criteria, blank CSV template, strict bounded measurement/provenance parsing, exact condition/property/identity comparison, signed discrepancy, correlated reported-output uncertainty and explicit blockers. No new propulsion equations. |
| Systems | `systems/projects/propulsion_validation.py`: derives predictions/context from retained CURRENT baseline/results, not posted values; exact baseline head/CAS, plan-before-data-before-assessment dependencies, retained original CSV bytes and method/baseline hashes, actor-scoped idempotent commands and recursive source currentness. Uses existing R05 storage, no migration/schema change. |
| API | `api/propulsion_validation.py`: authenticated project namespace `/api/projects/{project}/propulsion-validation`, capabilities, exact preview, paginated plans/measurements/assessments, exact committed inspection and downloads. No acceptance endpoint; unknown fields/queries and posted acceptance flags are refused. Composition in `api/project_authority.py`, currentness in `api/context_projects.py`. |
| GUI | `gui/static/managed-propulsion-validation.js`, composed in `gui/static/projects.js`, scoped styling in `gui/static/managed-cycle.css`, asset/capability composition in `gui/server.py`. Projects panel has explicit empty criteria, source preview, saved plan, empty templates, later actual-data import, comparison and retained history. Existing draft/uncertain-operation handling reused. UI selects one target per plan; API supports multiple supported targets. |
| Downloads | New `PropulsionEvidenceSource` purpose header and `COSMOS-unreviewed-evidence-` filenames distinguish unreviewed evidence from the existing software-fixture exporter. Old fixture naming/headers are unchanged. |
| Tests | `tests/unit_tests/validation/test_propulsion.py`, `tests/unit_tests/infrastructure/test_propulsion_validation.py`, `tests/integration_tests/gui/test_propulsion_validation_http.py`, `tests/js/propulsion_validation.test.cjs`; explicitly synthetic helper `tests/fixtures/propulsion_validation.py`. |

Supported retained target quantities: core thrust, core mass flow, core specific impulse, coolant outlet temperature, coolant pressure loss, coolant heat pickup and divergent-nozzle peak hot-wall temperature. The last four require their actual current subsystem sources; they do not represent full chamber/engine cooling. No full-engine solved operating point or bidirectional combustion-feedback output is invented.

Plans retain intended use/applicability, discrepancy and combined-uncertainty limits, prediction uncertainty or explicit UNKNOWN, its basis, coverage factor/correlation and numeric condition/property tolerances. CSV has exact SI units and exactly the requested targets/context/properties. No inferred conversion, resampling, default measurement, missing-value substitution or automatic property lookup. Every numeric observation requires positive reported standard uncertainty; identity rows require exact identity and no numerical uncertainty. Metadata retains source/author/version/license, instrumentation/calibration, acquisition time, uncertainty basis, criteria-predefinition basis and synthetic/experimental plus calibration/held-out usage.

## Scientific and acceptance boundaries

The reported-output comparison uses the covariance propagation rule for a difference, `u_delta^2 = u_prediction^2 + u_measurement^2 - 2*rho*u_prediction*u_measurement`, evaluated in a stable equivalent form. Independent fixtures check 3/4/5 and perfectly correlated/anticorrelated cases. Expanded bounds use declared `k*u_delta`; **no coverage probability is inferred from k alone**. Basis: [NIST TN1297 Appendix A](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-law-propagation-uncertainty) and [section 6](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-6-expanded-uncertainty). This is not a complete input/material/model/numerical uncertainty budget: context/property uncertainties are retained, not silently propagated into model outputs. UNKNOWN prediction uncertainty never becomes zero.

Passing the software comparison requires all declared context matches, discrepancy limits, uncertainty limits and expanded-bound checks. Synthetic/calibration-only data remains explicitly unsuitable as independent physical evidence even if numeric checks pass. Asserted experimental/held-out metadata is **not authenticated** by this software. All assessments retain applicability, authenticity, complete-budget and independent-review blockers; `physical_validation=NOT_PERFORMED`, `independent_acceptance=false`, `production_handoff=false`. Execution, currentness, comparison pass and physical acceptance are distinct. Validation applicability must be bounded to evidence conditions, consistent with the [NASA validation-assessment tutorial](https://www.grc.nasa.gov/WWW/wind/valid/tutorial/valassess.html); no NASA certification/compliance is claimed.

## Local qualification

- Existing targeted baseline: **61 passed** (`baseline.log`).
- Focused final Python: **26 passed**, including the previous coupled-cycle HTTP regression (`focused-final.log/xml`).
- Full qualified Python: **3,489 passed, 93 skipped**, 192.70 s (`full-python.log/xml`). All preceding test identities retained; **25 new Python cases**. Skips remain explicit optional native-runtime and unfinished Knowledge hashability checks, not passes (`test-summary.json`).
- JavaScript: **416 passed, 0 failed** (`javascript.log`), three new tests.
- Ruff existing CI production/test target set and new QA helper: PASS (`ruff-final.log`); evidence collector checked separately.
- Mypy existing CI target set: **397 production files PASS** (`mypy.log`). Seven existing strict TypeScript consumers: PASS (`typescript.log`, success is empty output).
- Test-mutated `cache/cea/test_key.json` was copied, EXIT-trap restored and byte-compared successfully. Backup `/private/tmp/cosmos-r06-validation-cea.GZGwJ0`; current cache equals that backup. No deletion of cache or owner data.
- Preservation against preceding R06.3/4 manifest: **1,335 unchanged, 5 declared composition/style edits, 0 unexpected, 0 missing**. No preceding Core/Physics/Numerics source changed (`preservation.json`). New source manifest and exact preceding manifest hash are retained; old receipts are not rewritten.

The first focused run found a test asserting exact binary equality to 5 for an independently computed floating-point uncertainty. It now checks `approx(5, rel=1e-14)`. No application comparison tolerance or acceptance condition was relaxed. Initial type-check issues were resolved before the successful final suite. Earlier diagnostic logs are retained rather than presented as final passes.

## Full-story verification

The verification skill guided real UI → authenticated API → durable storage → download → restart checks, alongside the full HTTP import/comparison tests.

Only task-owned root `/private/tmp/cosmos-r06_3_4-qa.validation.mSMXgA`, synthetic QA account and localhost:8871 were used. The existing QA preview seeded a synthetic baseline, not a successful plan or measurements. In the real browser:

1. Saving without an exact preview was refused. Chose the actual retained thrust prediction; all generated criteria/tolerance numeric inputs were initially empty.
2. Entered explicitly labelled software-QA-only criteria with UNKNOWN prediction uncertainty. These numbers are **not recommendations or owner/hardware acceptance criteria**.
3. Saved plan commit `92311beb-126e-4871-8cfb-42d42b892894`, SHA256 `7cc4527eab8e3f9eb7909e845ae6903051f7f5f04505fa49e3295b790c7381e9` in project `cd2dc2af-fe6a-4ce4-ac26-252adb55f365`.
4. Downloaded original JSON, CSV and metadata through actual links. Checker `tests/ui/r06_validation/check_plan.py` verifies retained bytes/hash, unchanged exact baseline, **11 CSV rows with empty values and uncertainties**, entirely empty metadata values, UNKNOWN prediction uncertainty, and **zero measurement/assessment records**.
5. Gracefully restarted this task-created server with the same isolated root, reloaded and reopened the plan. Same commit/hash, CURRENT source/methods, AWAITING_MEASUREMENTS, NOT_PERFORMED and false independent acceptance; post-restart JSON download is byte-identical.
6. Browser console error list is empty (`ui-console.json`). Closed only the task-created tab and localhost:8871 server; retained QA root/downloads. User app/data root and existing localhost:8787 were not changed.

Receipts: `ui-plan-proof.json`, `ui-plan.txt`, `ui-restart.txt`, `ui-awaiting-measurements.png`, task server logs. HTTP tests separately exercise synthetic import/comparison, blank-template refusal, permissions, foreign project refusal, extra flags/queries, flag-off reads, stale-baseline originals and restart. None is hardware evidence.

## Remaining work and next dependency

**No full operating-point or bidirectional thermal/combustion solver was implemented in this increment.** Existing prescribed-component R06.3/4 assessments remain unchanged. The current cooling model covers the divergent nozzle with prescribed gas-side conditions; CEA rocket performance uses an adiabatic nozzle. Iterating heated fuel into that unmodified nozzle can double-count recovered heat or omit gas-side energy extraction. A numerical loop alone is not this missing model.

`EXECUTION_PLAN.md` records the required next contracts: supported flow-dependent feed/component characteristics and maps, unknowns/phase/property bounds, source-backed heated-reactant enthalpy, location-resolved non-adiabatic heat extraction, engine control-volume energy cancellation, nonlinear residual/bracketing/termination contracts, independent references and immutable downstream solved candidates without circular mutation of the frozen graph. These are open implementation/qualification tasks, not completed by this document. Wider R06 sensitivity, pressurant and conditioner capabilities also remain scoped/open in the backlog.

Physical acceptance additionally needs genuine compatible measurements, calibrated instrumentation/provenance, independently reviewed complete uncertainty/applicability and predeclared intended-use criteria, evaluated comparison and a qualified independent decision. User has none yet; this workflow prepares their collection/import and retains that gate. No live data migration, commit/push, CI execution, release, hardware operation or engineering acceptance was performed.
