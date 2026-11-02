> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# Native Geometry Generator — implementation specification

## Scope
Feature tree; parametric graph; 3d viewport; sectioning; geometry representation; build jobs; topology diagnostics; step/mesh export.

## Required screen structure
- Global COSMOS shell and persistent project/revision context.
- Workbench-specific left navigation and central task editor.
- Right contextual inspector with unit-safe values and evidence links.
- Bottom diagnostics, run/build history, errors and activity panel.

## UI states
Loading; empty; draft; stale; invalid; running; complete; failed; evidence pending; review accepted. Show only states that apply to the active workflow. Each error MUST contain a code, a cause where known, and a recovery action.

## Data contracts
Read from existing typed application services. Do not implement scientific algorithms inside UI components. Use immutable snapshots for expensive computations. Store UI layout preferences separately from scientific model data.

## Interaction requirements
Keyboard navigation; undo for reversible edits; explicit destructive-action confirmation; source-linked help; large-table virtualization; resizable panels; context-preserving navigation; consistent unit formatting.

## Test scenario
Generate reference geometry; inspect and validate it; export; reimport; trace back to exact design snapshot.

## Required evidence
Before/after screenshots; component inventory; API contract tests; accessibility checks; numerical regression where relevant; performance benchmark; change log.
