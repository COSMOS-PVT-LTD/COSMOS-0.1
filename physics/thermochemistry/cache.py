# ============================================================================
# Public API
# ============================================================================

__all__ = (
    "CACHE_SCHEMA_VERSION",
    "DEFAULT_CACHE_DIRECTORY",
    "CacheError",
    "CacheCorruptionError",
    "CacheKeyError",
    "CacheSerializationError",
    "CacheSource",
    "CacheEntry",
    "CacheStatistics",
    "MemoryCache",
    "DiskCache",
    "ThermochemistryCache",
    "generate_cache_key",
    "get_global_cache",
    "reset_global_cache",
    "cache",
)

# ============================================================================
# Standard Library
# ============================================================================

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from enum import Enum
from typing import Any

# ============================================================================
# Constants
# ============================================================================

CACHE_SCHEMA_VERSION: str = "1.0.0"

DEFAULT_CACHE_DIRECTORY: str = "cache"

# ============================================================================
# Exceptions
# ============================================================================


class CacheError(Exception):
    """
    Base cache exception.
    """


class CacheCorruptionError(CacheError):
    """
    Raised when a cache entry is corrupt.
    """


class CacheKeyError(CacheError):
    """
    Raised when a cache key is invalid.
    """


class CacheSerializationError(CacheError):
    """
    Raised when cache serialization fails.
    """

# ============================================================================
# Enumerations
# ============================================================================


class CacheSource(str, Enum):
    """
    Source of cached data.
    """

    MEMORY = "MEMORY"

    DISK = "DISK"

    ROCKETCEA = "ROCKETCEA"

    NASA_CEA = "NASA_CEA"

    CANTERA = "CANTERA"

    EQUILIBRIUM = "EQUILIBRIUM"

    MIXTURE = "MIXTURE"

    OPTIMIZATION = "OPTIMIZATION"

    USER = "USER"

# ============================================================================
# Cache Entry
# ============================================================================


@dataclass(
    frozen=True,
    slots=True,
)
class CacheEntry:
    """
    Immutable cache entry.
    """

    key: str

    created_at: datetime

    expires_at: datetime | None

    payload: dict[str, Any]

    source: CacheSource

    metadata: dict[str, str]

    schema_version: str = CACHE_SCHEMA_VERSION

    def __post_init__(
        self,
    ) -> None:
        """
        Validate entry.
        """

        if not self.key:
            raise CacheKeyError(
                "Cache key cannot be empty."
            )

        if not isinstance(
            self.source,
            CacheSource,
        ):
            raise CacheSerializationError(
                "Invalid cache source."
            )

        if (
            self.created_at.tzinfo
            is None
        ):
            raise CacheSerializationError(
                "created_at must be "
                "timezone aware."
            )

        if (
            self.expires_at
            is not None
            and
            self.expires_at.tzinfo
            is None
        ):
            raise CacheSerializationError(
                "expires_at must be "
                "timezone aware."
            )

# ============================================================================
# Cache Statistics
# ============================================================================


@dataclass(
    slots=True,
)
class CacheStatistics:
    """
    Cache statistics.
    """

    hits: int = 0

    misses: int = 0

    writes: int = 0

    evictions: int = 0

    memory_hits: int = 0

    disk_hits: int = 0

    expired_entries: int = 0

    corrupt_entries: int = 0

    @property
    def hit_rate(
        self,
    ) -> float:
        """
        Return cache hit rate.
        """

        total = (
            self.hits
            + self.misses
        )

        if total == 0:
            return 0.0

        return (
            self.hits
            / total
        )

# ============================================================================
# Utility Functions
# ============================================================================


def utc_now() -> datetime:
    """
    Return current UTC timestamp.
    """

    return datetime.now(
        tz=UTC,
    )
# ============================================================================
# Standard Library Imports (Part 2)
# ============================================================================

import hashlib
import json

from pathlib import Path

# ============================================================================
# CacheEntry Serialization
# ============================================================================


def _datetime_to_string(
    value: datetime | None,
) -> str | None:
    """
    Convert datetime to ISO string.
    """

    if value is None:
        return None

    return value.isoformat()


def _datetime_from_string(
    value: str | None,
) -> datetime | None:
    """
    Convert ISO string to datetime.
    """

    if value is None:
        return None

    return datetime.fromisoformat(
        value,
    )


