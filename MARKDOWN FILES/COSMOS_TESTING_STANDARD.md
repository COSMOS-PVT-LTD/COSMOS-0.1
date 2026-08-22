# COSMOS TESTING STANDARD

Version: 1.0

Status: Approved

Parent Documents:

* COSMOS_MASTER_SPEC.md
* COSMOS_ARCHITECTURE_SPEC.md
* COSMOS_API_SPEC.md
* COSMOS_CODING_STANDARD.md
* COSMOS_DATABASE_SPEC.md
* COSMOS_GUI_SPEC.md

---

# 1. PURPOSE

This document defines:

* Testing philosophy
* Verification procedures
* Validation procedures
* Numerical accuracy requirements
* Coverage requirements
* Acceptance criteria

All COSMOS modules must comply with this document.

---

# 2. TESTING PHILOSOPHY

COSMOS follows:

```text
Verification
+
Validation
+
Regression
+
Automation
```

Verification asks:

```text
Did we build the software correctly?
```

Validation asks:

```text
Did we build the correct engineering model?
```

Both are mandatory.

---

# 3. TEST PYRAMID

```text
                Regression
                     ▲
                     │
            Integration Tests
                     ▲
                     │
                Unit Tests
```

Unit tests are most numerous.

Regression tests are most critical.

---

# 4. TEST DIRECTORY STRUCTURE

```text
tests/

├── unit_tests/
│
├── integration_tests/
│
├── regression_tests/
│
├── validation_tests/
│
├── benchmark_tests/
│
└── performance_tests/
```

---

# 5. TEST FRAMEWORK

Mandatory:

```text
pytest
```

Additional tools:

```text
pytest-cov
pytest-mock
hypothesis
```

---

# 6. UNIT TEST REQUIREMENTS

Every public module requires unit tests.

Example:

```text
physics/gas_dynamics/nozzle_1d.py
```

Must have:

```text
test_nozzle_1d.py
```

---

# 7. UNIT TEST OBJECTIVES

Verify:

* Correct outputs
* Correct exceptions
* Correct bounds checking
* Correct units
* Correct dataclasses

---

# 8. UNIT TEST COVERAGE

Minimum:

```text
Core        ≥ 95%
Physics     ≥ 90%
Systems     ≥ 90%
Backend     ≥ 85%
GUI         ≥ 70%
```

Target:

```text
Overall Coverage ≥ 90%
```

---

# 9. CORE TESTING

Must verify:

* Constants
* Units
* Validation
* Logging
* Configurations

Example:

```python
assert G0 == 9.80665
```

---

# 10. PHYSICS TESTING

Every equation must be tested.

Example:

Bartz correlation.

Verify:

* Known input
* Known output
* Numerical stability

Reference:

Published literature.

---

# 11. GAS DYNAMICS TESTING

Verify:

* Choked flow
* Area ratio
* Exit pressure
* Mach number

Against:

* Analytical solutions
* Textbook references

Tolerance:

```text
±0.1%
```

---

# 12. THERMOCHEMISTRY TESTING

Verify:

* Chamber temperature
* Gamma
* Molecular weight
* C*

Against:

NASA CEA.

Tolerance:

```text
±1%
```

---

# 13. FLUID PROPERTY TESTING

Verify:

* Density
* Viscosity
* Cp
* Conductivity

Against:

CoolProp references.

Tolerance:

```text
±0.5%
```

---

# 14. COMBUSTION TESTING

Verify:

* C*
* Efficiency
* Residence time

Against:

Published propulsion references.

Tolerance:

```text
±1%
```

---

# 15. HEAT TRANSFER TESTING

Verify:

* Bartz correlation
* Heat flux
* Recovery temperature

Against:

NASA publications.

Tolerance:

```text
±2%
```

---

# 16. MATERIAL TESTING

Verify:

* Density
* Yield strength
* Thermal conductivity

Against:

Database values.

Tolerance:

```text
Exact Match
```

---

# 17. SYSTEMS TESTING

Verify:

* Performance
* Geometry
* Injector
* Cooling
* Tanks
* Structure

Each subsystem shall have deterministic tests.

---

# 18. PERFORMANCE TESTING

Verify:

* Thrust
* Isp
* Exhaust velocity
* Mass flow

Against:

Hand calculations.

Tolerance:

```text
±1%
```

---

# 19. GEOMETRY TESTING

Verify:

* Chamber dimensions
* Throat dimensions
* Nozzle dimensions

Against:

Analytical calculations.

Tolerance:

```text
±0.1%
```

---

# 20. TANK TESTING

Verify:

* Tank volume
* Propellant capacity
* Pressurant sizing

Against:

Analytical calculations.

Tolerance:

```text
±1%
```

---

