"""
COSMOS Rocket Propulsion Platform

Unit Tests:
    physics.thermochemistry.cache
"""

from __future__ import annotations

# ============================================================================
# Standard Library
# ============================================================================

from datetime import UTC
from datetime import datetime
from physics.thermochemistry.cache import (
    MemoryCache,
)
from pathlib import Path
from tempfile import TemporaryDirectory

from physics.thermochemistry.cache import (
    DiskCache,
)
from physics.thermochemistry.cache import (
    ThermochemistryCache,
    get_global_cache,
    reset_global_cache,
)
from datetime import timedelta

from physics.thermochemistry.cache import (
    cache_entry_is_expired,
)

import pytest  # type: ignore

import json

from physics.thermochemistry.cache import (
    _cache_entry_from_dict,
    _cache_entry_to_dict,
    cache_entry_from_json,
    cache_entry_to_json,
)
from concurrent.futures import ThreadPoolExecutor

# ============================================================================
# Module Under Test
# ============================================================================

from physics.thermochemistry.cache import (
    CACHE_SCHEMA_VERSION,
    CacheCorruptionError,
    CacheEntry,
    CacheError,
    CacheKeyError,
    CacheSerializationError,
    CacheSource,
    CacheStatistics,
)

# ============================================================================
# Helpers
# ============================================================================


def create_cache_entry() -> CacheEntry:
    """
    Create valid cache entry.
    """

    return CacheEntry(
        key="test_key",
        created_at=datetime.now(
            tz=UTC,
        ),
        expires_at=None,
        payload={
            "value": 42,
        },
        source=CacheSource.USER,
        metadata={
            "fuel": "CH4",
        },
        schema_version=(
            CACHE_SCHEMA_VERSION
        ),
    )

# ============================================================================
# CacheSource Tests
# ============================================================================


def test_cache_source_memory() -> None:

    assert (
        CacheSource.MEMORY.value
        == "MEMORY"
    )


def test_cache_source_disk() -> None:

    assert (
        CacheSource.DISK.value
        == "DISK"
    )


def test_cache_source_rocketcea() -> None:

    assert (
        CacheSource.ROCKETCEA.value
        == "ROCKETCEA"
    )


def test_cache_source_nasa_cea() -> None:

    assert (
        CacheSource.NASA_CEA.value
        == "NASA_CEA"
    )


def test_cache_source_cantera() -> None:

    assert (
        CacheSource.CANTERA.value
        == "CANTERA"
    )


def test_cache_source_equilibrium() -> None:

    assert (
        CacheSource.EQUILIBRIUM.value
        == "EQUILIBRIUM"
    )


def test_cache_source_mixture() -> None:

    assert (
        CacheSource.MIXTURE.value
        == "MIXTURE"
    )


def test_cache_source_optimization() -> None:

    assert (
        CacheSource.OPTIMIZATION.value
        == "OPTIMIZATION"
    )


def test_cache_source_user() -> None:

    assert (
        CacheSource.USER.value
        == "USER"
    )

# ============================================================================
# Exception Tests
# ============================================================================


def test_cache_error() -> None:

    assert issubclass(
        CacheError,
        Exception,
    )


def test_cache_corruption_error() -> None:

    assert issubclass(
        CacheCorruptionError,
        CacheError,
    )


def test_cache_key_error() -> None:

    assert issubclass(
        CacheKeyError,
        CacheError,
    )


def test_cache_serialization_error() -> None:

    assert issubclass(
        CacheSerializationError,
        CacheError,
    )

# ============================================================================
# CacheEntry Tests
# ============================================================================


def test_create_cache_entry() -> None:

    entry = (
        create_cache_entry()
    )

    assert (
        entry.key
        == "test_key"
    )


def test_cache_entry_source() -> None:

    entry = (
        create_cache_entry()
    )

    assert (
        entry.source
        is CacheSource.USER
    )


def test_cache_entry_payload() -> None:

    entry = (
        create_cache_entry()
    )

    assert (
        entry.payload[
            "value"
        ]
        == 42
    )


def test_cache_entry_metadata() -> None:

    entry = (
        create_cache_entry()
    )

    assert (
        entry.metadata[
            "fuel"
        ]
        == "CH4"
    )


def test_empty_key_fails() -> None:

    with pytest.raises(
        CacheKeyError
    ):

        CacheEntry(
            key="",
            created_at=datetime.now(
                tz=UTC,
            ),
            expires_at=None,
            payload={},
            source=CacheSource.USER,
            metadata={},
        )


def test_invalid_source_fails() -> None:

    with pytest.raises(
        CacheSerializationError
    ):

        CacheEntry(
            key="x",
            created_at=datetime.now(
                tz=UTC,
            ),
            expires_at=None,
            payload={},
            source="INVALID",  # type: ignore
            metadata={},
        )

# ============================================================================
# CacheStatistics Tests
# ============================================================================


def test_statistics_defaults() -> None:

    stats = CacheStatistics()

    assert stats.hits == 0

    assert stats.misses == 0

    assert stats.writes == 0

    assert stats.evictions == 0


def test_hit_rate_zero() -> None:

    stats = CacheStatistics()

    assert (
        stats.hit_rate
        == 0.0
    )


def test_hit_rate_nonzero() -> None:

    stats = CacheStatistics(
        hits=8,
        misses=2,
    )

    assert (
        stats.hit_rate
        == 0.8
    )
# ============================================================================
# Additional Imports (Part 2)
# ============================================================================

from physics.thermochemistry.cache import (
    generate_cache_key,
)

# ============================================================================
# Cache Key Generation Tests
# ============================================================================


def test_generate_cache_key_returns_string() -> None:

    key = generate_cache_key(
        namespace="cea",
        parameters={
            "fuel": "CH4",
            "oxidizer": "LOX",
        },
    )

    assert isinstance(
        key,
        str,
    )


def test_generate_cache_key_length() -> None:

    key = generate_cache_key(
        namespace="cea",
        parameters={
            "fuel": "CH4",
        },
    )

    assert len(key) == 64


