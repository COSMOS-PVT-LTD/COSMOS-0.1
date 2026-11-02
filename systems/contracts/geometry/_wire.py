"""Bounded, lossless NGG-json-v1 transport; no filesystem/process ownership."""
from __future__ import annotations

import hashlib
import json
import math
import re
import types
from collections.abc import Mapping
from dataclasses import fields
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, ClassVar, Self, Union, get_args, get_origin, get_type_hints
from urllib.parse import unquote, urlparse

SCHEMA_VERSION = "1.0.0"
MAX_WIRE_BYTES = 2 * 1024 * 1024
MAX_COLLECTION = 4096
MAX_DEPTH = 24


class GeometryContractError(ValueError):
    """Stable diagnostic; contract rejection is not a physics/geometry QA result."""

    def __init__(self, code: str, message: str, field: str = "", recovery: str = "Correct the contract and resubmit; no artifact was published.") -> None:
        super().__init__(message)
        self.code, self.field, self.recovery = code, field, recovery

    def diagnostic(self, correlation_id: str) -> dict[str, str]:
        identifier(correlation_id, "correlation_id")
        return {"code": self.code, "message": str(self), "field": self.field,
                "recovery": self.recovery, "correlation_id": correlation_id}


def require(condition: bool, code: str, message: str, field: str = "") -> None:
    if not condition:
        raise GeometryContractError(code, message, field)


def identifier(value: str, field: str) -> None:
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value) is not None,
            "INVALID_IDENTIFIER", "Expected a bounded identifier without whitespace or path segments", field)


def sha(value: str, field: str) -> None:
    require(re.fullmatch(r"[0-9a-f]{64}", value) is not None, "INVALID_HASH", "Expected lowercase SHA256", field)


def positive(value: float, field: str) -> None:
    require(value > 0, "INVALID_POSITIVE", "Expected a positive finite SI value", field)


def utc(value: str, field: str) -> str:
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(instant.tzinfo is not None and instant.utcoffset() == timedelta(0), "INVALID_TIMESTAMP", "Timestamp must declare UTC", field)
        return instant.isoformat(timespec="microseconds")
    except (TypeError, ValueError) as error:
        raise GeometryContractError("INVALID_TIMESTAMP", "Expected an explicit ISO UTC timestamp", field) from error


def relative_path(value: str, field: str) -> None:
    require(re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", value) is not None
            and all(part not in {".", ".."} for part in value.split("/")) and len(value) <= 512,
            "UNSAFE_PATH", "Artifact URI must be a bounded relative POSIX path, without traversal/encoding", field)


def source_uri(value: str) -> None:
    require(bool(value) and value == value.strip() and len(value) <= 1024 and not any(ord(c) <= 32 for c in value) and "\\" not in value,
            "UNSAFE_SOURCE", "Source URI contains invalid characters", "source_uri")
    try:
        parsed = urlparse(value)
        # Parsing/reading a malformed host must produce the same typed rejection
        # as other source-reference violations. References are never fetched here.
        host = parsed.hostname
        _ = parsed.port  # Reject malformed/out-of-range ports without any network IO.
    except ValueError as error:
        raise GeometryContractError("UNSAFE_SOURCE", "Malformed source reference host", "source_uri") from error
    if parsed.scheme:
        require(parsed.scheme == "https" and bool(host) and not parsed.username and not parsed.password,
                "UNSAFE_SOURCE", "Only HTTPS or relative source references are allowed", "source_uri")
    else:
        require(not parsed.netloc and not value.startswith("/"), "UNSAFE_SOURCE", "Relative source references cannot select a host/root", "source_uri")
    require(all(p not in {".", ".."} for p in unquote(parsed.path).split("/")), "UNSAFE_SOURCE", "Source reference traversal rejected", "source_uri")


def unique(values: tuple[str, ...], field: str, *, nonempty: bool = True) -> None:
    require((bool(values) or not nonempty) and len(set(values)) == len(values), "DUPLICATE_OR_EMPTY", "Expected unique identifiers", field)
    for value in values:
        identifier(value, field)


def encode(value: object) -> Any:
    if isinstance(value, WireContract):
        return value.to_canonical_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [encode(item) for item in value]
    return value


def dumps(value: Mapping[str, object]) -> str:
    # Do not use Core's 16-significant-digit normalization for new geometry data.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=True)


def digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(dumps(value).encode("utf-8")).hexdigest()


_HINTS: dict[type, dict[str, Any]] = {}


def hints(cls: type) -> dict[str, Any]:
    if cls not in _HINTS:
        _HINTS[cls] = get_type_hints(cls)
    return _HINTS[cls]


