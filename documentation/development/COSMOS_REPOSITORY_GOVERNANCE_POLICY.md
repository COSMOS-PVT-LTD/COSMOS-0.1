# COSMOS repository governance policy

Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

`main` integrates reviewed PRs with up-to-date successful GitHub Actions checks:
`Test (Python 3.11)`, `Test (Python 3.12)`, and `Lint and type check` (app ID 15368).
GUI regressions are blocking steps in both Python jobs. No force push, branch
deletion or merge commits; resolve conversations. Administrators are included.

Solo-developer policy: zero independent approvals are required by GitHub, and
last-pusher/code-owner independent approval is not mandatory. The verified owner
can self-review a PR, record acceptance and merge it after green checks. This
does not waive CONTRIBUTING.md's authorized human acceptance before merge.
Increase the independent-review threshold only when an active authorized team exists.

Emergency recovery is an explicit administrator **configuration change**, not an
automatic bypass: record incident/reason/current SHA and the exact temporary rule
diff, retain recoverable refs, never overwrite unknown work, then restore and
read back protection. Do not disable protections during routine integration.
No signing requirement is imposed when no signing key is configured.

Baseline tags are annotated, immutable by policy, never overwritten and only
created after checking current remote state and successful CI. Record SHA, date,
tag type, signature state and CI identity. Unsigned is not verified/signed.
The manual release workflow checks an existing annotated tag, main ancestry and
required checks. It creates neither a tag nor a release/deployment. Human review
and separate authorization are needed for publication/release. All claims remain
development-only, not production/flight/certification qualification.

Read current remote configuration before every mutation. The governance script
defaults to inspection and refuses to replace existing protection. Its apply
mode requires the expected current main SHA and admin access.

Keep LICENSE, NOTICE and the authoritative IP policies unchanged. Do not invent
a security contact; SECURITY.md's unresolved contact must be supplied by the
company. Never publish secret values or restricted reference datasets.

API basis: [GitHub branch protection documentation](https://docs.github.com/en/rest/branches/branch-protection).