def test_generate_cache_key_is_deterministic() -> None:

    params = {
        "fuel": "CH4",
        "oxidizer": "LOX",
        "mr": 3.5,
    }

    key1 = generate_cache_key(
        namespace="cea",
        parameters=params,
    )

    key2 = generate_cache_key(
        namespace="cea",
        parameters=params,
    )

    assert key1 == key2


def test_generate_cache_key_order_independent() -> None:

    params_a = {
        "fuel": "CH4",
        "oxidizer": "LOX",
        "mr": 3.5,
    }

    params_b = {
        "mr": 3.5,
        "oxidizer": "LOX",
        "fuel": "CH4",
    }

    key_a = generate_cache_key(
        namespace="cea",
        parameters=params_a,
    )

    key_b = generate_cache_key(
        namespace="cea",
        parameters=params_b,
    )

    assert key_a == key_b


def test_generate_cache_key_different_namespace() -> None:

    params = {
        "fuel": "CH4",
    }

    key_a = generate_cache_key(
        namespace="cea",
        parameters=params,
    )

    key_b = generate_cache_key(
        namespace="equilibrium",
        parameters=params,
    )

    assert key_a != key_b


def test_generate_cache_key_different_parameters() -> None:

    key_a = generate_cache_key(
        namespace="cea",
        parameters={
            "mr": 3.0,
        },
    )

    key_b = generate_cache_key(
        namespace="cea",
        parameters={
            "mr": 3.5,
        },
    )

    assert key_a != key_b


def test_generate_cache_key_different_fuel() -> None:

    key_a = generate_cache_key(
        namespace="cea",
        parameters={
            "fuel": "CH4",
        },
    )

    key_b = generate_cache_key(
        namespace="cea",
        parameters={
            "fuel": "RP1",
        },
    )

    assert key_a != key_b


def test_generate_cache_key_different_oxidizer() -> None:

    key_a = generate_cache_key(
        namespace="cea",
        parameters={
            "oxidizer": "LOX",
        },
    )

    key_b = generate_cache_key(
        namespace="cea",
        parameters={
            "oxidizer": "N2O4",
        },
    )

    assert key_a != key_b


def test_generate_cache_key_empty_parameters() -> None:

    key = generate_cache_key(
        namespace="cea",
        parameters={},
    )

    assert isinstance(
        key,
        str,
    )

    assert len(key) == 64


def test_generate_cache_key_empty_namespace_fails() -> None:

    with pytest.raises(
        CacheKeyError
    ):

        generate_cache_key(
            namespace="",
            parameters={},
        )


def test_generate_cache_key_whitespace_namespace() -> None:

    key = generate_cache_key(
        namespace="   ",
        parameters={
            "x": 1,
        },
    )

    assert isinstance(
        key,
        str,
    )


def test_generate_cache_key_large_parameter_set() -> None:

    params = {
        f"parameter_{i}": i
        for i in range(
            100
        )
    }

    key = generate_cache_key(
        namespace="large",
        parameters=params,
    )

    assert len(key) == 64


def test_generate_cache_key_nested_dictionary() -> None:

    params = {
        "conditions": {
            "pc": 20.0,
            "mr": 3.5,
        }
    }

    key = generate_cache_key(
        namespace="cea",
        parameters=params,
    )

    assert len(key) == 64


def test_generate_cache_key_list_parameter() -> None:

    params = {
        "species": [
            "CO2",
            "H2O",
        ]
    }

    key = generate_cache_key(
        namespace="equilibrium",
        parameters=params,
    )

    assert len(key) == 64


def test_generate_cache_key_repeatability_many_calls() -> None:

    params = {
        "fuel": "CH4",
        "pc": 20.0,
    }

    reference = (
        generate_cache_key(
            namespace="cea",
            parameters=params,
        )
    )

    for _ in range(50):

        current = (
            generate_cache_key(
                namespace="cea",
                parameters=params,
            )
        )

        assert (
            current
            == reference
        )


def test_generate_cache_key_case_sensitive() -> None:

    key_a = generate_cache_key(
        namespace="CEA",
        parameters={
            "fuel": "CH4",
        },
    )

    key_b = generate_cache_key(
        namespace="cea",
        parameters={
            "fuel": "CH4",
        },
    )

    assert key_a != key_b


def test_generate_cache_key_unique_set() -> None:

    keys = set()

    for index in range(
        100
    ):

        key = (
            generate_cache_key(
                namespace="cea",
                parameters={
                    "run": index,
                },
            )
        )

        keys.add(key)

    assert len(keys) == 100
# ============================================================================
# MemoryCache Helpers
# ============================================================================


def create_memory_cache() -> MemoryCache:

    return MemoryCache()
# ============================================================================
# MemoryCache Tests
# ============================================================================


def test_memory_cache_initially_empty() -> None:

    cache = create_memory_cache()

    assert cache.size() == 0


def test_memory_cache_set() -> None:

    cache = create_memory_cache()

    entry = create_cache_entry()

    cache.set(entry)

    assert cache.size() == 1


def test_memory_cache_get() -> None:

    cache = create_memory_cache()

    entry = create_cache_entry()

    cache.set(entry)

    result = cache.get(
        entry.key
    )

    assert result is not None

    assert result.key == entry.key


def test_memory_cache_get_missing() -> None:

    cache = create_memory_cache()

    result = cache.get(
        "missing"
    )

    assert result is None


def test_memory_cache_exists_true() -> None:

    cache = create_memory_cache()

    entry = create_cache_entry()

    cache.set(entry)

    assert cache.exists(
        entry.key
    )


def test_memory_cache_exists_false() -> None:

    cache = create_memory_cache()

    assert not cache.exists(
        "missing"
    )


def test_memory_cache_remove() -> None:

    cache = create_memory_cache()

    entry = create_cache_entry()

    cache.set(entry)

    assert cache.remove(
        entry.key
    )

    assert cache.size() == 0


def test_memory_cache_remove_missing() -> None:

    cache = create_memory_cache()

    assert (
        cache.remove(
            "missing"
        )
        is False
    )


def test_memory_cache_clear() -> None:

    cache = create_memory_cache()

    cache.set(
        create_cache_entry()
    )

    cache.clear()

    assert cache.size() == 0


