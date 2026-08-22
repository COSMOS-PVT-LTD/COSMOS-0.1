# COSMOS CODING STANDARD


Version: 1.0

Status: Approved

Parent Documents:

* COSMOS_MASTER_SPEC.md
* COSMOS_ARCHITECTURE_SPEC.md
* COSMOS_API_SPEC.md

---

# 1. PURPOSE

This document defines the mandatory coding standards for all COSMOS source code.

Objectives:

* Consistency
* Maintainability
* Readability
* Testability
* Scalability
* Professional aerospace software quality

All generated source code must comply with this document.

---

# 2. OFFICIAL LANGUAGE

Primary Language:

Python

Required Version:

Python 3.13+

All code must be compatible with Python 3.13 or newer.

---

# 3. GENERAL PRINCIPLES

Every module must be:

* Modular
* Reusable
* Unit-testable
* Type-safe
* Documented
* Deterministic

Avoid:

* Hidden state
* Global variables
* Side effects
* Circular imports

---

# 4. FILE HEADER TEMPLATE

Every file shall begin with:

```python
"""
COSMOS Rocket Propulsion Platform

Module:
Author:
Version:
Purpose:

Description:
"""

from __future__ import annotations
```

All generated files shall use this header.

---

# 5. IMPORT ORDER

Imports shall always follow:

```python
# Standard Library

# Third Party

# COSMOS Core

# COSMOS Physics

# COSMOS Systems

# COSMOS Backend
```

Example:

```python
from pathlib import Path

import numpy as np

from core.constants import G0
from physics.gas_dynamics.nozzle_1d import nozzle_area_ratio
```

Never mix import groups.

---

# 6. TYPE HINTS

Mandatory.

Bad:

```python
def thrust(pc, at):
```

Good:

```python
def thrust(
    chamber_pressure: float,
    throat_area: float
) -> float:
```

All public functions require type hints.

---

# 7. DATACLASSES

Use dataclasses for structured data.

Required:

```python
from dataclasses import dataclass

@dataclass(slots=True)
class ChamberGeometry:
    diameter: float
    length: float
```

Preferred:

```python
@dataclass(slots=True, frozen=True)
```

when mutation is unnecessary.

---

# 8. FUNCTION DESIGN

Functions should:

* Do one thing
* Be deterministic
* Have clear inputs
* Have clear outputs

Avoid giant functions.

Target:

```text
20–60 lines
```

Maximum:

```text
150 lines
```

---

# 9. DOCSTRING STANDARD

Use NumPy Style.

Example:

```python
def calculate_thrust(
    chamber_pressure: float,
    throat_area: float
) -> float:
    """
    Calculate ideal thrust.

    Parameters
    ----------
    chamber_pressure : float
        Chamber pressure [Pa].

    throat_area : float
        Throat area [m²].

    Returns
    -------
    float
        Thrust [N].
    """
```

All public APIs require docstrings.

---

# 10. UNIT POLICY

All internal calculations:

SI Units Only

Required:

```text
Length          m
Mass            kg
Time            s
Pressure        Pa
Force           N
Temperature     K
Energy          J
```

Never mix:

```text
psi
bar
inches
feet
```

inside solver code.

Unit conversion belongs only in:

```text
core/units.py
```

---

# 11. CONSTANTS POLICY

Never hardcode constants.

Forbidden:

```python
g0 = 9.81
```

Required:

```python
from core.constants import G0
```

---

# 12. LOGGING POLICY

Never use:

```python
print()
```

Use:

```python
logger.debug()
logger.info()
logger.warning()
logger.error()
logger.critical()
```

All solver execution paths shall log.

---

# 13. EXCEPTION POLICY

Never silently ignore exceptions.

Forbidden:

```python
try:
    ...
except:
    pass
```

Required:

```python
try:
    ...
except ValueError as exc:
    raise InvalidInputError(
        "Invalid chamber pressure."
    ) from exc
```

---

# 14. CUSTOM EXCEPTIONS

All exceptions shall inherit from:

```python
CosmosError
```

Example:

```python
CosmosError

├── ValidationError
├── GeometryError
├── SolverError
├── DatabaseError
├── CFDError
└── GUIError
```