def _cache_entry_to_dict(
    entry: CacheEntry,
) -> dict[str, Any]:
    """
    Serialize cache entry.
    """

    return {
        "key": entry.key,
        "created_at": (
            _datetime_to_string(
                entry.created_at
            )
        ),
        "expires_at": (
            _datetime_to_string(
                entry.expires_at
            )
        ),
        "payload": entry.payload,
        "source": (
            entry.source.value
        ),
        "metadata": entry.metadata,
        "schema_version": (
            entry.schema_version
        ),
    }


def _cache_entry_from_dict(
    data: dict[str, Any],
) -> CacheEntry:
    """
    Deserialize cache entry.
    """

    required_fields = {
        "key",
        "created_at",
        "expires_at",
        "payload",
        "source",
        "metadata",
        "schema_version",
    }

    missing = (
        required_fields
        - set(data.keys())
    )

    if missing:
        raise (
            CacheSerializationError(
                "Missing cache "
                "fields: "
                f"{sorted(missing)}"
            )
        )

    created_at = _datetime_from_string(
        data["created_at"]
    )
    if created_at is None:
        raise CacheSerializationError(
            "created_at must be a valid ISO formatted datetime."
        )

    return CacheEntry(
        key=str(
            data["key"]
        ),
        created_at=created_at,
        expires_at=(
            _datetime_from_string(
                data["expires_at"]
            )
        ),
        payload=dict(
            data["payload"]
        ),
        source=CacheSource(
            data["source"]
        ),
        metadata=dict(
            data["metadata"]
        ),
        schema_version=str(
            data[
                "schema_version"
            ]
        ),
    )


def cache_entry_to_json(
    entry: CacheEntry,
) -> str:
    """
    Serialize entry to JSON.
    """

    try:

        return json.dumps(
            _cache_entry_to_dict(
                entry
            ),
            indent=4,
            sort_keys=True,
        )

    except Exception as exc:

        raise (
            CacheSerializationError(
                "Failed to "
                "serialize cache "
                "entry."
            )
        ) from exc


def cache_entry_from_json(
    text: str,
) -> CacheEntry:
    """
    Deserialize entry from JSON.
    """

    try:

        data = json.loads(
            text
        )

    except Exception as exc:

        raise (
            CacheSerializationError(
                "Invalid cache "
                "JSON."
            )
        ) from exc

    if not isinstance(
        data,
        dict,
    ):
        raise (
            CacheSerializationError(
                "Cache JSON "
                "must contain "
                "an object."
            )
        )

    return (
        _cache_entry_from_dict(
            data
        )
    )

# ============================================================================
# Cache Entry Convenience Methods
# ============================================================================


def cache_entry_is_expired(
    entry: CacheEntry,
) -> bool:
    """
    Determine expiration status.
    """

    if (
        entry.expires_at
        is None
    ):
        return False

    return (
        utc_now()
        >= entry.expires_at
    )

# ============================================================================
# SHA256 Cache Key Generation
# ============================================================================


def _normalize_parameters(
    parameters: dict[str, Any],
) -> str:
    """
    Create deterministic
    parameter representation.

    Ordering is guaranteed.
    """

    return json.dumps(
        parameters,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )


def generate_cache_key(
    namespace: str,
    parameters: dict[str, Any],
) -> str:
    """
    Generate deterministic
    SHA256 cache key.

    Parameters
    ----------
    namespace : str
        Cache namespace.

    parameters : dict[str, Any]
        Cache parameters.

    Returns
    -------
    str
        SHA256 key.
    """

    if not namespace:

        raise CacheKeyError(
            "Namespace cannot "
            "be empty."
        )

    normalized = (
        _normalize_parameters(
            parameters
        )
    )

    payload = (
        f"{namespace}|"
        f"{normalized}"
    )

    return hashlib.sha256(
        payload.encode(
            "utf-8"
        )
    ).hexdigest()

# ============================================================================
# Disk Utility Helpers
# ============================================================================


def cache_file_path(
    cache_directory: Path,
    namespace: str,
    key: str,
) -> Path:
    """
    Build cache file path.
    """

    return (
        cache_directory
        / namespace.lower()
        / f"{key}.json"
    )
# ============================================================================
# Standard Library Imports (Part 3)
# ============================================================================

from threading import RLock

# ============================================================================
# Memory Cache
# ============================================================================