def test_memory_cache_multiple_entries() -> None:

    cache = create_memory_cache()

    for i in range(10):

        cache.set(
            CacheEntry(
                key=f"k{i}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "i": i
                },
                source=CacheSource.USER,
                metadata={},
            )
        )

    assert cache.size() == 10


def test_memory_cache_keys() -> None:

    cache = create_memory_cache()

    cache.set(
        create_cache_entry()
    )

    keys = cache.keys()

    assert "test_key" in keys


def test_memory_cache_keys_empty() -> None:

    cache = create_memory_cache()

    assert cache.keys() == ()


def test_memory_cache_snapshot() -> None:

    cache = create_memory_cache()

    cache.set(
        create_cache_entry()
    )

    snapshot = (
        cache.snapshot()
    )

    assert isinstance(
        snapshot,
        dict,
    )

    assert (
        "test_key"
        in snapshot
    )


def test_memory_cache_snapshot_copy() -> None:

    cache = create_memory_cache()

    cache.set(
        create_cache_entry()
    )

    snapshot = (
        cache.snapshot()
    )

    snapshot.clear()

    assert cache.size() == 1


def test_memory_cache_statistics_object() -> None:

    cache = create_memory_cache()

    stats = (
        cache.statistics()
    )

    assert isinstance(
        stats,
        CacheStatistics,
    )


def test_memory_cache_hit_statistics() -> None:

    cache = create_memory_cache()

    entry = create_cache_entry()

    cache.set(entry)

    cache.get(
        entry.key
    )

    stats = (
        cache.statistics()
    )

    assert stats.hits == 1


def test_memory_cache_miss_statistics() -> None:

    cache = create_memory_cache()

    cache.get(
        "missing"
    )

    stats = (
        cache.statistics()
    )

    assert stats.misses == 1


def test_memory_cache_write_statistics() -> None:

    cache = create_memory_cache()

    cache.set(
        create_cache_entry()
    )

    stats = (
        cache.statistics()
    )

    assert stats.writes == 1


def test_memory_cache_eviction_statistics() -> None:

    cache = create_memory_cache()

    entry = create_cache_entry()

    cache.set(entry)

    cache.remove(
        entry.key
    )

    stats = (
        cache.statistics()
    )

    assert (
        stats.evictions
        == 1
    )


def test_memory_cache_replace_existing_key() -> None:

    cache = create_memory_cache()

    entry_a = (
        create_cache_entry()
    )

    entry_b = CacheEntry(
        key="test_key",
        created_at=datetime.now(
            tz=UTC
        ),
        expires_at=None,
        payload={
            "value": 99
        },
        source=CacheSource.USER,
        metadata={},
    )

    cache.set(entry_a)

    cache.set(entry_b)

    result = cache.get(
        "test_key"
    )

    assert result is not None

    assert (
        result.payload[
            "value"
        ]
        == 99
    )


def test_memory_cache_size_after_replace() -> None:

    cache = create_memory_cache()

    entry_a = (
        create_cache_entry()
    )

    entry_b = CacheEntry(
        key="test_key",
        created_at=datetime.now(
            tz=UTC
        ),
        expires_at=None,
        payload={
            "new": True
        },
        source=CacheSource.USER,
        metadata={},
    )

    cache.set(entry_a)

    cache.set(entry_b)

    assert cache.size() == 1


def test_memory_cache_many_entries() -> None:

    cache = create_memory_cache()

    for i in range(100):

        cache.set(
            CacheEntry(
                key=f"entry_{i}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "index": i
                },
                source=CacheSource.USER,
                metadata={},
            )
        )

    assert cache.size() == 100


# ============================================================================
# DiskCache Helpers
# ============================================================================


def create_disk_cache() -> DiskCache:

    temp_dir = TemporaryDirectory()

    cache = DiskCache(
        Path(
            temp_dir.name
        )
    )

    # assign backing TemporaryDirectory to cache instance (bypass readonly/type checks)
    object.__setattr__(cache, "_temp_dir", temp_dir)

    return cache


# ============================================================================
# DiskCache Tests
# ============================================================================


def test_disk_cache_initially_empty() -> None:

    cache = create_disk_cache()

    assert cache.size() == 0


def test_disk_cache_save() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    assert path.exists()


def test_disk_cache_load() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    cache.save(
        "cea",
        entry,
    )

    loaded = cache.load(
        "cea",
        entry.key,
    )

    assert loaded is not None

    assert loaded.key == entry.key


def test_disk_cache_load_missing() -> None:

    cache = create_disk_cache()

    result = cache.load(
        "cea",
        "missing",
    )

    assert result is None


def test_disk_cache_exists_true() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    cache.save(
        "cea",
        entry,
    )

    assert cache.exists(
        "cea",
        entry.key,
    )


def test_disk_cache_exists_false() -> None:

    cache = create_disk_cache()

    assert (
        cache.exists(
            "cea",
            "missing",
        )
        is False
    )


def test_disk_cache_delete() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    cache.save(
        "cea",
        entry,
    )

    assert cache.delete(
        "cea",
        entry.key,
    )


def test_disk_cache_delete_missing() -> None:

    cache = create_disk_cache()

    assert (
        cache.delete(
            "cea",
            "missing",
        )
        is False
    )


def test_disk_cache_size_after_save() -> None:

    cache = create_disk_cache()

    cache.save(
        "cea",
        create_cache_entry(),
    )

    assert cache.size() == 1


def test_disk_cache_clear() -> None:

    cache = create_disk_cache()

    cache.save(
        "cea",
        create_cache_entry(),
    )

    removed = cache.clear()

    assert removed == 1

    assert cache.size() == 0


def test_disk_cache_namespaces() -> None:

    cache = create_disk_cache()

    cache.save(
        "cea",
        create_cache_entry(),
    )

    names = (
        cache.namespaces()
    )

    assert "cea" in names


def test_disk_cache_multiple_namespaces() -> None:

    cache = create_disk_cache()

    cache.save(
        "cea",
        create_cache_entry(),
    )

    cache.save(
        "equilibrium",
        CacheEntry(
            key="eq",
            created_at=datetime.now(
                tz=UTC
            ),
            expires_at=None,
            payload={},
            source=CacheSource.USER,
            metadata={},
        ),
    )

    names = (
        cache.namespaces()
    )

    assert (
        len(names)
        == 2
    )


