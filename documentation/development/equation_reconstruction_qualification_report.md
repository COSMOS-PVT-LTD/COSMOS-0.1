# Equation Reconstruction Qualification Report

**Document ID:** `COSMOS-KF-EQ-RECON-001`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-FOUNDATION-COMPLETION-2026-08-24`  
**Qualification state:** QUALIFIED FOR DEVELOPMENT  
**PRODUCTION-READY:** NO

## Source vs normalized

Source is preserved exactly. Example:

```text
SOURCE:       Re =rho* V* D/ mu
NORMALIZED:   Re = rho * V * D / mu
HYPOTHESIZED: Re = ρ * V * D / μ
```

The hypothesized Greek form is review-only. It does not replace the source span.

## AST

`knowledge.equations.ast.parse_equation` builds an expression tree for:

- `+ - * / ** ^`
- parentheses / nested groups
- juxtaposition treated as multiplication
- functions `sin cos log sqrt ...`
- identifiers including subscripts (`P_c`)

Parse failure is `EXTRACTION_UNAVAILABLE` for the reconstruction, not an invented tree.

## Equivalence states

`classify_equation_relation` returns:

`EQUIVALENT`, `DIFFERENT_APPLICABILITY`, `CONTRADICTORY`, `NOT_COMPARABLE`, `NOT_PROVEN`

Algebraic identities such as `a/b` vs `a*(1/b)` are **NOT_PROVEN**. They are not declared equivalent.

## Golden cases

| Source | Reconstruction |
|---|---|
| `Re = rho * V * D / mu` | DIV/MUL tree; LaTeX `\frac` |
| `Re = (rho * V * D) / mu` | grouped numerator |
| `Re =rho* V* D/ mu` | equivalent AST to the spaced form |
| `Re = rho * V * D * mu` | CONTRADICTORY vs the identity |