def coerce(value: object, annotation: Any, field: str, *, wire: bool = False, depth: int = 0) -> Any:
    require(depth <= MAX_DEPTH, "CONTRACT_LIMIT", "Contract nesting limit exceeded", field)
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, types.UnionType):
        if value is None and type(None) in args:
            return None
        candidates = tuple(candidate for candidate in args if candidate is not type(None))
        if len(candidates) == 1:
            return coerce(value, candidates[0], field, wire=wire, depth=depth + 1)
        for candidate in candidates:
            if candidate is not type(None):
                try:
                    return coerce(value, candidate, field, wire=wire, depth=depth + 1)
                except GeometryContractError:
                    pass
        raise GeometryContractError("INVALID_TYPE", "Value is not an allowed optional type", field)
    if origin is tuple:
        require(isinstance(value, (tuple, list)) and len(value) <= MAX_COLLECTION, "CONTRACT_LIMIT", "Expected a bounded array", field)
        assert isinstance(value, (tuple, list))
        require(len(args) == 2 and args[1] is Ellipsis, "INVALID_TYPE", "Unsupported tuple schema", field)
        return tuple(coerce(item, args[0], field, wire=wire, depth=depth + 1) for item in value)
    if annotation is str:
        require(type(value) is str and len(value) <= 2048, "INVALID_TYPE", "Expected a bounded string", field)
        return value
    if annotation is bool:
        require(type(value) is bool, "INVALID_TYPE", "Expected a Boolean", field)
        return value
    if annotation is int:
        require(type(value) is int, "INVALID_TYPE", "Expected an integer, not a Boolean", field)
        return value
    if annotation is float:
        require(type(value) in (int, float), "INVALID_TYPE", "Expected a number, not a Boolean/string", field)
        try:
            number = float(value)  # type: ignore[arg-type]
        except OverflowError as error:
            raise GeometryContractError("NONFINITE", "Numeric conversion overflow", field) from error
        require(math.isfinite(number), "NONFINITE", "Expected finite SI numbers", field)
        return number
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        try:
            require(isinstance(value, (str, annotation)), "INVALID_ENUM", "Expected a supported enum", field)
            return annotation(value)
        except ValueError as error:
            raise GeometryContractError("INVALID_ENUM", "Unsupported enum value", field) from error
    if isinstance(annotation, type) and issubclass(annotation, WireContract):
        if wire:
            require(isinstance(value, dict), "INVALID_TYPE", "Expected a contract object", field)
            assert isinstance(value, dict)
            return annotation._decode(value, depth + 1)
        require(type(value) is annotation, "INVALID_TYPE", "Expected the typed immutable contract", field)
        return value
    raise GeometryContractError("INVALID_TYPE", "Unsupported contract annotation", field)


class WireContract:
    """CanonicalSerializable-compatible interface, separate lossless NGG wire profile."""
    __slots__ = ()
    schema_version: ClassVar[str] = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in fields(self):  # type: ignore[arg-type]
            object.__setattr__(self, item.name, coerce(getattr(self, item.name), hints(type(self))[item.name], item.name))

    def _payload(self) -> dict[str, object]:
        return {"schema_version": SCHEMA_VERSION, "contract_type": type(self).__name__,
                **{f.name: encode(getattr(self, f.name)) for f in fields(self)}}  # type: ignore[arg-type]

    @property
    def content_sha256(self) -> str:
        return digest(self._payload())

    def to_canonical_dict(self) -> dict[str, object]:
        payload = self._payload()
        return {**payload, "content_sha256": digest(payload)}

    def to_json(self) -> str:
        text = dumps(self.to_canonical_dict())
        require(len(text.encode("utf-8")) <= MAX_WIRE_BYTES, "CONTRACT_LIMIT", "Serialized contract exceeds wire byte limit")
        return text

    @classmethod
    def _decode(cls, value: dict[str, Any], depth: int = 0) -> Self:
        names = {f.name for f in fields(cls)}  # type: ignore[arg-type]
        require(set(value) == names | {"schema_version", "contract_type", "content_sha256"}, "INVALID_FIELDS", "Unknown or missing contract fields")
        require(value["schema_version"] == SCHEMA_VERSION, "SCHEMA_VERSION", "Unsupported geometry schema version")
        require(value["contract_type"] == cls.__name__, "CONTRACT_TYPE", "Incorrect contract type")
        values = {name: coerce(value[name], hints(cls)[name], name, wire=True, depth=depth) for name in names}
        instance = cls(**values)
        require(value["content_sha256"] == instance.content_sha256, "HASH_MISMATCH", "Contract content checksum mismatch")
        return instance

    @classmethod
    def from_canonical_dict(cls, data: dict[str, Any]) -> Self:
        try:
            return cls.from_json(dumps(data))
        except GeometryContractError:
            raise
        except (TypeError, ValueError, RecursionError) as error:
            raise GeometryContractError("INVALID_JSON", "Canonical data is not finite JSON") from error

    @classmethod
    def from_json(cls, text: str) -> Self:
        require(type(text) is str and len(text.encode("utf-8")) <= MAX_WIRE_BYTES, "CONTRACT_LIMIT", "Expected bounded JSON text")
        def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
            require(len(items) <= MAX_COLLECTION, "CONTRACT_LIMIT", "Object key limit exceeded")
            result: dict[str, Any] = {}
            for key, value in items:
                require(key not in result, "DUPLICATE_KEY", "Duplicate JSON key rejected", key)
                result[key] = value
            return result
        try:
            data = json.loads(text, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(GeometryContractError("NONFINITE", "Nonfinite JSON constant rejected")))
            require(isinstance(data, dict), "INVALID_TYPE", "Expected a JSON contract object")
            return cls._decode(data)
        except GeometryContractError:
            raise
        except (ValueError, TypeError, RecursionError, OverflowError) as error:
            raise GeometryContractError("INVALID_JSON", "Malformed or excessively nested JSON") from error
