# COSMOS 0.1 — Future Mathematics / Physics Upgrade Policy

**Document ID:** `CORE-PHYSICS-FUTURE-UPGRADE-POLICY-001`  
**Date:** 2026-09-03  
**Applies to:** Changes after Core + Physics frozen baseline  

---

## Principle

```text
Freeze the baseline, not the future.
```

The COSMOS_0.1 Core + Physics foundation is a trusted reference. Future improvements in mathematics, physics, numerical methods, correlations, property models, thermochemistry, constitutive laws, and multiphysics coupling are expected — but must enter as **controlled, versioned extensions**.

---

## Required workflow

```text
PROPOSE → ARCHITECTURE REVIEW → MODEL DEFINITION → IMPLEMENT
  → UNIT TEST → VERIFICATION → VALIDATION (where data exist)
  → REGRESSION → INDEPENDENT REVIEW → COMPATIBILITY REVIEW
  → MODEL VERSION / RELEASE → OPTIONAL DEFAULT PROMOTION
```

A new model must **earn** promotion to default. Silent replacement of accepted numerical behavior is forbidden.

---

## Model record (minimum)

For each significant engineering model, capture as applicable:

- Identity (name, id, version, domain, application)
- Equations / constitutive relations / correlations / numerical method
- Assumptions and simplifications
- Validity domain
- Provenance (literature, dataset, implementation, date, commit)
- Verification evidence
- Validation evidence **or** explicit `NOT VALIDATED`
- Compatibility statement vs frozen baseline

Never call a model **validated** when only verification has been performed.

---

## Layering (non-negotiable)

```text
physics → core
core ─X→ physics
```

Do not introduce Core → Physics imports (including lazy/dynamic). Do not put Physics equations in GUI presentation code.

---

## PHYS-004 Numerics evolution

PATH A temporary bisection remains until:

1. Canonical `numerics/root_finding/bisection` is implemented  
2. Behavior is verified against the frozen baseline  
3. Intentional differences are quantified  
4. `numerics_port` migrates to Numerics  
5. Fallback is removed  
6. Waiver is updated/closed  
7. Independent review is performed  

Do not scatter root finders through Physics.

---

## Agent rules after freeze

1. Read the frozen baseline documents before changing Core/Physics.  
2. Inspect current source before modifying it.  
3. Preserve dimensional safety and typed failures.  
4. Never silently change accepted numerical behavior.  
5. Never remove an old model solely because a new one exists.  
6. Add tests with every material change.  
7. State what was verified, validated, and not validated.  
8. Never claim certification/equivalence without evidence.  
9. Do not declare freeze authority as an agent.

---

**Policy committed for COSMOS_0.1 controlled evolution.**