def test_disk_cache_statistics_object() -> None:

    cache = create_disk_cache()

    stats = (
        cache.statistics()
    )

    assert isinstance(
        stats,
        CacheStatistics,
    )


def test_disk_cache_write_statistics() -> None:

    cache = create_disk_cache()

    cache.save(
        "cea",
        create_cache_entry(),
    )

    stats = (
        cache.statistics()
    )

    assert stats.writes == 1


def test_disk_cache_hit_statistics() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    cache.save(
        "cea",
        entry,
    )

    cache.load(
        "cea",
        entry.key,
    )

    stats = (
        cache.statistics()
    )

    assert stats.hits == 1


def test_disk_cache_miss_statistics() -> None:

    cache = create_disk_cache()

    cache.load(
        "cea",
        "missing",
    )

    stats = (
        cache.statistics()
    )

    assert stats.misses == 1


def test_disk_cache_eviction_statistics() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    cache.save(
        "cea",
        entry,
    )

    cache.delete(
        "cea",
        entry.key,
    )

    stats = (
        cache.statistics()
    )

    assert (
        stats.evictions
        == 1
    )


def test_disk_cache_cache_directory_property() -> None:

    cache = create_disk_cache()

    assert isinstance(
        cache.cache_directory,
        Path,
    )


def test_disk_cache_multiple_entries() -> None:

    cache = create_disk_cache()

    for i in range(10):

        cache.save(
            "cea",
            CacheEntry(
                key=f"k{i}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "i": i
                },
                source=CacheSource.USER,
                metadata={},
            ),
        )

    assert cache.size() == 10


def test_disk_cache_load_multiple_entries() -> None:

    cache = create_disk_cache()

    for i in range(5):

        cache.save(
            "cea",
            CacheEntry(
                key=f"k{i}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "i": i
                },
                source=CacheSource.USER,
                metadata={},
            ),
        )

    for i in range(5):

        entry = cache.load(
            "cea",
            f"k{i}",
        )

        assert entry is not None


def test_disk_cache_corrupt_file() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "INVALID JSON",
        encoding="utf-8",
    )

    with pytest.raises(
        CacheCorruptionError
    ):

        cache.load(
            "cea",
            entry.key,
        )


def test_disk_cache_corruption_statistics() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "INVALID JSON",
        encoding="utf-8",
    )

    try:

        cache.load(
            "cea",
            entry.key,
        )

    except CacheCorruptionError:
        pass

    stats = (
        cache.statistics()
    )

    assert (
        stats.corrupt_entries
        == 1
    )

# ============================================================================
# ThermochemistryCache Helpers
# ============================================================================


def create_thermochemistry_cache(
) -> ThermochemistryCache:

    temp_dir = TemporaryDirectory()

    cache = (
        ThermochemistryCache(
            Path(
                temp_dir.name
            )
        )
    )

    return cache

# ============================================================================
# ThermochemistryCache Tests
# ============================================================================


def test_thermochemistry_cache_creation() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    assert isinstance(
        cache,
        ThermochemistryCache,
    )


def test_thermochemistry_cache_set() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    entry = (
        create_cache_entry()
    )

    cache.set(
        "cea",
        entry,
    )

    assert cache.exists(
        "cea",
        entry.key,
    )


def test_thermochemistry_cache_get() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    entry = (
        create_cache_entry()
    )

    cache.set(
        "cea",
        entry,
    )

    result = cache.get(
        "cea",
        entry.key,
    )

    assert result is not None

    assert (
        result.key
        == entry.key
    )


def test_thermochemistry_cache_get_missing() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    result = cache.get(
        "cea",
        "missing",
    )

    assert result is None


def test_thermochemistry_cache_exists_false() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    assert (
        cache.exists(
            "cea",
            "missing",
        )
        is False
    )


def test_thermochemistry_cache_remove() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    entry = (
        create_cache_entry()
    )

    cache.set(
        "cea",
        entry,
    )

    assert cache.remove(
        "cea",
        entry.key,
    )


def test_thermochemistry_cache_remove_missing() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    assert (
        cache.remove(
            "cea",
            "missing",
        )
        is False
    )


def test_thermochemistry_cache_clear() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    cache.set(
        "cea",
        create_cache_entry(),
    )

    cache.clear()

    assert (
        cache.memory_cache.size()
        == 0
    )


def test_thermochemistry_cache_memory_cache_accessor() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    assert isinstance(
        cache.memory_cache,
        MemoryCache,
    )


def test_thermochemistry_cache_disk_cache_accessor() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    assert isinstance(
        cache.disk_cache,
        DiskCache,
    )


def test_thermochemistry_cache_statistics() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    stats = (
        cache.statistics()
    )

    assert (
        "memory"
        in stats
    )

    assert (
        "disk"
        in stats
    )


def test_thermochemistry_cache_statistics_sizes() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    stats = (
        cache.statistics()
    )

    assert (
        "memory_size"
        in stats
    )

    assert (
        "disk_size"
        in stats
    )


def test_disk_to_memory_promotion() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    entry = (
        create_cache_entry()
    )

    cache.disk_cache.save(
        "cea",
        entry,
    )

    result = cache.get(
        "cea",
        entry.key,
    )

    assert result is not None

    assert (
        cache.memory_cache.exists(
            entry.key
        )
    )


def test_cleanup_expired_empty() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    removed = (
        cache.cleanup_expired()
    )

    assert removed == 0


def test_context_manager() -> None:

    with (
        create_thermochemistry_cache()
    ) as cache:

        assert isinstance(
            cache,
            ThermochemistryCache,
        )


def test_context_manager_get() -> None:

    with (
        create_thermochemistry_cache()
    ) as cache:

        entry = (
            create_cache_entry()
        )

        cache.set(
            "cea",
            entry,
        )

        result = cache.get(
            "cea",
            entry.key,
        )

        assert result is not None


def test_global_cache_singleton() -> None:

    reset_global_cache()

    cache_a = (
        get_global_cache()
    )

    cache_b = (
        get_global_cache()
    )

    assert (
        cache_a
        is cache_b
    )


