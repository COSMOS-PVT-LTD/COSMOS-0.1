# Material research checkpoint - not installed engine data

2026-10-21. User approved the **research basis only**: GRCop-42 LPBF/HIP and
conventionally postprocessed LPBF IN718. Installation, manufacturing recipes,
extrapolated hot allowables and hardware approval remain outside that approval.
R08 remains HOLD; the full connected-engine goal is not complete.

## Implemented boundary

- `systems/materials/research.py`: strict original-unit conductivity staging,
  retained document/transcription hashes, source/table locator, alloy/process/
  machine/powder/heat-treatment/orientation identity, reported statistic,
  unknown sample size and unresolved evidence.
- `EXACT_CONDITION_RESEARCH` requires complete equal identities and no unresolved
  evidence. Unknown values are not wildcards, even if unknown on both sides.
- `UNMATCHED_SAME_ALLOY_COMPARISON` is explicit and retains every mismatch/gap.
  Different alloys cannot substitute. Neither mode installs data or claims an
  allowable, physical validation or engine closure.
- Core converts Celsius to kelvin. Existing bounded Physics k(T) and Numerics
  perform the wall balance. The frozen architecture and existing material
  catalog were not replaced. No fallback was added to the GUI.
- `scripts/prepare_material_research.py` pins the exact inspected source and
  transcription hashes, creates a new isolated output folder, retains a
  predeclared study, checks independent piecewise-linear Fourier balances, and
  records successful research results and expected domain rejections.

Staging proves document identity and structural consistency, **not** that any
arbitrary manual transcription is correct or that three measured nodes bound
interpolation error. The exercised script additionally pins the reviewed
transcription. Synthetic unit tests need no downloaded proprietary PDF.

## Primary-source disposition

[Linde's June 2024 TRUFORM CU42 sheet](https://assets.linde.com/-/media/global/advanced-material-technologies/advanced-material-technologies/literature/40-5016_truform_cu42_amt_web.pdf),
PDF page 2, was downloaded, rendered and visually inspected. Thermal rows are
under **AFTER HIP**, separate **Mean** and **Mean -3sigma** columns, not the
AS PRINTED column or independent process datasets.

- Original temperatures: 25, 260, 537.8 degrees C; domain 298.15-810.95 K.
- Mean k: 323, 317, 303 W/(m K).
- Reported mean minus 3sigma k: 303, 309, 299 W/(m K).
- The second column is not a COSMOS-qualified lower bound. Thermal uncertainty,
  sample count, specific process/machine and HIP schedule are not supplied.
  Missing identity fields remain null; both curves are **unmatched comparisons**,
  not admitted LPBF/HIP engine curves. No pooling or new distribution is fitted.

Original-unit records: `GRCOP42_RESEARCH_TRANSCRIPTIONS.json`. Source SHA256:
`f542b2a0b829a0d6e10c9b1d47bef78d464df92659181d84530990e5e255c229`.
The isolated run retains the PDF and original transcription. No live catalog,
owner input or engineering property window was changed.

Other leads were not blended into these curves:

- [Velo3D's powder-specific sheet](https://velo3d.com/wp-content/uploads/2024/04/Velo3D-GRCop-42-Material-Datasheet.pdf)
  appears in search, but publisher PDF retrieval returned HTTP403 in this run.
  A cached search table was not relabelled a retained, inspected numerical source.
- [NIST's cryogenic IN718 page](https://trc.nist.gov/cryogenics/materials/Iconel%20718/Inconel718_rev.htm)
  does not establish the approved conventional LPBF condition. It was not
  substituted for that condition or joined to room-temperature data.
- [NASA/TM-2018-220129](https://ntrs.nasa.gov/citations/20190001243) is a process/
  tensile source, not a complete conductivity/strength surface. Its non-HIP
  high-strength outlier must not become HIP data.
- Previously inspected NASA/NIST sources and the IN939-table exclusion remain
  in `LPBF_HIP_MATERIAL_DATA_PROPOSAL.md`. No conductivity was inferred from an
  alloy name, room-temperature tensile result or ML prediction.

## Executed isolated study

Current artifacts: `output/material-research-bounded-2026-10-21-v2/`.
The first run remains intact in the sibling `v1` folder. The final run also
retains 13 selected implementation-file identities and Python version; this is
not a full environment qualification or release receipt.
Reproduce with the retained PDF, exact checked-in transcription, and a **new**
output folder:

```sh
.venv-release-p12/bin/python -m scripts.prepare_material_research \
  --source-pdf output/material-research-bounded-2026-10-21-v2/source.pdf \
  --transcriptions docs/implementation/evidence/ENGINE_WORKFLOW_REPAIR_2026-10-21/GRCOP42_RESEARCH_TRANSCRIPTIONS.json \
  --output output/material-research-bounded-replay-NEW
```

Four prescribed boundary cases per reported statistic: **8/8 software checks
passed**. Four bounded planar research balances returned; four unsupported
cryogenic/hot-wall cases rejected without extrapolation. Exact-condition
admission rejected in all eight cases. All accepted gas/conduction/coolant and
independent Fourier residuals were below the predeclared 1e-6 W tolerance.

Gas/coolant temperatures, coefficients and areas are **prescribed software
fixtures**, not solved methalox engine states. They do not size channels,
establish heat pickup, model ribs/roof/bimetal response or close the engine.
The small differences between these curves under the fixtures are not an
engine sensitivity, uncertainty or safety conclusion.

Focused material/wall tests: **52 passed**. Coverage includes altered sources,
condition matching, unresolved evidence, wrong alloy, unknown identity, original
units, nonfinite data, no installation mode, domain failures, reviewed-table
pinning, CLI-to-Physics execution and refusing to overwrite an existing output.
Broader targeted regression: **1199 passed**, 79.70 s, no failures/skips.
Scope: unit Physics, Systems, API, Plugins and Core; component cooling/interface,
design analysis and managed project authority HTTP integration. Not full-repo
tests, remote CI or hardware validation. XML reports are retained in the study
v1 folder. After the final additive implementation-manifest change, all 52
focused tests passed again (XML in v2). Focused Mypy (two production files) and
Ruff passed. Current coolant-v1
native runtime admission still verified; its receipts were not resealed.

## Still open

No matching IN718 k(T) curve for the approved condition is staged. Neither
candidate has complete condition-matched cryogenic/hot mechanical, fatigue,
creep and joint data. Supplier/coupon traceability, complete process conditions,
domains, uncertainties and qualified criteria are still needed. No automatic
data request or message was sent.

Software still needs full matched chamber/throat/nozzle cooling and heated
operating closure, external pipes, attachment/bolt/gland/seal geometry/checks,
and managed UI/persistence/export acceptance. Physical readiness needs genuine
measurements and qualified evaluation. These remain open in
`CONNECTED_ENGINE_CURRENT_STATUS.md`; research permission changes none to complete.
