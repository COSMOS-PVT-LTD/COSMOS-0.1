# Using the selected R06/R07 increment

Use the existing Mac development launch process with dependency-capable managed projects enabled. Do not migrate or switch owner data merely to view these controls. The temporary QA server used for qualification is closed; it was not an owner-data launch.

## Coupled sensitivity

1. In Projects, calculate and retain a current engine operating candidate through the existing explicit operating panel. It requires a saved actual divergent contour and, when selected, saved counterflow channel/wall inputs plus explicit sourced liquid/characteristic/window/solver/tolerance inputs.
2. Reload Projects after saving the operating result to refresh available sources. Expand **Coupled operating sensitivity**.
3. Select the exact retained current operating recipe. Enter supported parameter/response, 3–5 increasing explicit SI sample values containing the recipe baseline, h, admission budget (≤120 s), and range/step applicability source. There are no scientific defaults.
4. Run explicitly. Each case re-solves the model from the unchanged saved baseline. Inspect both invalid-domain reasons and h/h2 availability. A small derivative difference is not a measurement uncertainty or physical validation.
5. Use the source-bound plots and download exact input/record JSON and evaluated-case CSV. A plot export is a bundle: CSV/SVG plus full source and provenance. Keep all files together.
6. Interrupted/uncertain calls retain captured originals. Inspect capture history and use **Retry exact … captured command** rather than substituting a newer baseline. Inspect stale/historical originals without presenting them as current. Abandon local retry identity or discard drafts explicitly when needed.

The admission budget is checked between individually bounded solves. Client patience is 240 s; this is not native cancellation. The other operating form uses 180 s client patience. No global/default numerical tolerance was changed.

## Solved-candidate physical-validation preparation

1. Reload Projects after retaining the candidate. Expand **Propulsion experimental-validation preparation** and choose **Solved operating candidate · exact commit**.
2. Choose a target available in that profile and preview it. For example, `solved_chamber_pressure` is the actual solver output, not the old imposed pressure. GG speed is unavailable in pressure-fed; cooling quantities require actual cooling.
3. Declare intended use, applicability/review basis, matching-context tolerances and output acceptance criteria **before measurements**. Explicitly state UNKNOWN when prediction uncertainty is unavailable; it must not become zero.
4. Save the immutable plan, then download the empty CSV/provenance checklist. Do not copy predicted values into a file and call it experimental data.
5. Later import authentic documented measurements and evaluate them under the existing comparison workflow. Source assertions do not authenticate themselves. Physical acceptance remains unavailable without qualified independent review and a complete applicable evidence/uncertainty package.

The legacy baseline and solved-candidate adapters have different target availability; unavailable targets fail explicitly, without using a different model's prediction.

## R07 intent capture

1. Expand **R07 engine nozzle geometry intent**, choose an exact saved engine design with an actual CURRENT divergent contour.
2. Enter explicit radial wall thickness in metres and its design/applicability source, and distinct source/export tolerance inputs in metres. Both tolerances must be less than half the thickness. These are inputs, not a structural sizing recommendation.
3. Capture intent. Inspect saved snapshot/graph/source hashes, feature order and inner/outer sampled profile. The wall is a radial offset, not a normal offset. Do not infer a smooth original bell from piecewise-linear samples.
4. Download original JSON/plot bundles if needed. Status remains **CAPTURED_NOT_BUILT**, with no backend or artifacts and no engineering CAD export eligibility. Do not send this source document to manufacturing or simulation as a qualified solid.

Native profile/revolve build, engineering STEP/STL QA, editable graph revision operations, larger component templates and study handoff are the next R07/R08 work—not concealed behind the current intent preview.
