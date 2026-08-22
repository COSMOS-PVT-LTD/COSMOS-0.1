# Contributing to COSMOS

COSMOS is proprietary software owned by **COSMOS PVT LTD**. It is **not** an
unrestricted open-source contribution project.

Public repository visibility does not grant the public permission to contribute
or use COSMOS without explicit authorization.

## Authorized Contribution

Contributions are accepted only from individuals authorized by COSMOS PVT LTD,
including employees, contractors, consultants, and partners operating under
applicable company agreements and policies.

Unauthorized submissions may be rejected without review.

## Contributor Agreements

Contributions are subject to COSMOS PVT LTD's applicable employment agreements,
contractor agreements, confidentiality agreements, intellectual property
assignment agreements, and contributor policies.

If a formal contributor agreement has not yet been issued for a specific
engagement, contribution rights remain governed by the applicable COSMOS PVT LTD
agreements and company policy in effect for that contributor.

## Coding Standards

Follow existing project conventions and the specifications in:

- `MARKDOWN FILES/COSMOS_CODING_STANDARD.md`
- `documentation/COSMOS_0.1_FREEZED.md` (architecture — do not redesign)

Match naming, structure, typing, and documentation patterns used in adjacent
modules.

## Testing Requirements

- Add or update tests for behavior changes.
- Run the test suite before submitting changes.
- Do not reduce test coverage without documented justification.

Current test entry point:

```bash
python -m pytest
```

## Documentation Requirements

- Update relevant documentation when behavior, architecture boundaries, or
  governance-relevant workflows change.
- Distinguish **IMPLEMENTED**, **PARTIALLY IMPLEMENTED**, **PLANNED**, and
  **FUTURE** capabilities in user-facing documentation.
- Do not claim unimplemented functionality exists.

## Review Requirements

All changes require review and approval by authorized COSMOS PVT LTD personnel
before merge, in accordance with company development policy.

## Security Requirements

- Never commit secrets, credentials, or confidential information.
- Follow `SECURITY.md` and `documentation/PUBLIC_REPOSITORY_IP_POLICY.md`.
- Report security issues through the process in `SECURITY.md`.

## Dependency Licensing Requirements

- Preserve third-party license terms.
- Do not replace third-party licenses with the COSMOS proprietary license.
- Document new dependencies and verify license compatibility before merge.
- Do not introduce copyleft licenses into core proprietary modules without
  explicit company approval.

## Intellectual Property Requirements

- Original work contributed to COSMOS is intended for inclusion in the COSMOS PVT
  LTD proprietary software portfolio, subject to applicable agreements.
- Do not submit third-party proprietary code without rights and approval.
- Do not submit code copied from restricted or unknown-license sources.

## Confidentiality Requirements

Contributors must not disclose confidential company information through public
issues, pull requests, commit messages, or repository files.

## Prohibited Submissions

Do not submit:

- secrets or credentials
- confidential customer or supplier information
- proprietary datasets not approved for public repository inclusion
- export-controlled or restricted technical information without approval
- malicious code
- unrelated third-party projects
- architectural redesigns that conflict with the frozen COSMOS 0.1 architecture

## Process

1. Obtain authorization to contribute.
2. Create a branch from the current default branch.
3. Implement focused changes with tests and documentation.
4. Open a pull request with a clear description.
5. Address review feedback.
6. Merge only after authorized approval.

## Questions

Direct contribution and access questions to authorized COSMOS PVT LTD engineering
or management contacts.

Copyright © 2026 COSMOS PVT LTD. All Rights Reserved.
