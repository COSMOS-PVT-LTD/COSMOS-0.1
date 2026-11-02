# P04 application shell

The shell wraps the existing authenticated workbenches. It does not replace their editors, handlers, calculation APIs or persistence. Default rollout is **off**.

## Enable and roll back

Set `COSMOS_NEW_SHELL=1` or `true` when starting the existing application. Keep the same configured data root. For example, replace the placeholder below with the existing app-data directory:

```sh
COSMOS_NEW_SHELL=1 .venv-remediation/bin/python -m gui --headless --root PATH_TO_EXISTING_APP_DATA --port 8780
```

Do not launch a second writer against the same store while an older application instance is running. Stop/start through the normal application workflow. The P04 implementation did not restart the user's server on port 8787.

Roll back with the `Use legacy layout` button. This restores the original DOM in place and retains unsaved rocket-engine input text and handlers. `Enable modern shell` reverses this presentation switch. The choice persists in a namespaced browser preference, not in the scientific store.

For a server-level rollback, unset the flag or set `COSMOS_NEW_SHELL=0` before the normal restart. `?shell=legacy` bypasses injected shell assets for a particular workbench route. A query cannot enable a server-disabled shell. Invalid or conflicting flags fail closed. `/app/projects` falls back to the original workbench hub when the flag or route override is off.

## What is implemented

- `/app/projects`: actual existing design summaries; bounded dashboard and project tree. No fabricated designs.
- Persistent UI project context, selected design, current persisted revision, read-only change-event inspection and explicit return to current.
- Seven navigation destinations, with native geometry and V&V visibly unavailable; every existing registry route retained.
- Three resizable/collapsible docks, keyboard resizing, persisted layout and default recovery.
- Guided/Standard/Expert density, source/SI inspection units, dark/high-contrast chrome and text scaling. These never become solver inputs.
- Searchable commands, notifications/profile/help delegation, breadcrumbs and original DTO evidence links.
- Knowledge-ingestion job observations, unavailable cancellation, failures and retry. No new physics/native run queue.
- Asynchronous read isolation, stale-response suppression, draft/busy navigation guards and in-place rollback.

## Boundaries

`Project context` is the existing local UI preference. A persisted propulsion design is not relabeled as an authoritative Project. `Inspected revision` exposes current stored inputs or a historical **change event**, not a full historical input snapshot. Activation/restoration of historical scientific inputs is unavailable.

The adapter provides only GET methods. Immutable, validated projections do not change the mutable DesignStore into an immutable publication service or fix its existing cross-writer race. Those contracts require later reviewed persistence work.

Display SI conversion uses an explicit unit map and rejects unsupported/nonfinite values. It reads both canonical Core `unit.symbol` DTOs and existing input `unit_symbol` DTOs. The original source magnitude/unit are retained unchanged.

Legacy scientific content stays outside the new `.cosmos-ds` styling islands. Theme/density controls apply to the shell, not a full workbench redesign. At narrow viewports the auxiliary docks start collapsed; at large text scale the header scrolls while project/revision context remains sticky and the editor retains space. Tables scroll rather than split numerical values across lines.

The existing knowledge polling cadence is reused; this is not a guaranteed-live scientific run monitor. Authentication and role enforcement remain server-authoritative. No native backend, new storage authority, schema migration, report publication or hardware-validation claim is enabled.

Implementation evidence and reproducible checks: `docs/implementation/evidence/P04_2026-10-09/README.md`.