---

# 15. NUMERICAL METHODS

All numerical solvers must:

* Check convergence
* Check physical bounds
* Validate inputs
* Validate outputs

Example:

```python
if chamber_pressure <= 0:
    raise ValidationError(...)
```

---

# 16. ARRAY HANDLING

Use NumPy.

Preferred:

```python
numpy.ndarray
```

Avoid:

```python
Python lists
```

for heavy numerical work.

---

# 17. VECTORIZATION POLICY

Prefer:

```python
numpy operations
```

instead of:

```python
for loops
```

when practical.

---

# 18. CLASS DESIGN

Classes should encapsulate behavior.

Example:

```python
class NozzleSolver:
```

Not:

```python
class UtilityFunctions:
```

Avoid "God Classes".

---

# 19. SOLVER TEMPLATE

Every solver shall follow:

```python
class Solver:

    def solve(
        self,
        inputs
    ):
        ...
```

Inputs:

Dataclass

Outputs:

Dataclass

---

# 20. RESULT OBJECTS

Never return:

```python
tuple
dict
list
```

Use dataclasses.

Example:

```python
PerformanceResult
```

from API specification.

---

# 21. ENUMS

Use enums for fixed selections.

Example:

```python
class PropellantType(Enum):
    LOX = "LOX"
    METHANE = "METHANE"
```

Avoid string literals throughout code.

---

# 22. CONFIGURATION POLICY

Configuration belongs only in:

```text
core/config.py
```

Never scatter configuration variables.

---

# 23. DATABASE ACCESS

Database operations shall use repositories.

Example:

```python
MaterialRepository
PropellantRepository
```

GUI must never directly query SQLite.

---

# 24. GUI RULES

GUI shall:

* Display
* Collect input
* Trigger backend

GUI shall never:

* Run equations
* Contain engineering calculations

Forbidden:

```python
thrust = pc * at
```

inside GUI.

---

# 25. PLOTTING RULES

Plots belong only in:

```text
gui/plots
```

Physics modules shall never import plotting libraries.

---

# 26. THREADING RULES

Long-running tasks:

```text
Optimization
CFD
FEA
```

must execute in worker threads.

GUI shall remain responsive.

---

# 27. TESTING REQUIREMENTS

Every public module requires:

```python
test_<module>.py
```

Coverage target:

```text
≥ 90%
```

for Core and Physics.

---

# 28. FILE SIZE LIMITS

Function Target:
20–100 lines

Function Hard Limit:
200 lines

Module Preferred:
< 1000 lines

Module Review Threshold:
1000–1500 lines

Large Module Threshlod:
1500–2500 lines

Module Hard Limit:
4000 lines

Files exceeding 4000 lines shall be split unless a documented
engineering exception is approved.

Exceptions:
- GUI files
- Database schema definitions
- Material libraries
- CEA interfaces
- Generated code 

---

# 29. MODULE RESPONSIBILITY RULE

One module.

One responsibility.

Bad:

```text
cooling.py

+ heat transfer
+ GUI
+ export
```

Good:

Separate modules.

---

# 30. AI CODE GENERATION RULES

When generating COSMOS code:

Always:

1. Follow Master Spec.
2. Follow Architecture Spec.
3. Follow API Spec.
4. Follow Coding Standard.

Never:

1. Create placeholder code.
2. Use TODO stubs.
3. Use pass statements unless abstract.
4. Invent APIs outside specification.
5. Violate layer boundaries.

---

# 31. FILE GENERATION CHECKLIST

Before accepting a generated file:

□ Correct architecture layer

□ Correct imports

□ Uses type hints

□ Uses dataclasses

□ Uses logging

□ Uses custom exceptions

□ Uses SI units

□ Has tests

□ Uses API dataclasses

□ Follows naming convention

□ No circular imports

□ No print statements

□ No hidden state

---

# 32. DEFINITION OF DONE

A COSMOS module is complete only when:

1. Code compiles
2. Unit tests pass
3. Documentation exists
4. API compliant
5. Architecture compliant
6. Logging implemented
7. Exceptions implemented
8. Type hints complete
9. SI units verified
10. Peer review checklist passed

END OF DOCUMENT
