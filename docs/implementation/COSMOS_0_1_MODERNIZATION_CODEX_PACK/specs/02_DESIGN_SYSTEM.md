> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# COSMOS professional scientific design system

## Visual direction
High-density scientific workstation. Dark space-inspired visual identity, restrained accent colors, precise alignment, minimal decorative effects. Do not copy the visual identity or trademarked layout of commercial CAD/CAE products.

## Token hierarchy
Define semantic tokens, not hard-coded colors in components: `surface.canvas`, `surface.panel`, `surface.elevated`, `text.primary`, `text.secondary`, `border.subtle`, `focus.ring`, `status.info`, `status.warning`, `status.error`, `status.success`, `science.field.low/high`. Use one central token registry and theme tests.

## Typography
Select a professional readable UI family with broad Unicode and Greek coverage. Use tabular numerals for parameters, logs and measurements. Establish 4 text roles: display, heading, body, numeric/monospace. Avoid small text in critical engineering controls.

## Component library
`CosmosShell`, `WorkbenchTabs`, `ProjectTree`, `PropertyInspector`, `UnitInput`, `ParameterTable`, `EngineeringStatus`, `JobMonitor`, `EvidenceLink`, `PlotPanel`, `Legend`, `ArtifactBrowser`, `SplitDock`, `CommandPalette`, `ErrorDetails`, `ReviewSignoff`, `ExportWizard`, `EmptyState`.

## Plot conventions
All axes MUST include quantity and unit. Residual plots MUST declare linear/log scale and residual definition. Field legends MUST show scalar range, units, clipping, and color map. Never use red/green alone to convey scientific status.

## Component states
Idle, hover, focus, disabled, loading, stale, invalid, warning, error, success. Every asynchronous operation MUST show a stable state and actionable failure details.

## Accessibility
Keyboard-only traversal, visible focus, screen reader names where framework permits, sufficient text contrast, no critical information conveyed by color alone, adjustable font scaling, and reduced-motion support.

## Performance
Virtualize large tables and trees. Avoid re-rendering entire viewports on parameter typing. Use throttled visualization updates. Measure interaction latency and memory on the target development device; define budgets from the baseline, not guesses.

## Design acceptance
Snapshot tests for shared components; automated keyboard navigation tests; contrast checks; two end-to-end user studies using scripted tasks (even if internal); visual regression baselines for all workbenches.
