# COSMOS THERMOCHEMISTRY CACHE SPECIFICATION

Document ID: COSMOS-CACHE-001

Version: 1.0

Status: Approved Baseline

Parent Documents:

* COSMOS_MASTER_SPEC.md
* COSMOS_ARCHITECTURE_SPEC.md
* COSMOS_API_SPEC.md
* COSMOS_CODING_STANDARD.md
* COSMOS_TESTING_STANDARD.md

---

# 1. PURPOSE

This document defines the official requirements for:

physics/thermochemistry/cache.py

and

tests/unit_tests/test_cache.py

The cache subsystem shall provide deterministic, thread-safe, aerospace-grade caching services for all thermochemistry-related computations within COSMOS.

This module shall become the foundational caching layer for:

* RocketCEA integrations
* NASA CEA integrations
* Cantera integrations
* Equilibrium solvers
* Mixture solvers
* Optimization engines
* Parametric studies
* Monte Carlo analyses
* Future CFD integrations
* Future multiphysics coupling

---

# 2. DESIGN GOALS

The cache subsystem shall provide:

* Deterministic behavior
* Reproducible results
* Offline operation
* Thread safety
* O(1) memory lookups
* Disk persistence
* Expiration support
* Scientific auditability
* Future scalability

The cache subsystem shall never alter scientific results.

The cache subsystem shall only store and retrieve validated results.

---

# 3. ARCHITECTURE OVERVIEW

The cache subsystem consists of:

CacheEntry

CacheStatistics

MemoryCache

DiskCache

ThermochemistryCache

generate_cache_key()

get_global_cache()

All public interfaces shall remain stable.

---

# 4. EXCEPTION HIERARCHY

Required exceptions:

CacheError

CacheCorruptionError

CacheKeyError

CacheSerializationError

All cache exceptions shall inherit from Exception.

---

# 5. ENUMERATIONS

Required enumeration:

CacheSource

Allowed values:

MEMORY

DISK

ROCKETCEA

NASA_CEA

CANTERA

EQUILIBRIUM

MIXTURE

OPTIMIZATION

USER

The enum shall be used instead of raw strings.

---

# 6. CACHE ENTRY DATACLASS

Required dataclass:

CacheEntry

Implementation:

@dataclass(
frozen=True,
slots=True
)

Required fields:

key

created_at

expires_at

payload

source

metadata

schema_version

---

# 7. FIELD DEFINITIONS

## key

Unique cache identifier.

Type:

str

Must be SHA256 compatible.

---

## created_at

Creation timestamp.

Type:

datetime

Timezone-aware UTC.

---

## expires_at

Expiration timestamp.

Type:

datetime | None

None indicates no expiration.

---

## payload

Cached result object.

Type:

dict[str, Any]

Must be JSON serializable.

---

## source

Origin of cached data.

Type:

CacheSource

---

## metadata

Optional descriptive information.

Type:

dict[str, str]

Example:

{
"fuel": "CH4",
"oxidizer": "LOX",
"mr": "3.5"
}

---

## schema_version

Cache schema version.

Example:

"1.0.0"

Mandatory.

---

# 8. CACHE STATISTICS DATACLASS

Required dataclass:

CacheStatistics

Fields:

hits

misses

writes

evictions

memory_hits

disk_hits

expired_entries

corrupt_entries

Properties:

hit_rate

Formula:

hits / (hits + misses)

If denominator is zero:

Return 0.0

---

# 9. CACHE KEY GENERATION

Required function:

generate_cache_key()

Purpose:

Generate deterministic SHA256 cache keys.

Function shall support:

namespace

parameters

Required behavior:

* Stable
* Deterministic
* Order-independent

The following parameter orderings:

{
"fuel": "CH4",
"mr": 3.5
}

and

{
"mr": 3.5,
"fuel": "CH4"
}

must generate identical keys.

---

# 10. MEMORY CACHE

Required class:

MemoryCache

Backend:

dict[str, CacheEntry]

Complexity:

O(1)

Required methods:

get()

set()

exists()

remove()

clear()

size()

statistics()

---

# 11. THREAD SAFETY

MemoryCache shall use:

threading.RLock

All read/write operations shall be protected.

No race conditions permitted.

---

# 12. DISK CACHE

Required class:

DiskCache

Purpose:

Persistent cache storage.

---

# 13. DISK LAYOUT