# 21. INJECTOR TESTING

Verify:

* Pressure drop
* Orifice sizing
* Momentum ratio

Tolerance:

```text
±1%
```

---

# 22. COOLING TESTING

Verify:

* Heat removal
* Wall temperature
* Pressure drop

Tolerance:

```text
±2%
```

---

# 23. STRUCTURE TESTING

Verify:

* Hoop stress
* Thermal stress
* Safety factor

Against:

Classical mechanics equations.

Tolerance:

```text
±1%
```

---

# 24. BACKEND TESTING

Verify:

* Dependency graph
* Solver execution order
* Convergence logic

Ensure:

```text
No circular dependencies
```

---

# 25. DATABASE TESTING

Verify:

* CRUD operations
* Data integrity
* Repository interfaces

Every repository requires tests.

---

# 26. GUI TESTING

Verify:

* Widget initialization
* Tab loading
* Signal handling
* Theme compatibility

GUI tests do not verify engineering calculations.

---

# 27. INTEGRATION TESTS

Purpose:

Verify subsystem interaction.

Example:

```text
Thermochemistry
↓
Performance
↓
Geometry
↓
Cooling
```

---

# 28. ENGINE INTEGRATION TEST

Input:

```text
Methane
LOX
5 kN
20 bar
```

Expected:

Valid EngineSolution

This becomes a baseline integration test.

---

# 29. MULTIPHYSICS TESTING

Verify:

```text
Combustion
↓
Gas Dynamics
↓
Heat Transfer
↓
Cooling
↓
Structure
```

Data must propagate correctly.

---

# 30. REGRESSION TESTING

Purpose:

Prevent future changes from breaking validated behavior.

Every bug fix requires:

```text
Regression Test
```

before merging.

---

# 31. VALIDATION TESTS

Purpose:

Compare against trusted references.

Sources:

* NASA CEA
* NASA SP documents
* Sutton
* Huzel & Huang
* Experimental data

---

# 32. VALIDATION DATABASE

Validation cases shall be stored in:

```text
validation.db
```

No hardcoded validation data.

---

# 33. CFD VALIDATION

Compare:

* Pressure fields
* Temperature fields
* Velocity fields

Against:

OpenFOAM
SU2
Published references

---

# 34. ACCEPTANCE CRITERIA

A solver is accepted when:

✓ Unit tests pass

✓ Integration tests pass

✓ Regression tests pass

✓ Validation tests pass

✓ Performance requirements met

---

# 35. CONVERGENCE TESTING

Iterative solvers must verify:

```text
Residual Reduction
Convergence Stability
Iteration Limits
```

Failure to converge shall raise:

```python
SolverConvergenceError
```

---

# 36. PROPERTY-BASED TESTING

Use:

```text
Hypothesis
```

Verify:

* Positive pressures
* Positive temperatures
* Positive mass flow

Across broad ranges.

---

# 37. PERFORMANCE BENCHMARKS

Target execution:

Performance Solver:

```text
< 1 sec
```

Cooling Solver:

```text
< 5 sec
```

Optimization:

```text
Parallelized
```

---

# 38. MEMORY TESTING

Verify:

* No memory leaks
* Stable large optimizations
* Stable CFD imports

---

# 39. NUMERICAL STABILITY TESTING

Verify:

* Extreme pressures
* Extreme temperatures
* Extreme O/F ratios

Solver must fail gracefully.

---

# 40. TEST DATA MANAGEMENT

Test datasets shall be:

* Version controlled
* Traceable
* Reproducible

Every dataset requires:

```text
Source
Version
Reference
```

---

# 41. CONTINUOUS INTEGRATION

Future requirement:

Every commit shall run:

```text
Unit Tests
Integration Tests
Regression Tests
```

Automatically.

---

# 42. DEFINITION OF VERIFIED

A module is VERIFIED when:

✓ Unit tests pass

✓ Coverage requirements met

✓ Numerical checks pass

---

# 43. DEFINITION OF VALIDATED

A module is VALIDATED when:

✓ Compared against reference data

✓ Meets tolerance limits

✓ Accepted by validation suite

---

# 44. DEFINITION OF RELEASE READY

A COSMOS release is approved only when:

✓ Architecture compliant

✓ API compliant

✓ Coding standard compliant

✓ Database compliant

✓ GUI compliant

✓ Testing compliant

✓ Validation suite passes

---

# 45. TEST COMPLIANCE CHECKLIST

Every generated module must answer:

□ Unit tested?

□ Integration tested?

□ Regression tested?

□ Validation data available?

□ Meets tolerance limits?

□ Uses SI units?

□ Architecture compliant?

□ API compliant?

□ Coverage target met?

□ Release ready?

END OF DOCUMENT
