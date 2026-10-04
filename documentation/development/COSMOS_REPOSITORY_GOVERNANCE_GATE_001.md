# Repository governance gate 001

Date: 2026-10-04. Repository: COSMOS-PVT-LTD/COSMOS-0.1.

## Verified starting baseline

Main/local HEAD: `796ce4fa91c0086340cfab9602b35639285ad124`; fetch showed no divergence
and the starting worktree was clean. Hosted CI run
[37174114788](https://github.com/COSMOS-PVT-LTD/COSMOS-0.1/actions/runs/37174114788)
was successful on that SHA: both Python jobs 1,938 passed / 7 skipped, GUI 7
passed; Ruff/Mypy passed. Fresh Mac baseline: 1,939 passed / 6 skipped, GUI 7
passed, Ruff clean, Mypy clean across 168 files. The additional Linux skip is the
unprovisioned native-window test, not a suppressed numerical failure.

## Reconnaissance and target

Authenticated `trishul4kumar-ui` has verified admin permission. Protection was
absent (404), rulesets empty, CODEOWNERS invalid placeholder; no PR/issue/release
templates. Dependabot alerts enabled (204), security updates and secret scanning
disabled. No commit/tag signing configuration was found; no baseline tags existed.

Policy and exact initial protection payload are versioned. The sole developer
can use a green PR with zero independent reviewers; admin enforcement is enabled,
with documented break-glass configuration recovery. Existing legal/IP/architecture
documents are preserved. No scientific behavior changes in this increment.

## Evidence status

GOVERNANCE_REMOTE_ENFORCEMENT = VERIFIED by successful PUT followed by two GET readbacks.

Verified settings: strict/up-to-date three required checks pinned to GitHub Actions
app 15368; administrators enforced; PR threshold zero; independent code-owner/
last-pusher approvals false; linear history and conversation resolution true;
force push/deletion/branch lock false. Rulesets remain empty; classic protection
is the actual enforcement mechanism. No bypass mutation or destructive push was used.

Security settings were changed minimally and read back: secret scanning, secret
push protection and Dependabot security updates enabled. Dependabot alerts remain
enabled. Non-provider secret patterns/validity checks remain disabled; no claim
of exhaustive secret detection is made. No confidential alert content was fetched.

Baseline tag: `COSMOS-0.1-POST-REMEDIATION-001`, annotated **unsigned**, created
2026-10-04. Tag object `f383e956642aba03bb81ff4c372889f8120891b5` was read back
from origin and dereferences to `796ce4fa91c0086340cfab9602b35639285ad124`.
CI reference: 37174114788. Signing unavailable/unconfigured; no verified signature claim.

GitHub initially rejected a payload containing both `contexts` and `checks` (422).
The payload now uses only app-pinned `checks`; a regression rejects the ambiguity.
Governance regression tests: 2 passed; no Core/Physics source was changed.

Final result: **PASS — GOVERNANCE ENFORCED** for the read-back remote settings
and locally tested proposed governance files. This is not human PR acceptance.
Optional pre-commit dependency was not introduced: authoritative CI remains the
mandatory gate. SECURITY.md's company contact remains unresolved rather than invented.

Local governance files and templates are proposed on
`codex/numerics-foundation-001`; they reach main only through owner-approved PR integration.