def test_reset_global_cache() -> None:

    reset_global_cache()

    cache_a = (
        get_global_cache()
    )

    reset_global_cache()

    cache_b = (
        get_global_cache()
    )

    assert (
        cache_a
        is not cache_b
    )


def test_global_cache_type() -> None:

    reset_global_cache()

    cache = (
        get_global_cache()
    )

    assert isinstance(
        cache,
        ThermochemistryCache,
    )


def test_global_cache_set_and_get() -> None:

    reset_global_cache()

    cache = (
        get_global_cache()
    )

    cache.clear()

    entry = (
        create_cache_entry()
    )

    cache.set(
        "cea",
        entry,
    )

    result = cache.get(
        "cea",
        entry.key,
    )

    assert result is not None


def test_global_cache_exists() -> None:

    reset_global_cache()

    cache = (
        get_global_cache()
    )

    cache.clear()

    entry = (
        create_cache_entry()
    )

    cache.set(
        "cea",
        entry,
    )

    assert cache.exists(
        "cea",
        entry.key,
    )


def test_multiple_entries_same_namespace() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    for i in range(20):

        cache.set(
            "cea",
            CacheEntry(
                key=f"k{i}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "index": i
                },
                source=CacheSource.USER,
                metadata={},
            ),
        )

    assert (
        cache.memory_cache.size()
        == 20
    )


def test_multiple_namespaces() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    cache.set(
        "cea",
        create_cache_entry(),
    )

    cache.set(
        "equilibrium",
        CacheEntry(
            key="eq",
            created_at=datetime.now(
                tz=UTC
            ),
            expires_at=None,
            payload={},
            source=CacheSource.USER,
            metadata={},
        ),
    )

    assert (
        cache.disk_cache.size()
        == 2
    )

# ============================================================================
# Expiration Helpers
# ============================================================================


def create_expired_entry() -> CacheEntry:

    now = datetime.now(
        tz=UTC,
    )

    return CacheEntry(
        key="expired_key",
        created_at=(
            now
            - timedelta(
                hours=2
            )
        ),
        expires_at=(
            now
            - timedelta(
                hours=1
            )
        ),
        payload={
            "expired": True,
        },
        source=CacheSource.USER,
        metadata={},
    )


def create_unexpired_entry() -> CacheEntry:

    now = datetime.now(
        tz=UTC,
    )

    return CacheEntry(
        key="active_key",
        created_at=now,
        expires_at=(
            now
            + timedelta(
                hours=1
            )
        ),
        payload={
            "active": True,
        },
        source=CacheSource.USER,
        metadata={},
    )

# ============================================================================
# Expiration Tests
# ============================================================================


def test_cache_entry_is_expired_true() -> None:

    entry = (
        create_expired_entry()
    )

    assert (
        cache_entry_is_expired(
            entry
        )
        is True
    )


def test_cache_entry_is_expired_false() -> None:

    entry = (
        create_unexpired_entry()
    )

    assert (
        cache_entry_is_expired(
            entry
        )
        is False
    )


def test_cache_entry_no_expiration() -> None:

    entry = (
        create_cache_entry()
    )

    assert (
        cache_entry_is_expired(
            entry
        )
        is False
    )


def test_memory_cache_expired_entry_get() -> None:

    cache = create_memory_cache()

    entry = (
        create_expired_entry()
    )

    cache.set(entry)

    result = cache.get(
        entry.key
    )

    assert result is None


def test_memory_cache_expired_entry_exists() -> None:

    cache = create_memory_cache()

    entry = (
        create_expired_entry()
    )

    cache.set(entry)

    assert (
        cache.exists(
            entry.key
        )
        is False
    )


def test_memory_cache_cleanup_expired() -> None:

    cache = create_memory_cache()

    cache.set(
        create_expired_entry()
    )

    removed = (
        cache.cleanup_expired()
    )

    assert removed == 1


def test_memory_cache_cleanup_expired_empty() -> None:

    cache = create_memory_cache()

    removed = (
        cache.cleanup_expired()
    )

    assert removed == 0


def test_memory_cache_cleanup_unexpired() -> None:

    cache = create_memory_cache()

    cache.set(
        create_unexpired_entry()
    )

    removed = (
        cache.cleanup_expired()
    )

    assert removed == 0


def test_memory_cache_expiration_statistics() -> None:

    cache = create_memory_cache()

    cache.set(
        create_expired_entry()
    )

    cache.cleanup_expired()

    stats = (
        cache.statistics()
    )

    assert (
        stats.expired_entries
        == 1
    )


def test_disk_cache_expired_load() -> None:

    cache = create_disk_cache()

    entry = (
        create_expired_entry()
    )

    cache.save(
        "cea",
        entry,
    )

    result = cache.load(
        "cea",
        entry.key,
    )

    assert result is None


def test_disk_cache_expired_exists() -> None:

    cache = create_disk_cache()

    entry = (
        create_expired_entry()
    )

    cache.save(
        "cea",
        entry,
    )

    assert (
        cache.exists(
            "cea",
            entry.key,
        )
        is False
    )


def test_disk_cache_cleanup_expired() -> None:

    cache = create_disk_cache()

    cache.save(
        "cea",
        create_expired_entry(),
    )

    removed = (
        cache.cleanup_expired()
    )

    assert removed == 1


def test_disk_cache_cleanup_unexpired() -> None:

    cache = create_disk_cache()

    cache.save(
        "cea",
        create_unexpired_entry(),
    )

    removed = (
        cache.cleanup_expired()
    )

    assert removed == 0


def test_disk_cache_expired_statistics() -> None:

    cache = create_disk_cache()

    cache.save(
        "cea",
        create_expired_entry(),
    )

    cache.cleanup_expired()

    stats = (
        cache.statistics()
    )

    assert (
        stats.expired_entries
        == 1
    )


def test_thermochemistry_cache_cleanup_expired_memory() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    cache.memory_cache.set(
        create_expired_entry()
    )

    removed = (
        cache.cleanup_expired()
    )

    assert removed >= 1


def test_thermochemistry_cache_cleanup_expired_disk() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    cache.disk_cache.save(
        "cea",
        create_expired_entry(),
    )

    removed = (
        cache.cleanup_expired()
    )

    assert removed >= 1


