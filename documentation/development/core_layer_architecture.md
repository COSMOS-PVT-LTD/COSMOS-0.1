# Core Layer Architecture — COSMOS 0.1

**Rule:** Core is the lower computational foundation and **must remain independently importable without Physics**.

## Dependency direction

```text
physics  ──►  core
core       ──X  physics   (forbidden)
```

Physics may import generic Core primitives (`validate_positive`, `Quantity`, etc.). Core must not import any `physics.*` module — including lazy, local, or dynamic imports.

## Deprecated propulsion validators

`core.validation.validate_mixture_ratio` and `validate_expansion_ratio` remain for backward compatibility. They are self-contained wrappers around `validate_positive` and do **not** delegate to Physics.

New propulsion-domain code should prefer:

```python
from physics.propulsion_validation import validate_mixture_ratio
```

## Verification

Architecture acceptance tests live in:

`tests/unit_tests/core/test_core_layer_independence.py`

These tests inspect `sys.modules` after import and scan Core source with AST analysis to detect forbidden Physics dependencies.
