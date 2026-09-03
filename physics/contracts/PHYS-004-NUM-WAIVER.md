# PHYS-004-NUM-001 — Formal Waiver

**Finding:** Temporary bisection fallback in `physics/contracts/numerics_port.py`  
**Severity:** S2  
**Status:** FORMALLY APPROVED WAIVER for COSMOS 0.1 foundation freeze (PATH A)  
**Date:** 2026-09-01  
**Approval date:** 2026-09-03  
**Owner:** physics/contracts

## Reason not fixed

The `numerics/` package is not yet present in COSMOS 0.1. Inverse Mach,
Prandtl–Meyer, and oblique-shock solvers require a bracketed scalar root
finder. A minimal fallback keeps physics closed-form modules testable without
introducing a partial numerical library during CORE/PHYS remediation.

## Current behavior

`physics.contracts.numerics_port._fallback_bisection` provides bracketed
bisection with explicit `SolverConvergenceError` when no sign change exists.

## Declared capability

Closed-form compressible-flow identities plus bounded inverse solves using
the documented temporary port only.

## Risk

Numerical behavior differs from the future canonical `numerics/` implementation
(tolerance, bracket expansion, logging). Physics inverse results may change
when Numerics lands.

## Mitigation

- Port is isolated behind `numerics_port.py`.
- Documented in `NUM-CONTRACT-ISSUE.md`.
- Anderson γ=1.4, M=2 benchmarks validate closed-form paths independently.

## Scope limitation

Applies only to scalar inverse solves in PHYS-004. Not a general root-finding
framework.

## Removal condition

Delete fallback when `numerics/root_finding.py` (or equivalent) is merged and
physics imports the canonical implementation.

## Approved by

Name: TK NAYAK  
Role: CEO, CTO, Chief propulsion scientist  
Date: 2026-09-03  
Decision: APPROVED for COSMOS 0.1 PATH A (temporary bounded bisection)  
Notes: Capability limited to documented PHYS-004 inverse paths only. Not a general Numerics framework.