def test_thermochemistry_cache_get_expired() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    entry = (
        create_expired_entry()
    )

    cache.set(
        "cea",
        entry,
    )

    result = cache.get(
        "cea",
        entry.key,
    )

    assert result is None


def test_expired_entry_removed_from_memory_cache() -> None:

    cache = create_memory_cache()

    entry = (
        create_expired_entry()
    )

    cache.set(entry)

    cache.get(
        entry.key
    )

    assert (
        cache.size()
        == 0
    )


def test_expired_entry_removed_from_disk_cache() -> None:

    cache = create_disk_cache()

    entry = (
        create_expired_entry()
    )

    cache.save(
        "cea",
        entry,
    )

    cache.load(
        "cea",
        entry.key,
    )

    assert (
        cache.size()
        == 0
    )


def test_unexpired_entry_remains_memory_cache() -> None:

    cache = create_memory_cache()

    cache.set(
        create_unexpired_entry()
    )

    cache.cleanup_expired()

    assert (
        cache.size()
        == 1
    )


def test_unexpired_entry_remains_disk_cache() -> None:

    cache = create_disk_cache()

    cache.save(
        "cea",
        create_unexpired_entry(),
    )

    cache.cleanup_expired()

    assert (
        cache.size()
        == 1
    )

# ============================================================================
# Serialization Tests
# ============================================================================


def test_cache_entry_to_dict() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    assert isinstance(
        data,
        dict,
    )

    assert (
        data["key"]
        == "test_key"
    )


def test_cache_entry_to_dict_contains_required_fields() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    required = {
        "key",
        "created_at",
        "expires_at",
        "payload",
        "source",
        "metadata",
        "schema_version",
    }

    assert (
        required
        <= set(data.keys())
    )


def test_cache_entry_from_dict() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    restored = (
        _cache_entry_from_dict(
            data
        )
    )

    assert (
        restored.key
        == entry.key
    )


def test_cache_entry_from_dict_payload() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    restored = (
        _cache_entry_from_dict(
            data
        )
    )

    assert (
        restored.payload[
            "value"
        ]
        == 42
    )


def test_cache_entry_from_dict_source() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    restored = (
        _cache_entry_from_dict(
            data
        )
    )

    assert (
        restored.source
        is CacheSource.USER
    )


def test_round_trip_dict_serialization() -> None:

    original = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            original
        )
    )

    restored = (
        _cache_entry_from_dict(
            data
        )
    )

    assert (
        restored.key
        == original.key
    )

    assert (
        restored.payload
        == original.payload
    )

    assert (
        restored.metadata
        == original.metadata
    )


def test_cache_entry_to_json() -> None:

    entry = (
        create_cache_entry()
    )

    text = (
        cache_entry_to_json(
            entry
        )
    )

    assert isinstance(
        text,
        str,
    )


def test_cache_entry_to_json_contains_key() -> None:

    entry = (
        create_cache_entry()
    )

    text = (
        cache_entry_to_json(
            entry
        )
    )

    assert (
        "test_key"
        in text
    )


def test_cache_entry_from_json() -> None:

    entry = (
        create_cache_entry()
    )

    text = (
        cache_entry_to_json(
            entry
        )
    )

    restored = (
        cache_entry_from_json(
            text
        )
    )

    assert (
        restored.key
        == entry.key
    )


def test_round_trip_json_serialization() -> None:

    original = (
        create_cache_entry()
    )

    text = (
        cache_entry_to_json(
            original
        )
    )

    restored = (
        cache_entry_from_json(
            text
        )
    )

    assert (
        restored.key
        == original.key
    )

    assert (
        restored.payload
        == original.payload
    )


def test_schema_version_preserved_dict() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    assert (
        data[
            "schema_version"
        ]
        == CACHE_SCHEMA_VERSION
    )


def test_schema_version_preserved_json() -> None:

    entry = (
        create_cache_entry()
    )

    text = (
        cache_entry_to_json(
            entry
        )
    )

    data = json.loads(
        text
    )

    assert (
        data[
            "schema_version"
        ]
        == CACHE_SCHEMA_VERSION
    )


def test_missing_key_field() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    del data["key"]

    with pytest.raises(
        CacheSerializationError
    ):

        _cache_entry_from_dict(
            data
        )


def test_missing_created_at_field() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    del data["created_at"]

    with pytest.raises(
        CacheSerializationError
    ):

        _cache_entry_from_dict(
            data
        )


def test_missing_payload_field() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    del data["payload"]

    with pytest.raises(
        CacheSerializationError
    ):

        _cache_entry_from_dict(
            data
        )


def test_missing_source_field() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    del data["source"]

    with pytest.raises(
        CacheSerializationError
    ):

        _cache_entry_from_dict(
            data
        )


def test_invalid_json_string() -> None:

    with pytest.raises(
        CacheSerializationError
    ):

        cache_entry_from_json(
            "INVALID JSON"
        )


def test_invalid_json_root_type() -> None:

    with pytest.raises(
        CacheSerializationError
    ):

        cache_entry_from_json(
            "[1,2,3]"
        )


def test_invalid_source_in_dict() -> None:

    entry = (
        create_cache_entry()
    )

    data = (
        _cache_entry_to_dict(
            entry
        )
    )

    data["source"] = (
        "INVALID_SOURCE"
    )

    with pytest.raises(
        Exception
    ):

        _cache_entry_from_dict(
            data
        )


def test_json_round_trip_many_entries() -> None:

    for index in range(
        25
    ):

        entry = CacheEntry(
            key=f"k{index}",
            created_at=datetime.now(
                tz=UTC
            ),
            expires_at=None,
            payload={
                "index": index
            },
            source=CacheSource.USER,
            metadata={},
        )

        text = (
            cache_entry_to_json(
                entry
            )
        )

        restored = (
            cache_entry_from_json(
                text
            )
        )

        assert (
            restored.key
            == entry.key
        )


def test_metadata_preserved() -> None:

    entry = (
        create_cache_entry()
    )

    text = (
        cache_entry_to_json(
            entry
        )
    )

    restored = (
        cache_entry_from_json(
            text
        )
    )

    assert (
        restored.metadata
        == entry.metadata
    )


