# Public Repository IP Policy

**COSMOS PVT LTD — COSMOS 0.1**

Copyright © 2026 COSMOS PVT LTD. All Rights Reserved.

## Purpose

This policy defines what COSMOS PVT LTD permits in the public COSMOS-0.1
repository and what must remain private or require explicit approval before
public inclusion.

Public repository visibility is for development convenience, collaboration,
source control, issue tracking, CI/CD development, version control, and
appropriate technical transparency. It does **not** constitute an open-source
license.

## Company Ownership

All original COSMOS source code, algorithms, engineering models, computational
methods, software architecture, documentation, databases, AI/ML implementations,
optimization methods, engineering workflows, internal tooling, and other original
technical material committed to this repository remain proprietary intellectual
property of COSMOS PVT LTD, subject to applicable third-party rights and
licenses.

## Permitted in the Public Repository

Subject to review and approval workflows, the public repository may contain:

- proprietary COSMOS source code authorized for public visibility
- architecture and engineering documentation approved for publication
- automated tests and test fixtures approved for publication
- non-sensitive engineering reference data approved for publication
- CI/CD configuration for development and quality assurance
- governance and security documentation

## Prohibited Without Explicit Approval

The following must **not** be committed to the public repository unless
explicitly approved by COSMOS PVT LTD:

- passwords
- API keys
- authentication tokens
- private keys
- certificates
- cloud credentials
- database credentials
- service-account credentials
- confidential customer information
- confidential supplier information
- proprietary datasets
- private AI training datasets
- proprietary model weights
- sensitive engineering test data
- unpublished experimental results
- unpublished inventions
- patent-sensitive information
- trade-secret information
- proprietary engineering databases
- confidential business information
- internal financial information
- security-sensitive infrastructure information
- restricted technical information
- legally protected third-party information
- export-controlled information where applicable

COSMOS PVT LTD does not make unsupported claims about export-control
classification in this document.

## Third-Party Material

Third-party software, libraries, datasets, models, and dependencies remain
subject to their respective licenses and ownership rights. COSMOS PVT LTD does
not claim ownership of third-party software.

Required third-party notices and license terms must be preserved.

## Contributor Responsibilities

Contributors must:

- review changes for accidental secret or confidential disclosure
- follow `SECURITY.md` and `CONTRIBUTING.md`
- escalate uncertain IP or confidentiality questions before commit
- use `.gitignore` and company-approved secret-management practices

## Incident Response

If confidential or sensitive material is committed:

1. Stop further public disclosure where possible.
2. Notify authorized COSMOS PVT LTD management and engineering leadership.
3. Rotate exposed credentials immediately.
4. Follow company incident-response procedures.
5. Remediate repository history only through approved processes.

## Legal Review

This policy is a project governance document and is not legal advice. Final
legal instruments and publication decisions are subject to review by qualified
legal counsel for COSMOS PVT LTD.
