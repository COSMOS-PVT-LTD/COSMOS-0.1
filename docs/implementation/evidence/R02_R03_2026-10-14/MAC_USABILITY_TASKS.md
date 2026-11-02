# Two genuine Mac usability observations — owner handoff

Status: PREPARED, NOT OBSERVED. The owner agreed to perform both tasks. Automated tests and the agent's native walkthrough are not human-study evidence. This is a single-owner formative evaluation, not institutional certification or a representative multi-participant study.

## Safe launch

Run in Terminal:

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
.venv-release-p12/bin/python tests/ui/r02_r03/mac_preview.py --native
```

Choose ENGINEER, then log in with `presentation-qa` / `isolated-presentation-qa`. These are synthetic fixture credentials, never production credentials. The helper uses new temporary storage, two explicitly synthetic designs, one draft Knowledge source/claim, and loopback port 8850. It does not open your normal projects or enable native geometry. If 8850 is already occupied, close the previous synthetic preview or use `--port 8851`; do not kill an unidentified process. Closing the preview stops its server and retains its recoverable temporary fixture. No dependencies are installed by this command.

Use the real native window, not a substitute browser. Start at its default 1440×900 size; also try its supported minimum 1100×700. Only synthetic UI data is in scope. Do not interpret outputs as hardware readiness.

## Task 1 — edit, recover and distinguish revisions (about 10 minutes)

Goal: demonstrate you can make and recover an unsaved edit, save deliberately, and identify what the software is actually inspecting.

1. Open Rocket Engine and select synthetic fixture A. Note the design name and active revision.
2. Find the design name input and replace its text with `Owner usability task A`. Do not save yet. Identify the draft/unsaved indication. Use **Undo draft edit**, then **Redo draft edit**. Record whether the exact original and new names returned, focus stayed usable, and the persisted revision remained unchanged.
3. With the edit still unsaved, try selecting fixture B. Choose **Cancel** in the native confirmation. Check that A and its unsaved text remain. Record the actual wording and any confusion. Then deliberately save A; inspect active name/revision and the persisted design DTO link. Do not assume a save has recalculated scientific results.
4. Inspect one historical change event. Explain in your own words the difference between the active revision and the inspected event, and whether this screen permits restoring a durable historical snapshot.
5. Use **Open commands** to find an existing workbench action. Note which actions are enabled/disabled. Toggle **Focus workspace**, press Escape, and try Navigation/Inspector/Diagnostics at the minimum window size. Can you recover the workbench without losing context?
6. Open Workspace controls; compare Guided, Standard and Expert. Try high contrast and 125% text. Confirm these affect display only. With VoiceOver if available, record control names, focus order and any unreadable value/unit/source table. Do not mark VoiceOver passed if you did not use it.

Write observations in `HUMAN_OBSERVATIONS.md`. Actual elapsed time, failed attempts and uncertainty are useful; do not fill PASS just because the script states an expected behavior.

## Task 2 — inspect and retain source-bound visual evidence (about 10 minutes)

Goal: retain an exact result and explain its source, units, uncertainty and validation boundary.

1. Open Visualization and Graphs, choose unchanged synthetic fixture B, and inspect the nozzle contour. Identify axial/radius units, source design/revision/result ID, freshness, verification, validation and whether uncertainty is quantified.
2. Try the chart zoom and reset. Inspect the exact source-data table. Try a log axis and note any refusal involving zero/negative values; an invalid view must not silently discard source samples or become a valid model.
3. Export SVG, CSV and source JSON using the chooser. Save each file separately through the native Save dialog. Give them new names; retain the `.provenance.json` with the SVG. Verify that closing the chooser returns focus and does not claim the runtime saved an unobserved file.
4. If comfortable in Terminal, independently verify your four files (replace the four paths with the exact files you saved):

   ```sh
   .venv-release-p12/bin/python scripts/verify_visualization_exports.py \
     "/absolute/path/source.json" "/absolute/path/exact.csv" \
     "/absolute/path/figure.svg" "/absolute/path/provenance.json"
   ```

   Record the actual result. A software export PASS is not scientific/experimental acceptance. If you skipped this command, record NOT RUN.
5. Open modern Maharshi Knowledge, expand **Explore the recorded Knowledge relationship graph**, and load it. Select the synthetic source using the keyboard-accessible node list. Check that its original text remains inspectable and that position/proximity are explicitly nonphysical. The graph does not substitute for the governed claim/source/review panel. Try pause/resume, collapse/reopen and high contrast.
6. Explain in your own words whether CURRENT, a software verification status, or a graph relationship establishes physical validation. Record any difficulty distinguishing these meanings.

## Return the evidence

Send both completed observation blocks back in this chat (or provide the filled Markdown file), plus any screenshots and the exact native export filenames. Do not include personal credentials, production project data or other confidential files. We will fix observed defects and recheck before claiming R03 human acceptance.

Full workflow-wide undo/durable historical restoration remains an R05 authority dependency; these tasks qualify the implemented draft and bounded actor-session flows only. Larger-project performance, full VoiceOver flows and all supported font/zoom/theme combinations are still separate qualifications, not inferred from these two observations.