def test_expiration_preserved() -> None:

    entry = (
        create_unexpired_entry()
    )

    text = (
        cache_entry_to_json(
            entry
        )
    )

    restored = (
        cache_entry_from_json(
            text
        )
    )

    assert (
        restored.expires_at
        == entry.expires_at
    )

# ============================================================================
# Corruption & Recovery Tests
# ============================================================================


def test_corrupt_json_file_raises() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    with pytest.raises(
        CacheCorruptionError
    ):
        cache.load(
            "cea",
            entry.key,
        )


def test_truncated_json_file_raises() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        '{"key":"abc"',
        encoding="utf-8",
    )

    with pytest.raises(
        CacheCorruptionError
    ):
        cache.load(
            "cea",
            entry.key,
        )


def test_empty_file_raises() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(
        CacheCorruptionError
    ):
        cache.load(
            "cea",
            entry.key,
        )


def test_corrupt_file_removed() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "CORRUPT",
        encoding="utf-8",
    )

    try:

        cache.load(
            "cea",
            entry.key,
        )

    except CacheCorruptionError:
        pass

    assert (
        path.exists()
        is False
    )


def test_corruption_statistics_increment() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "CORRUPT",
        encoding="utf-8",
    )

    try:

        cache.load(
            "cea",
            entry.key,
        )

    except CacheCorruptionError:
        pass

    stats = (
        cache.statistics()
    )

    assert (
        stats.corrupt_entries
        == 1
    )


def test_multiple_corrupt_files() -> None:

    cache = create_disk_cache()

    for index in range(
        5
    ):

        entry = CacheEntry(
            key=f"k{index}",
            created_at=datetime.now(
                tz=UTC
            ),
            expires_at=None,
            payload={},
            source=CacheSource.USER,
            metadata={},
        )

        path = cache.save(
            "cea",
            entry,
        )

        path.write_text(
            "CORRUPT",
            encoding="utf-8",
        )

    failures = 0

    for index in range(
        5
    ):

        try:

            cache.load(
                "cea",
                f"k{index}",
            )

        except CacheCorruptionError:

            failures += 1

    assert failures == 5


def test_cleanup_expired_handles_corrupt_files() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "BROKEN",
        encoding="utf-8",
    )

    removed = (
        cache.cleanup_expired()
    )

    assert removed == 1


def test_cleanup_expired_updates_corrupt_statistics() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "BROKEN",
        encoding="utf-8",
    )

    cache.cleanup_expired()

    stats = (
        cache.statistics()
    )

    assert (
        stats.corrupt_entries
        == 1
    )


def test_exists_returns_false_for_corrupt_file() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "CORRUPT",
        encoding="utf-8",
    )

    assert (
        cache.exists(
            "cea",
            entry.key,
        )
        is False
    )


def test_corrupt_file_removed_by_exists() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "CORRUPT",
        encoding="utf-8",
    )

    cache.exists(
        "cea",
        entry.key,
    )

    assert (
        path.exists()
        is False
    )


def test_recovery_after_corruption() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "CORRUPT",
        encoding="utf-8",
    )

    try:

        cache.load(
            "cea",
            entry.key,
        )

    except CacheCorruptionError:
        pass

    cache.save(
        "cea",
        entry,
    )

    restored = cache.load(
        "cea",
        entry.key,
    )

    assert restored is not None


def test_recovery_preserves_payload() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "CORRUPT",
        encoding="utf-8",
    )

    try:

        cache.load(
            "cea",
            entry.key,
        )

    except CacheCorruptionError:
        pass

    cache.save(
        "cea",
        entry,
    )

    restored = cache.load(
        "cea",
        entry.key,
    )

    assert restored is not None
    assert (
        restored.payload[
            "value"
        ]
        == 42
    )


def test_load_after_corruption_is_miss() -> None:

    cache = create_disk_cache()

    entry = create_cache_entry()

    path = cache.save(
        "cea",
        entry,
    )

    path.write_text(
        "CORRUPT",
        encoding="utf-8",
    )

    try:

        cache.load(
            "cea",
            entry.key,
        )

    except CacheCorruptionError:
        pass

    result = cache.load(
        "cea",
        entry.key,
    )

    assert result is None


def test_corrupt_file_does_not_affect_other_entries() -> None:

    cache = create_disk_cache()

    good = CacheEntry(
        key="good",
        created_at=datetime.now(
            tz=UTC
        ),
        expires_at=None,
        payload={
            "ok": True
        },
        source=CacheSource.USER,
        metadata={},
    )

    bad = CacheEntry(
        key="bad",
        created_at=datetime.now(
            tz=UTC
        ),
        expires_at=None,
        payload={},
        source=CacheSource.USER,
        metadata={},
    )

    cache.save(
        "cea",
        good,
    )

    path = cache.save(
        "cea",
        bad,
    )

    path.write_text(
        "CORRUPT",
        encoding="utf-8",
    )

    try:

        cache.load(
            "cea",
            "bad",
        )

    except CacheCorruptionError:
        pass

    result = cache.load(
        "cea",
        "good",
    )

    assert result is not None


def test_corruption_statistics_multiple_files() -> None:

    cache = create_disk_cache()

    for index in range(
        3
    ):

        entry = CacheEntry(
            key=f"c{index}",
            created_at=datetime.now(
                tz=UTC
            ),
            expires_at=None,
            payload={},
            source=CacheSource.USER,
            metadata={},
        )

        path = cache.save(
            "cea",
            entry,
        )

        path.write_text(
            "CORRUPT",
            encoding="utf-8",
        )

    for index in range(
        3
    ):

        try:

            cache.load(
                "cea",
                f"c{index}",
            )

        except CacheCorruptionError:
            pass

    stats = (
        cache.statistics()
    )

    assert (
        stats.corrupt_entries
        == 3
    )

# ============================================================================
# Thread Safety Tests
# ============================================================================


