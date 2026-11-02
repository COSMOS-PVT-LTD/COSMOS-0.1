# P10 Comparison and V&V preview

Default off. Set `COSMOS_NEW_SHELL=1 COSMOS_NEW_VV_UI=1`; additionally enable `COSMOS_NEW_SIM_UI=1 COSMOS_NGG=1` with the qualified local runtime manifest for P09 imports and native comparisons. Route: `/app/workbench/comparison`. Legacy `code-comparison` remains unchanged.

The browser formats API results only. `validation/` owns immutable typed datasets/criteria, SI conversions, coordinate checks, discrepancies and conditional output-uncertainty summaries. Shared ProjectTree, ParameterTable (bounded 20-row windows), PlotPanel, ErrorDetails and ReviewSignoff are reused. The global shell supplies keyboard docks, themes and project navigation; this preview explicitly identifies its fixture project rather than pretending to use engineering DesignStore data.

Workflow: build an accepted OCCT sphere; create a current verified P09 run; import that run; inspect/declare criteria; create independent analytic reference or import documented `p10-thermal-v1` JSON; assess; inspect/download the receipt. Criteria must precede the first import of the reference source hash. Editing criteria clears the active assessment; old immutable receipts remain inspectable. No interpolation, extrapolation, inferred frames, unsupported unit conversion or model substitution occurs. Server ordering cannot establish off-platform blindness.

Thermal imports support Temperature K/degC, Radius m/mm, explicit matching SI geometry/material/boundary conditions, bounded 2–1024 samples, explicit standard output uncertainty or null, and source/calibration/instrument metadata. A checksum authenticates bytes, not authorship. Experimental claims always remain pending source/scope/budget review; synthetic test metadata is never physical evidence. The conditional formula uses declared output correlation; it does not silently propagate input/model errors or assign a confidence probability to a coverage factor.

Native captures compare matching fixed P07 fixtures. OCCT/PicoGK are distinct kernels; Gmsh/OCCT reimport is independent by tool/process but shares the OCCT implementation. Tolerances are the sum of predeclared per-operand analytic-reference bounds. Surface distances are per-operand bidirectional samples to the common analytic reference, not certified pairwise Hausdorff distance. Trusted external STEP import supports only centred 10mm metre-unit analytic sphere solids; the existing bounded native reader runs asynchronously. It is not a malicious-file sandbox. No arbitrary CAD/CAE parser, remote URL fetch, native command, file path or archive extraction is exposed.

Storage is bounded, actor-scoped and ephemeral. Download receipts for retention; durable engineering evidence storage, cryptographic independent reviewer signatures and release governance are not implemented. ReviewSignoff records intent only. Neither P09 nor P10 production handoff can be enabled by a client flag or an administrator preview action. Turning the P10 flag off removes the route/API/catalog addition without data migration or changes to existing engine physics.

Receipts include `canonical_json`, the exact server record string. Its UTF-8 SHA-256 is `report_id`; the browser checks this before display/export. Retain that string unchanged. Re-serializing parsed numeric fields can change `10.0` to `10` and is not a valid byte-integrity check. The download preserves both the exact string and convenient parsed display fields. Integrity checks do not authenticate imported authors or create reviewer signatures.

Local launch from the repository root (the existing qualified runtime manifest is Mac-local, not a distributable runtime):

```sh
cosmos_p10_preview="$(mktemp -d /tmp/cosmos-p10-preview.XXXXXX)"
COSMOS_NEW_SHELL=1 COSMOS_NEW_VV_UI=1 COSMOS_NEW_SIM_UI=1 COSMOS_NGG=1 COSMOS_NGG_RUNTIME_CONFIG="$PWD/docs/implementation/evidence/P08_2026-10-09/local-runtime.json" .venv-remediation/bin/python -m gui --root "$cosmos_p10_preview" --port 8787 --browser
```

Open `http://127.0.0.1:8787/app/workbench/comparison`. If that port already serves your app, stop your own instance or choose a free port. Stop the preview with Ctrl-C. Roll back by restarting without `COSMOS_NEW_VV_UI`; other feature flags are independent. Restart clears this preview's session evidence, so retain receipts first.