class MemoryCache:
    """
    Thread-safe in-memory cache.

    Backend:
        dict[str, CacheEntry]

    Complexity:
        O(1)
    """

    def __init__(
        self,
    ) -> None:

        self._entries: dict[
            str,
            CacheEntry,
        ] = {}

        self._statistics = (
            CacheStatistics()
        )

        self._lock = RLock()

    # ---------------------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------------------

    def _evict_if_expired(
        self,
        key: str,
    ) -> bool:
        """
        Remove expired entry.

        Returns
        -------
        bool
            True if expired.
        """

        entry = (
            self._entries.get(
                key
            )
        )

        if entry is None:
            return False

        if not (
            cache_entry_is_expired(
                entry
            )
        ):
            return False

        del self._entries[key]

        self._statistics.evictions += 1

        self._statistics.expired_entries += 1

        return True

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def get(
        self,
        key: str,
    ) -> CacheEntry | None:
        """
        Retrieve cache entry.
        """

        with self._lock:

            if (
                self._evict_if_expired(
                    key
                )
            ):
                self._statistics.misses += 1

                return None

            entry = (
                self._entries.get(
                    key
                )
            )

            if entry is None:

                self._statistics.misses += 1

                return None

            self._statistics.hits += 1

            self._statistics.memory_hits += 1

            return entry

    def set(
        self,
        entry: CacheEntry,
    ) -> None:
        """
        Store cache entry.
        """

        with self._lock:

            self._entries[
                entry.key
            ] = entry

            self._statistics.writes += 1

    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check existence.
        """

        with self._lock:

            if (
                self._evict_if_expired(
                    key
                )
            ):
                return False

            return (
                key
                in self._entries
            )

    def remove(
        self,
        key: str,
    ) -> bool:
        """
        Remove cache entry.
        """

        with self._lock:

            if (
                key
                not in self._entries
            ):
                return False

            del self._entries[key]

            self._statistics.evictions += 1

            return True

    def clear(
        self,
    ) -> None:
        """
        Clear cache.
        """

        with self._lock:

            count = len(
                self._entries
            )

            self._entries.clear()

            self._statistics.evictions += (
                count
            )

    def size(
        self,
    ) -> int:
        """
        Return entry count.
        """

        with self._lock:

            return len(
                self._entries
            )

    def keys(
        self,
    ) -> tuple[str, ...]:
        """
        Return cache keys.
        """

        with self._lock:

            return tuple(
                self._entries.keys()
            )

    def cleanup_expired(
        self,
    ) -> int:
        """
        Remove all expired entries.

        Returns
        -------
        int
            Removed count.
        """

        removed = 0

        with self._lock:

            keys = tuple(
                self._entries.keys()
            )

            for key in keys:

                if (
                    self._evict_if_expired(
                        key
                    )
                ):
                    removed += 1

        return removed

    def statistics(
        self,
    ) -> CacheStatistics:
        """
        Return statistics object.
        """

        return self._statistics

    def snapshot(
        self,
    ) -> dict[str, CacheEntry]:
        """
        Return copy of entries.

        Useful for testing.
        """

        with self._lock:

            return dict(
                self._entries
            )

# ============================================================================
# Memory Cache Factory
# ============================================================================


def create_memory_cache(
) -> MemoryCache:
    """
    Create memory cache.
    """

    return MemoryCache()
# ============================================================================
# Disk Cache
# ============================================================================


class DiskCache:
    """
    Persistent JSON cache storage.
    """

    def __init__(
        self,
        cache_directory: Path,
    ) -> None:

        self._cache_directory = (
            cache_directory
        )

        self._statistics = (
            CacheStatistics()
        )

        self._lock = RLock()

        self._cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _file_path(
        self,
        namespace: str,
        key: str,
    ) -> Path:
        """
        Return cache file path.
        """

        return cache_file_path(
            self._cache_directory,
            namespace,
            key,
        )

    def _ensure_namespace(
        self,
        namespace: str,
    ) -> Path:
        """
        Create namespace directory.
        """

        directory = (
            self._cache_directory
            / namespace.lower()
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    def _handle_corruption(
        self,
        file_path: Path,
    ) -> None:
        """
        Handle corrupt cache file.
        """

        try:

            if file_path.exists():

                file_path.unlink()

        except Exception:
            pass

        self._statistics.corrupt_entries += 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(
        self,
        namespace: str,
        entry: CacheEntry,
    ) -> Path:
        """
        Save cache entry.
        """

        with self._lock:

            self._ensure_namespace(
                namespace
            )

            file_path = (
                self._file_path(
                    namespace,
                    entry.key,
                )
            )

            try:

                file_path.write_text(
                    cache_entry_to_json(
                        entry
                    ),
                    encoding="utf-8",
                )

            except Exception as exc:

                raise (
                    CacheSerializationError(
                        "Failed to "
                        "write cache "
                        "file."
                    )
                ) from exc

            self._statistics.writes += 1

            return file_path

    def load(
        self,
        namespace: str,
        key: str,
    ) -> CacheEntry | None:
        """
        Load cache entry.
        """

        with self._lock:

            file_path = (
                self._file_path(
                    namespace,
                    key,
                )
            )

            if (
                not file_path.exists()
            ):

                self._statistics.misses += 1

                return None

            try:

                entry = (
                    cache_entry_from_json(
                        file_path.read_text(
                            encoding="utf-8"
                        )
                    )
                )

            except Exception:

                self._handle_corruption(
                    file_path
                )

                raise (
                    CacheCorruptionError(
                        "Corrupt cache "
                        "file detected."
                    )
                )

            if (
                cache_entry_is_expired(
                    entry
                )
            ):

                try:

                    file_path.unlink()

                except Exception:
                    pass

                self._statistics.expired_entries += 1

                self._statistics.evictions += 1

                self._statistics.misses += 1

                return None

            self._statistics.hits += 1

            self._statistics.disk_hits += 1

            return entry

    def delete(
        self,
        namespace: str,
        key: str,
    ) -> bool:
        """
        Delete cache file.
        """

        with self._lock:

            file_path = (
                self._file_path(
                    namespace,
                    key,
                )
            )

            if (
                not file_path.exists()
            ):
                return False

            file_path.unlink()

            self._statistics.evictions += 1

            return True

    def exists(
        self,
        namespace: str,
        key: str,
    ) -> bool:
        """
        Check cache file.
        """

        with self._lock:

            file_path = (
                self._file_path(
                    namespace,
                    key,
                )
            )

            if (
                not file_path.exists()
            ):
                return False

            try:

                entry = (
                    cache_entry_from_json(
                        file_path.read_text(
                            encoding="utf-8"
                        )
                    )
                )

            except Exception:

                self._handle_corruption(
                    file_path
                )

                return False

            if (
                cache_entry_is_expired(
                    entry
                )
            ):

                try:

                    file_path.unlink()

                except Exception:
                    pass

                self._statistics.expired_entries += 1

                return False

            return True

    def clear(
        self,
    ) -> int:
        """
        Clear entire cache.
        """

        removed = 0

        with self._lock:

            for file_path in (
                self._cache_directory.rglob(
                    "*.json"
                )
            ):

                try:

                    file_path.unlink()

                    removed += 1

                except Exception:
                    pass

            self._statistics.evictions += (
                removed
            )

        return removed

    def size(
        self,
    ) -> int:
        """
        Count cache files.
        """

        with self._lock:

            return sum(
                1
                for _
                in self._cache_directory.rglob(
                    "*.json"
                )
            )

    def cleanup_expired(
        self,
    ) -> int:
        """
        Remove expired entries.
        """

        removed = 0

        with self._lock:

            for file_path in (
                self._cache_directory.rglob(
                    "*.json"
                )
            ):

                try:

                    entry = (
                        cache_entry_from_json(
                            file_path.read_text(
                                encoding="utf-8"
                            )
                        )
                    )

                except Exception:

                    self._handle_corruption(
                        file_path
                    )

                    removed += 1

                    continue

                if (
                    cache_entry_is_expired(
                        entry
                    )
                ):

                    try:

                        file_path.unlink()

                    except Exception:
                        pass

                    self._statistics.expired_entries += 1

                    self._statistics.evictions += 1

                    removed += 1

        return removed

    def namespaces(
        self,
    ) -> tuple[str, ...]:
        """
        Return namespace list.
        """

        with self._lock:

            names: list[str] = []

            for item in (
                self._cache_directory.iterdir()
            ):

                if item.is_dir():

                    names.append(
                        item.name
                    )

            return tuple(
                sorted(names)
            )

    def statistics(
        self,
    ) -> CacheStatistics:
        """
        Return statistics.
        """

        return self._statistics

    @property
    def cache_directory(
        self,
    ) -> Path:
        """
        Return root cache directory.
        """

        return self._cache_directory


# ============================================================================
# Disk Cache Factory
# ============================================================================


def create_disk_cache(
    cache_directory: Path,
) -> DiskCache:
    """
    Create disk cache.
    """

    return DiskCache(
        cache_directory
    )
# ============================================================================
# Thermochemistry Cache Manager
# ============================================================================


class ThermochemistryCache:
    """
    Unified thermochemistry cache.

    Search Order
    ------------
    Memory Cache

        ↓

    Disk Cache

        ↓

    Cache Miss
    """

    def __init__(
        self,
        cache_directory: Path | None = None,
    ) -> None:

        if cache_directory is None:

            cache_directory = (
                Path.cwd()
                / DEFAULT_CACHE_DIRECTORY
            )

        self._memory = (
            MemoryCache()
        )

        self._disk = (
            DiskCache(
                cache_directory
            )
        )

        self._lock = RLock()

    # ------------------------------------------------------------------
    # Context Manager
    # ------------------------------------------------------------------

    def __enter__(
        self,
    ) -> "ThermochemistryCache":

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> bool:

        return False

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    def get(
        self,
        namespace: str,
        key: str,
    ) -> CacheEntry | None:
        """
        Retrieve cache entry.

        Search order:

        Memory
            ↓
        Disk
            ↓
        Miss
        """

        with self._lock:

            entry = (
                self._memory.get(
                    key
                )
            )

            if entry is not None:

                return entry

            entry = (
                self._disk.load(
                    namespace,
                    key,
                )
            )

            if entry is not None:

                self._memory.set(
                    entry
                )

                return entry

            return None

    def set(
        self,
        namespace: str,
        entry: CacheEntry,
    ) -> None:
        """
        Store entry.
        """

        with self._lock:

            self._memory.set(
                entry
            )

            self._disk.save(
                namespace,
                entry,
            )

    def exists(
        self,
        namespace: str,
        key: str,
    ) -> bool:
        """
        Check existence.
        """

        with self._lock:

            if self._memory.exists(
                key
            ):
                return True

            return (
                self._disk.exists(
                    namespace,
                    key,
                )
            )

    def remove(
        self,
        namespace: str,
        key: str,
    ) -> bool:
        """
        Remove entry.
        """

        removed_memory = (
            self._memory.remove(
                key
            )
        )

        removed_disk = (
            self._disk.delete(
                namespace,
                key,
            )
        )

        return (
            removed_memory
            or removed_disk
        )

    def clear(
        self,
    ) -> None:
        """
        Clear all cache data.
        """

        with self._lock:

            self._memory.clear()

            self._disk.clear()

    def cleanup_expired(
        self,
    ) -> int:
        """
        Remove expired entries.
        """

        removed = 0

        removed += (
            self._memory.cleanup_expired()
        )

        removed += (
            self._disk.cleanup_expired()
        )

        return removed

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def statistics(
        self,
    ) -> dict[str, Any]:
        """
        Unified statistics.
        """

        memory_stats = (
            self._memory.statistics()
        )

        disk_stats = (
            self._disk.statistics()
        )

        return {
            "memory": memory_stats,
            "disk": disk_stats,
            "memory_size": (
                self._memory.size()
            ),
            "disk_size": (
                self._disk.size()
            ),
        }

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def memory_cache(
        self,
    ) -> MemoryCache:
        """
        Return memory cache.
        """

        return self._memory

    @property
    def disk_cache(
        self,
    ) -> DiskCache:
        """
        Return disk cache.
        """

        return self._disk


# ============================================================================
# Global Cache Singleton
# ============================================================================

_GLOBAL_CACHE: (
    ThermochemistryCache
    | None
) = None

_GLOBAL_CACHE_LOCK = (
    RLock()
)


def get_global_cache(
) -> ThermochemistryCache:
    """
    Return global cache.

    Lazy singleton.

    Cache is not created
    during module import.
    """

    global _GLOBAL_CACHE

    with _GLOBAL_CACHE_LOCK:

        if (
            _GLOBAL_CACHE
            is None
        ):

            _GLOBAL_CACHE = (
                ThermochemistryCache()
            )

        return (
            _GLOBAL_CACHE
        )


def reset_global_cache(
) -> None:
    """
    Testing helper.

    Reset singleton.
    """

    global _GLOBAL_CACHE

    with _GLOBAL_CACHE_LOCK:

        _GLOBAL_CACHE = None


# ============================================================================
# Global Alias
# ============================================================================

cache = get_global_cache