def test_memory_cache_concurrent_writes() -> None:

    cache = create_memory_cache()

    def worker(
        index: int,
    ) -> None:

        cache.set(
            CacheEntry(
                key=f"k{index}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "index": index
                },
                source=CacheSource.USER,
                metadata={},
            )
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        list(
            executor.map(
                worker,
                range(100),
            )
        )

    assert cache.size() == 100


def test_memory_cache_concurrent_reads() -> None:

    cache = create_memory_cache()

    for i in range(100):

        cache.set(
            CacheEntry(
                key=f"k{i}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "index": i
                },
                source=CacheSource.USER,
                metadata={},
            )
        )

    def worker(
        index: int,
    ) -> CacheEntry | None:

        return cache.get(
            f"k{index}"
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        results = list(
            executor.map(
                worker,
                range(100),
            )
        )

    assert all(
        result is not None
        for result in results
    )


def test_memory_cache_concurrent_exists() -> None:

    cache = create_memory_cache()

    cache.set(
        create_cache_entry()
    )

    def worker() -> bool:

        return cache.exists(
            "test_key"
        )

    with ThreadPoolExecutor(
        max_workers=16
    ) as executor:

        results = list(
            executor.map(
                lambda _: worker(),
                range(100),
            )
        )

    assert all(results)


def test_memory_cache_concurrent_remove() -> None:

    cache = create_memory_cache()

    cache.set(
        create_cache_entry()
    )

    def worker() -> bool:

        return cache.remove(
            "test_key"
        )

    with ThreadPoolExecutor(
        max_workers=16
    ) as executor:

        results = list(
            executor.map(
                lambda _: worker(),
                range(20),
            )
        )

    assert sum(results) == 1


def test_disk_cache_concurrent_writes() -> None:

    cache = create_disk_cache()

    def worker(
        index: int,
    ) -> None:

        cache.save(
            "cea",
            CacheEntry(
                key=f"k{index}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "index": index
                },
                source=CacheSource.USER,
                metadata={},
            ),
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        list(
            executor.map(
                worker,
                range(50),
            )
        )

    assert cache.size() == 50


def test_disk_cache_concurrent_reads() -> None:

    cache = create_disk_cache()

    for i in range(50):

        cache.save(
            "cea",
            CacheEntry(
                key=f"k{i}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "index": i
                },
                source=CacheSource.USER,
                metadata={},
            ),
        )

    def worker(
        index: int,
    ) -> CacheEntry | None:

        return cache.load(
            "cea",
            f"k{index}",
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        results = list(
            executor.map(
                worker,
                range(50),
            )
        )

    assert all(
        result is not None
        for result in results
    )


def test_thermochemistry_cache_concurrent_writes() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    def worker(
        index: int,
    ) -> None:

        cache.set(
            "cea",
            CacheEntry(
                key=f"k{index}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "index": index
                },
                source=CacheSource.USER,
                metadata={},
            ),
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        list(
            executor.map(
                worker,
                range(75),
            )
        )

    assert (
        cache.memory_cache.size()
        == 75
    )


def test_thermochemistry_cache_concurrent_reads() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    for i in range(75):

        cache.set(
            "cea",
            CacheEntry(
                key=f"k{i}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "index": i
                },
                source=CacheSource.USER,
                metadata={},
            ),
        )

    def worker(
        index: int,
    ) -> CacheEntry | None:

        return cache.get(
            "cea",
            f"k{index}",
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        results = list(
            executor.map(
                worker,
                range(75),
            )
        )

    assert all(
        result is not None
        for result in results
    )


def test_concurrent_global_cache_access() -> None:

    reset_global_cache()

    def worker() -> int:

        return id(
            get_global_cache()
        )

    with ThreadPoolExecutor(
        max_workers=16
    ) as executor:

        results = list(
            executor.map(
                lambda _: worker(),
                range(100),
            )
        )

    assert (
        len(set(results))
        == 1
    )


def test_global_cache_singleton_thread_safe() -> None:

    reset_global_cache()

    def worker():

        return (
            get_global_cache()
        )

    with ThreadPoolExecutor(
        max_workers=16
    ) as executor:

        caches = list(
            executor.map(
                lambda _: worker(),
                range(100),
            )
        )

    first = caches[0]

    assert all(
        cache is first
        for cache in caches
    )


def test_concurrent_statistics_access() -> None:

    cache = create_memory_cache()

    cache.set(
        create_cache_entry()
    )

    def worker():

        return (
            cache.statistics()
        )

    with ThreadPoolExecutor(
        max_workers=16
    ) as executor:

        stats = list(
            executor.map(
                lambda _: worker(),
                range(100),
            )
        )

    assert len(stats) == 100


def test_concurrent_cleanup_operations() -> None:

    cache = create_memory_cache()

    for i in range(25):

        cache.set(
            CacheEntry(
                key=f"k{i}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={},
                source=CacheSource.USER,
                metadata={},
            )
        )

    def worker():

        return (
            cache.cleanup_expired()
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        list(
            executor.map(
                lambda _: worker(),
                range(20),
            )
        )

    assert (
        cache.size()
        == 25
    )


def test_concurrent_namespace_operations() -> None:

    cache = create_disk_cache()

    def worker(
        index: int,
    ) -> None:

        namespace = (
            f"ns{index % 5}"
        )

        cache.save(
            namespace,
            CacheEntry(
                key=f"k{index}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={},
                source=CacheSource.USER,
                metadata={},
            ),
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        list(
            executor.map(
                worker,
                range(100),
            )
        )

    assert (
        len(
            cache.namespaces()
        )
        == 5
    )


def test_concurrent_set_get_operations() -> None:

    cache = (
        create_thermochemistry_cache()
    )

    def writer(
        index: int,
    ) -> None:

        cache.set(
            "cea",
            CacheEntry(
                key=f"k{index}",
                created_at=datetime.now(
                    tz=UTC
                ),
                expires_at=None,
                payload={
                    "index": index
                },
                source=CacheSource.USER,
                metadata={},
            ),
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        list(
            executor.map(
                writer,
                range(100),
            )
        )

    def reader(
        index: int,
    ) -> CacheEntry | None:

        return cache.get(
            "cea",
            f"k{index}",
        )

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:

        results = list(
            executor.map(
                reader,
                range(100),
            )
        )

    assert all(
        result is not None
        for result in results
    )