Required structure:

cache/

rocketcea/

equilibrium/

mixtures/

optimization/

Each namespace shall store:

<sha256>.json

Example:

cache/rocketcea/7f84a3....json

---

# 14. DISK CACHE METHODS

Required:

save()

load()

delete()

exists()

clear()

size()

statistics()

---

# 15. JSON STORAGE FORMAT

Cache files shall contain:

key

created_at

expires_at

payload

source

metadata

schema_version

Storage format shall be human-readable JSON.

---

# 16. CORRUPTION HANDLING

Required exception:

CacheCorruptionError

Corruption examples:

* malformed JSON
* missing fields
* invalid timestamps
* invalid schema

Behavior:

Delete corrupt file

Record corruption event

Increment statistics

Log warning

Continue execution

Never crash COSMOS.

---

# 17. EXPIRATION POLICY

The cache shall support:

ttl_seconds

Example:

ttl_seconds=3600

Expiration shall be checked during:

get()

exists()

load()

Expired entries:

* invalid
* removed automatically
* counted as expired

---

# 18. PERMANENT ENTRIES

The cache shall support:

ttl_seconds=None

Meaning:

Never expires

Required for:

NASA CEA data

RocketCEA data

Static equilibrium solutions

---

# 19. THERMOCHEMISTRY CACHE MANAGER

Required class:

ThermochemistryCache

Purpose:

Unified cache interface.

---

# 20. SEARCH ORDER

Search hierarchy:

Memory Cache

↓

Disk Cache

↓

Cache Miss

If found on disk:

Promote to memory cache.

---

# 21. MANAGER METHODS

Required:

get()

set()

exists()

remove()

clear()

statistics()

cleanup_expired()

---

# 22. GLOBAL CACHE

Required function:

get_global_cache()

Behavior:

Lazy singleton.

The cache shall NOT initialize during module import.

Required for:

Testing

Dependency injection

Future multiprocessing

---

# 23. CONTEXT MANAGER SUPPORT

Required:

**enter**()

**exit**()

Example:

with ThermochemistryCache() as cache:

```
...
```

Future resource management shall not require redesign.

---

# 24. SERIALIZATION

Required:

CacheEntry.to_dict()

CacheEntry.from_dict()

CacheEntry.to_json()

CacheEntry.from_json()

Round-trip serialization shall preserve all values.

---

# 25. PERFORMANCE REQUIREMENTS

Memory lookup:

O(1)

Key generation:

O(n log n)

Initialization:

<100 ms

Memory overhead:

<10 MB

---

# 26. LOGGING REQUIREMENTS

The module shall integrate with:

core.logger

Events:

cache hit

cache miss

cache write

cache eviction

cache expiration

cache corruption

Debug logging shall be configurable.

---

# 27. SECURITY REQUIREMENTS

The cache subsystem shall never:

* execute code
* deserialize arbitrary objects
* load pickle files
* overwrite unrelated files

Only JSON storage permitted.

---

# 28. TESTING REQUIREMENTS

Target coverage:

95% minimum

98% preferred

---

# 29. REQUIRED TEST GROUPS

Part 1

CacheEntry

Part 2

CacheStatistics

Part 3

Cache Key Generation

Part 4

MemoryCache

Part 5

DiskCache

Part 6

ThermochemistryCache

Part 7

Expiration

Part 8

Serialization

Part 9

Corruption Handling

Part 10

Thread Safety

Part 11

Context Manager

Part 12

Global Cache Singleton

---

# 30. TEST COUNT TARGET

Expected:

70–100 tests

Approximate distribution:

CacheEntry:
10–15

Key Generation:
10–15

MemoryCache:
15–20

DiskCache:
20–25

Manager:
15–20

Expiration:
10–15

Thread Safety:
5–10

---

# 31. FUTURE COMPATIBILITY

The cache architecture shall support future integration with:

* RocketCEA
* NASA CEA
* Cantera
* CoolProp
* CFD preprocessors
* Distributed compute clusters
* Optimization engines
* HPC workflows

without breaking public APIs.

---

# 32. LONG-TERM OBJECTIVE

The COSMOS cache subsystem shall evolve into a deterministic scientific caching framework capable of supporting large-scale propulsion design studies, thermochemistry simulations, optimization campaigns, and multiphysics workflows while preserving reproducibility, auditability, and computational efficiency.
