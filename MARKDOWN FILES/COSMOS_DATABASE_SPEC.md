# COSMOS_DATABASE_SPEC.md

# COSMOS DATABASE SPECIFICATION

Version: 1.0

Status: Approved

Parent Documents:

* COSMOS_MASTER_SPEC.md
* COSMOS_ARCHITECTURE_SPEC.md
* COSMOS_API_SPEC.md
* COSMOS_CODING_STANDARD.md

---

# 1. PURPOSE

This document defines:

* Database architecture
* Database ownership
* Database schemas
* Repository patterns
* Data integrity rules
* Versioning strategy
* Future scalability

The database layer is responsible for storing engineering data.

The database layer is NOT responsible for:

* Solver logic
* Physics equations
* GUI logic
* Optimization algorithms

---

# 2. DATABASE PHILOSOPHY

COSMOS follows:

```text
Data
≠
Logic
```

Databases store information.

Solvers perform calculations.

GUI displays information.

These responsibilities must never mix.

---

# 3. DATABASE ARCHITECTURE

Version 1:

```text
SQLite
```

Local-first architecture.

Benefits:

* Lightweight
* Fast
* Offline operation
* Cross-platform

Supported:

* Windows
* Linux
* macOS
* Android
* iOS

---

# 4. DATABASE DIRECTORY STRUCTURE

```text
databases/

├── materials.db
├── propellants.db
├── injector_library.db
├── standards.db
├── validation.db
├── projects.db
└── optimization.db
```

---

# 5. DATABASE OWNERSHIP

materials.db

Owns:

* Metals
* Alloys
* Thermal properties
* Mechanical properties

---

propellants.db

Owns:

* Fuel properties
* Oxidizer properties
* Cryogenic properties

---

injector_library.db

Owns:

* Injector templates
* Injector geometries
* Design libraries

---

standards.db

Owns:

* NASA standards
* ASTM standards
* Material allowables
* Safety factors

---

validation.db

Owns:

* Experimental datasets
* Benchmark datasets
* Published references

---

projects.db

Owns:

* User projects
* Saved configurations
* Results history

---

optimization.db

Owns:

* Optimization runs
* Design studies
* Pareto fronts

---

# 6. DATABASE ACCESS RULE

Allowed:

```text
Backend
 ↓
Repository
 ↓
Database
```

Forbidden:

```text
GUI
 ↓
Database
```

GUI must never directly access SQLite.

---

# 7. REPOSITORY PATTERN

Every database shall have a repository.

Example:

```python
MaterialRepository
PropellantRepository
InjectorRepository
StandardsRepository
ProjectRepository
```

Repositories provide:

```python
create()
read()
update()
delete()
```

Operations.

No raw SQL outside repositories.

---

# 8. MATERIALS DATABASE

File:

```text
materials.db
```

Primary Table:

```sql
materials
```

Schema:

```text
id
name
family
density
elastic_modulus
yield_strength
ultimate_strength
thermal_conductivity
specific_heat
thermal_expansion
melting_temperature
source
version
```

Examples:

```text
OFHC Copper
GRCop-42
GRCop-84
GRCop-46
CuCrZr
Inconel 625
Inconel 718
316L
Ti-6Al-4V
```

---

# 9. PROPELLANTS DATABASE

File:

```text
propellants.db
```

Table:

```sql
propellants
```

Schema:

```text
id
name
type
temperature
density
viscosity
specific_heat
thermal_conductivity
molecular_weight
critical_temperature
critical_pressure
```

Examples:

```text
Methane
LOX
LH2
RP-1
Nitrogen
Helium
```

---

# 10. THERMOCHEMICAL DATA TABLE

Table:

```sql
cea_cache
```

Purpose:

Store previously computed CEA results.

Schema:

```text
id
fuel
oxidizer
mixture_ratio
chamber_pressure
temperature
gamma
molecular_weight
c_star
isp
```

Used by:

```text
physics/thermochemistry/cache.py
```

---

# 11. INJECTOR LIBRARY DATABASE

Table:

```sql
injectors
```

Schema:

```text
id
injector_type
fuel_orifice_count
oxidizer_orifice_count
orifice_diameter
pressure_drop
spray_angle
notes
```

Types:

```text
Doublet
Triplet
Swirl
Coaxial
Pintle
```

---

# 12. STANDARDS DATABASE

Table:

```sql
standards
```

Schema:

```text
id
standard_number
title
organization
revision
description
```

Organizations:

```text
NASA
ASTM
ISO
MIL
```

---

# 13. VALIDATION DATABASE

Purpose:

Benchmarking.

Table:

```sql
validation_cases
```

Schema:

```text
id
source
case_name
parameter
predicted_value
reference_value
percent_error
```

---

# 14. PROJECT DATABASE

File:

```text
projects.db
```

Table:

```sql
projects
```

Schema:

```text
id
project_name
author
creation_date
last_modified
description
```

---

Table:

```sql
engine_inputs
```

Stores:

```text
Thrust
Pc
O/F
Expansion Ratio
Fuel
Oxidizer
```

---

Table:

```sql
engine_results
```

Stores:

```text
Performance
Geometry
Cooling
Structure
Reliability
```

---

# 15. OPTIMIZATION DATABASE

Table:

```sql
optimization_runs
```

Schema:

```text
id
run_name
algorithm
start_time
end_time
best_objective
```

---

Table:

```sql
optimization_designs
```

Stores every design iteration.

---

# 16. DATABASE VERSIONING

Every database must contain:

```sql
schema_version
```

Table:

```text
version
date
notes
```

Required for future migrations.

---

# 17. ENGINEERING DATA QUALITY

Every engineering record shall contain:

```text
source
reference
version
last_verified
```

No anonymous data allowed.

---

# 18. MATERIAL PROPERTY TRACEABILITY

Example:

```text
Material:
GRCop-42

Source:
NASA

Reference:
NASA TM-2016-219145

Version:
1.0
```

Required for aerospace credibility.

---

# 19. UNIT STORAGE RULE

All values stored in databases shall use:

SI Units Only

Example:

Pressure:

```text
Pa
```

Not:

```text
bar
psi
```

Temperature:

```text
K
```

Not:

```text
°C
°F
```

---

# 20. DATABASE SECURITY

Project databases may be encrypted.

Recommended:

```text
AES-256
```

Future enterprise version.

---

# 21. BACKUP POLICY

User projects:

Automatic backup.

Recommended:

```text
Daily
```

Retention:

```text
30 Days
```

---

# 22. DATABASE TESTING

Each repository requires:

```python
test_material_repository.py
test_propellant_repository.py
test_project_repository.py
```

Coverage:

```text
90%+
```

---

# 23. FUTURE DATABASES

Future additions:

```text
trajectory.db
turbomachinery.db
telemetry.db
digital_twin.db
mission.db
```

Must follow repository pattern.

---

# 24. AI DATASETS

Future AI models shall use:

```text
optimization.db
validation.db
projects.db
```

as training and surrogate-model sources.

Raw user data must never be used without permission.

---

# 25. DATABASE COMPLIANCE CHECKLIST

Every database must satisfy:

□ SI Units

□ Repository Pattern

□ Version Controlled

□ Traceable Sources

□ Tested

□ Documented

□ No Solver Logic

□ No GUI Logic

□ API Compatible

□ Architecture Compliant

END OF DOCUMENT
