# CI repair and protected-main publication

Date: 2026-11-02. Scope: repository/test/dependency maintenance for development
snapshot `4ed449334d3a69540a10548275ce4991a0091acb`.

## Observed failures and repairs

The snapshot's [CI run](https://github.com/COSMOS-PVT-LTD/COSMOS-0.1/actions/runs/41427836580)
failed both generic Python jobs, lint/type checking, and the macOS dependency
audit. NASA CEA integration passed. GitHub correctly refused the protected-main
push. No branch protection or required status checks were removed.

| Failure | Evidence / repair |
| --- | --- |
| Material research CLI exception escaped after Core isolation tests | `tests/unit_tests/core/test_core_layer_independence.py` unloads Physics modules. Collect `scripts.prepare_material_research` alongside its dependencies in `tests/unit_tests/systems_layer/test_material_research.py`, preserving a single exception identity. Property limits and expected rejection remain unchanged. |
| R08 planning tests required ignored private engine artifacts | `tests/unit_tests/scripts/test_r08_engine_acceptance_proposal.py` now exercises its seven contracts using an explicit manufactured software fixture. Exact saved-engine checks remain available through `COSMOS_R08_ENGINE_EVIDENCE_ROOT`; production capture checksums stay unchanged. A separate test proves manufactured bytes cannot impersonate that engine. |
| Real guided CEA calculations ran without the optional native dependency | Guard only real native calculation paths in the three guided test files. Keep input policy, authenticated acceptance, replay, tamper and other non-native checks active in generic CI. Run all three files additionally in the pinned CEA 3.3.4 job in `.github/workflows/ci.yml`. |
| Ruff diagnostics and GuidedAPI typing | Correct import order in unpinned GUI/test modules, explicit subprocess intent in tests, and the optional `ProjectAPI.guided` annotation. Add pinned ReportLab development stubs. Preserve admitted native module bytes as explained below. |
| macOS strict audit reported vulnerable PDF/image/build dependencies | Update release Pillow to 13.0.0, pypdf to 6.21.4 and setuptools to 84.1.0. Align development pins and desktop ranges. Keep `pip_audit --strict`, the arm64 assertion, preview tests and build step active. |

Dependency release references: [Pillow](https://pypi.org/project/pillow/13.0.0/),
[pypdf](https://pypi.org/project/pypdf/6.21.4/),
[setuptools](https://pypi.org/project/setuptools/84.1.0/),
[types-reportlab](https://pypi.org/project/types-reportlab/5.0.0.20260911/).

## Preserve existing source-bound runtime admission

Eleven legacy modules are exact-byte inputs to retained OCCT/PicoGK/CAD runtime
receipts. Even import sorting changes their admitted method hashes. Applying
formatting fixes made the existing OCCT profile reject with
`OCCT_METHOD_CHANGED`. Those edits were reversed byte-for-byte; historical
receipts, native sources, numerical methods and admission checks were not resealed
or changed.

`ruff.toml` records narrowly scoped exceptions matching the original diagnostics:

| Admitted source | Existing diagnostic exceptions |
| --- | --- |
| `api/occt_component_runtime.py` | I001 |
| `api/pico_component_runtime.py` | I001 |
| `api/pico_components.py` | I001, F401, RUF012 |
| `plugins/geometry/pico_components.py` | I001 |
| `plugins/geometry/workers/pico_preview_worker.py` | I001, F841 |
| `systems/geometry/pico_component_builds.py` | I001, F401 |
| `systems/geometry/pico_mesh_qa.py` | I001 |
| `systems/geometry/pico_preview.py` | I001 |
| `api/cad_tools.py` | I001 |
| `systems/geometry/manufacturing_drawing.py` | I001, B023 |
| `plugins/geometry/workers/cad_inspection_worker.py` | I001, BLE001 |

These cover import ordering, unused names, existing shared class metadata, an
immediately consumed loop closure, and a structured native-worker error boundary.
They are explicit legacy lint exceptions, not a new qualification. Other lint
rules remain active. A future cleanup of these modules requires separately
qualified runtime profiles rather than rewriting old receipts.

Existing `configuration()` checks passed after preservation:

- `docs/implementation/evidence/PICOGK_COMPONENTS_2026-10-24/occt-runtime/runtime.json`
- `docs/implementation/evidence/PICOGK_COMPONENTS_2026-10-24/pico-runtime-v4/runtime.json`
- `docs/implementation/evidence/CAD_NATIVE_TOOLS_2026-10-24/inspection-runtime-v2/runtime.json`

## Validation

- Full local Python suite: **4,209 passed, 245 skipped**, no failures, in 405.58 s.
- JavaScript workflow suite: **505 passed**, no failures or skips.
- Pinned Ruff 0.16.10: all production packages/tests passed.
- Pinned Mypy 1.20.2: **476 source files**, no errors.
- Core isolation + material research reproducer: **48 passed**.
- Guided/Core/material tests with CEA unavailable: **75 passed, 7 native skips**.
- Guided tests with CEA 3.3.4: **34 passed**.
- Clean-tree R08 planning tests without `output/`: **8 passed, 7 explicit local-artifact skips**; no output folder created.
- R08 planning tests with the exact original saved-engine artifacts explicitly provided: **15 passed**. This is planning software coverage, not a geometry qualification or engine acceptance.
- Updated Pillow 13.0.0 / pypdf 6.21.4 imported from an isolated target: **66 passed**, no skips, across PDF extraction, real/scanned PDF pipelines, OCR boundaries, immutable reports and authenticated report exports.
- Updated pinned release requirement audit: **no known vulnerabilities found**,
  using pip-audit 2.10.1, strict mode and the complete pinned requirements list
  without dependency installation. Actual installed macOS dependency audit must
  also pass in CI.
- Development + desktop dependency resolution: compatible.
- Independent diff review: no changes to scientific formulas, material domains,
  runtime admission, production checksum checks or security audit behavior.
- `git diff --check`: passed.

Local full-suite environment uses Python 3.11, CEA 3.3.4, Pillow 11.3.0 and pypdf
5.9.0. Updated dependency pins and Python 3.12 require the fresh GitHub jobs; local
results alone do not establish that evidence.

## Publication boundary

Publish the repair to the existing development branch, wait for all five GitHub
CI jobs for that exact commit, then attempt an ordinary fast-forward update of
`main`. No force-push or administrator bypass is authorized by this repair.
GitHub check status and the remote branch SHA are the publication evidence.

No application installation, live project migration, generated engine model,
physical validation, R08 acceptance or engineering readiness claim is part of
this repair.
