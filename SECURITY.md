# Security Policy

COSMOS is proprietary software owned by **COSMOS PVT LTD**. This repository is
publicly visible for development purposes. Security practices apply to all
contributors and authorized users.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability affecting COSMOS, report it through
responsible disclosure.

**Security contact:** `[SECURITY CONTACT]` *(placeholder — replace with the
official COSMOS PVT LTD security contact when established)*

When reporting, include:

- description of the issue
- affected component or file path
- steps to reproduce
- potential impact
- any proof-of-concept material (if applicable)

Do **not** post confidential information, credentials, exploit details, or
customer data in public GitHub issues.

COSMOS PVT LTD will acknowledge receipt and coordinate investigation through
authorized channels.

## Responsible Disclosure

- Do not publicly disclose vulnerabilities before COSMOS PVT LTD has had a
  reasonable opportunity to investigate and remediate.
- Do not access, modify, or exfiltrate data beyond what is necessary to
  demonstrate the issue.
- Do not perform destructive testing against production systems without written
  authorization.

## Secret and Credential Management

Never commit to this repository:

- passwords
- API keys
- authentication tokens
- private keys
- certificates
- cloud credentials
- database credentials
- service-account files

Use local environment files excluded by `.gitignore` and company-approved
secret-management systems.

## Dependency Security

Third-party dependencies must be reviewed for license compatibility and security
risk before introduction. Maintain awareness of known vulnerabilities in
dependencies used by COSMOS.

## Security-Sensitive Changes

Changes affecting authentication, authorization, cryptography, secret handling,
network exposure, or data protection require additional security review before
merge.

## Prohibited Public Disclosures

Do not use public GitHub issues, pull requests, or discussions to post:

- confidential engineering data
- proprietary datasets
- internal credentials
- unpublished inventions
- trade-secret information
- customer or supplier confidential information

## Legal Notice

This document describes project security practices. It is not legal advice.

Copyright © 2026 COSMOS PVT LTD. All Rights Reserved.
