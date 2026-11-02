# P01 — Accessibility and interaction acceptance plan

Scope: structural prototype and planned P03/P04/P12 implementation. No comprehensive accessibility certification is claimed.

## Invariants

- Critical engineering information remains readable at the supported native minimum 1100×700 and with text/zoom scaling. A compact mode cannot hide units, applicability limits or failures.
- Status names and meanings are conveyed in text, not color alone. “Current”, “completed”, “verified” and “validated” remain separate.
- Inputs have explicit quantity/unit labels. Missing required input is identified by code/cause/recovery; the error summary links to the exact field.
- Main navigation has an accessible name and current-page indicator. Existing Rocket active-step semantics are preserved. Do not incorrectly turn ordinary navigation buttons into an incomplete ARIA tab pattern.
- A skip link reaches the task editor. Navigation focuses the new task; inspection preserves the active draft and announces inspected context.
- Modals keep focus contained, support Escape where safe, and restore invoking focus. Default focus for reset/destructive confirmation is the safe “keep/cancel” action.
- Hidden panels expose expanded/collapsed state; controls outside the panel restore it. Width/height controls are keyboard-operable and layouts recover to defaults.
- Long-running status announcements are throttled and scoped; changes are not announced on every keystroke. Completion is not replaced by continuous noise.
- Source/assumption links have descriptive names. Graph/field inspection has an equivalent semantic table/tree pathway in future components.
- Font scaling, system contrast, Unicode/Greek coverage and reduced motion are tested. Prototype uses offline system fonts and no animation; final typography is a P03 decision.

## Executable prototype checks

Prototype uses semantic landmarks, labeled numeric inputs, text maturity badges, `aria-current`, `aria-expanded`, field-invalid state, a polite live status, focus-visible outlines and native dialogs. Synthetic job states have no animation or falsely computed progress. UI preferences use a dedicated prototype-only storage key.

Browser checks must record: field-error focus; modes preserve inputs; all seven destinations reachable; command dialog opens/focuses/traps/restores; reset cancel preserves state; layout collapse/recovery/persistence; active context visible at minimum viewport; and no outer horizontal overflow.

## Later production acceptance

| Scenario | Owner / gate | Required evidence |
|---|---|---|
| Keyboard-only open→edit→preflight→run→inspect→export | Frontend/scientific, G2/G4 | Scripted E2E with every critical control and error branch; production services, not fixtures |
| Screen-reader inputs/results/history/dialogs | UX, G2/G3 | Actual assistive-technology walkthrough; correct names/order/live announcements |
| Contrast and typography | Frontend, G2 | Computed rendered contrast including overlays, disabled exceptions and focus/status states; no blanket token-only compliance claim |
| 1100×700, larger desktop and text scaling | UX, G2/G3 | Screenshots/overflow/readability checks; context and primary actions retained |
| Resizable/collapsible/recoverable panels | Integration, G3 | Keyboard/mouse paths, focus recovery, persistence and defaults; preferences not scientific data |
| Large tables/trees and scientific fields | Frontend/viewer, G6/G7 | Virtualized semantic inspection, lazy loading, accessible alternatives and measured resources |
| Reduced motion / high contrast | Frontend, G2/P12 | Motion preferences honored in graph/viewer, noncolor status distinctions |
| Two internal scripted task studies | UX owner, G2 | Participant/task/outcome/friction record; automated checks cannot substitute |

The P00 source already contains valuable focus, live-region and reduced-motion behavior. Preserve it in the first integration. No proposed UI mode may bypass server-side checks or reduce scientific evidence disclosure for accessibility convenience.
