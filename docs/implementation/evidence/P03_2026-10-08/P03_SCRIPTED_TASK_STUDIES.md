# P03 internal scripted task studies

These are **agent-executed, browser-automated internal task walkthroughs**, not recruited-user research. They use explicitly synthetic inputs and events in the component laboratory. No scientific job, actual review certificate or file export is submitted. Executed outcomes are in `browser-tests.json`; both studies pass without retries.

## A — Engineering parameter and evidence workflow

Script: `tests/ui/design-system/components.spec.cjs`, test `internal study A`.

1. Enter explicit zero chamber pressure in a draft fixture; observe canonical `0 Pa`.
2. Clear the field; observe invalid/missing text and the preserved last accepted zero. Blank does not become zero.
3. Enter `1.25 MPa`, switch to kPa and observe `1250 kPa` with canonical `1250000 Pa` unchanged.
4. Enter `Infinity`; invalid text persists. Attempted unit switching is refused without replacing the draft or last accepted value.
5. Move tabs with the keyboard; active synthetic context changes without calculation or evidence claims.
6. Follow the artifact evidence link and inspect independently labelled **unverified** status despite completed/converged fixture dimensions.

Result: all assertions pass. Related additional checks cover repeated display switching with exact SI preservation, keyboard-visible focus, missing verification/validation evidence and stale export refusal. Usability implication: the unit/evidence contract is traceable; ease of comprehension and real-user error rates are not established by this study.

## B — Diagnose, request cancellation, review and export intent

Script: `tests/ui/design-system/components.spec.cjs`, test `internal study B`.

1. Open commands and verify initial search focus.
2. Reverse-Tab and forward-Tab across modal boundaries; Escape restores trigger focus. Reopen with Ctrl+K.
3. Search and choose an inspection command; observe only an explicit intent. Unsupported geometry commands are disabled.
4. Request cancellation; observe **acknowledgement pending**, not a false cancelled/completed state.
5. Expand a typed insufficient-evidence diagnostic and inspect missing physical-validation evidence/recovery guidance.
6. Acknowledge evidence review and record a local review intent; hardware certification remains false.
7. Open export review. Confirm remains disabled until the exploratory-mesh checkbox is selected; the result remains an STL intent with no file/result publication.

Result: all assertions pass. Related tests refuse stale/failed/missing-hash export, recover saved split panels and return from nested tree children to parents. This does not test cancellation during native compute, real authentication, durable signoff or actual export/reimport.

## Next research

P04/P12 should repeat these tasks against real state adapters, include VoiceOver/native desktop traversal, and collect participant completion/error observations before making usability or accessibility certification claims. No participant statistics or satisfaction scores were fabricated.
