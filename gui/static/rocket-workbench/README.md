# P05 presentation boundary

Opt-in through `COSMOS_NEW_SHELL=true`; off remains original HTML. Only rocket HTML gets these assets. `shell=legacy` rolls back the entire shell, `rocket_ui=legacy` preserves P04 chrome with the original rocket view. Both UI rollback buttons preserve the actual field nodes, original handlers and unsaved drafts.

`propulsion-suite.js` remains the only editor/API-write owner. `model.js` holds immutable read-only projections, bounded quantity tables and service trace metadata. `view.js` moves original navigation to the left dock, applies semantic styling and adds read-only inspection/activity. Undo restores one in-memory draft edit and cannot cross a saved revision/design. No framework, storage model or numerical algorithm is introduced.

P03 ParameterTable, EmptyState, ErrorDetails and EvidenceLink are reused. Original CEA/subsystem plots stay attached to the original result renderer. Panel resizing, persistent context, command search, font scale, units preference and theme reuse P04. Shell SI display converts only explicit known source quantities; original editor labels and API payload units never change.

CURRENT is freshness, not convergence, verification or validation. Sensitivity, cycle power balance, solver progress/cancellation and physical validation remain unavailable unless supplied by the existing backend. Scientific source paths are trace metadata, not evidence of experimental acceptance. API evidence links are authenticated read-only original DTOs, not export/approval endpoints.
