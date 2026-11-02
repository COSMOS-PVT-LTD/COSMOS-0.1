"""Typed project repository boundary and exact-byte scientific record envelope."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from core.exceptions import SerializationError
from core.serialization import canonical_json_dumps
from systems.projects.authority import (
    Head,
    InvalidRecord,
    Lifecycle,
    Membership,
    ObjectHead,
    Principal,
    Project,
    SavedSnapshot,
    StoragePolicy,
    identity,
)
from systems.projects.models import PropulsionDesign


def _bounded_json(
    value: object, *, depth: int = 0, budget: list[int] | None = None
) -> None:
    remaining = [200_000, 16 * 1024 * 1024] if budget is None else budget
    remaining[0] -= 1
    if remaining[0] < 0 or depth > 48:
        raise InvalidRecord("Record exceeds JSON structure budget.")
    if isinstance(value, str):
        try:
            # Count keys/values before Core encoding, rejecting oversized or
            # ill-formed mappings instead of allocating an unbounded JSON copy.
            remaining[1] -= len(value.encode("utf-8"))
        except UnicodeError as exc:
            raise InvalidRecord("Invalid Unicode in record.") from exc
        if remaining[1] < 0:
            raise InvalidRecord("Record exceeds string budget.")
        return
    if value is None or isinstance(value, bool):
        return
    if type(value) is int:
        if value.bit_length() > 256:
            raise InvalidRecord("Integer exceeds record budget.")
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise InvalidRecord("Nonfinite values are not scientific evidence.")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise InvalidRecord("Record keys must be strings.")
            _bounded_json(key, depth=depth + 1, budget=remaining)
            _bounded_json(item, depth=depth + 1, budget=remaining)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _bounded_json(item, depth=depth + 1, budget=remaining)
        return
    raise InvalidRecord("Record contains an unsupported value.")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidRecord("Ambiguous duplicate JSON key.")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class RecordPayload:
    """Unmodified accepted source bytes, with a separate storage digest.

    ``from_mapping`` deliberately reuses Core's existing canonical contract.
    Direct byte construction never normalizes another domain's canonical text.
    Domain-specific validity/hashes remain the domain adapter's responsibility.
    """

    data: bytes
    schema_id: str
    source_namespace: str = ""

    @property
    def content_hash(self) -> str:
        return sha256(self.data).hexdigest()

    def validate(self, policy: StoragePolicy) -> None:
        identity(self.schema_id, "schema ID")
        if not isinstance(self.source_namespace, str):
            raise InvalidRecord("Source namespace must be text.")
        if self.source_namespace:
            identity(self.source_namespace, "source namespace")
        if type(self.data) is not bytes or len(self.data) > min(
            policy.record_bytes, policy.blob_bytes
        ):
            raise InvalidRecord("Record exceeds byte budget or is not immutable bytes.")
        try:
            parsed = json.loads(
                self.data.decode("utf-8"), object_pairs_hook=_unique_pairs
            )
            if not isinstance(parsed, dict):
                raise InvalidRecord("A record must be a JSON object.")
            _bounded_json(parsed, budget=[200_000, policy.record_bytes])
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise InvalidRecord("Invalid bounded UTF-8 JSON record.") from exc

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, object], schema_id: str, *, source_namespace: str = ""
    ) -> RecordPayload:
        _bounded_json(value)
        try:
            encoded = canonical_json_dumps(value).encode("utf-8")
        except (
            ValueError,
            TypeError,
            RecursionError,
            UnicodeError,
            SerializationError,
        ) as exc:
            raise InvalidRecord("Record cannot be canonically serialized.") from exc
        return cls(encoded, schema_id, source_namespace)

    @classmethod
    def from_design(cls, design: PropulsionDesign) -> RecordPayload:
        return cls.from_mapping(
            design.to_canonical_dict(), "cosmos.propulsion-design.v1"
        )


@dataclass(frozen=True, slots=True)
class Dependency:
    relation: str
    commit_id: str
    job_id: str | None = None

    def __post_init__(self) -> None:
        identity(self.relation, "dependency relation")
        identity(self.commit_id, "dependency commit")
        if self.job_id is not None:
            identity(self.job_id, "dependency attempt")


class ProjectRepository(Protocol):
    """IO implementation belongs in Infrastructure; callers supply trusted actors."""

    def create_project(
        self, actor: Principal, *, title: str, mission: str = "", operation_id: str
    ) -> Project: ...

    def get_project(self, actor: Principal, project_id: str) -> Project: ...

    def list_projects(
        self,
        actor: Principal,
        *,
        limit: int = 50,
        after_id: str = "",
    ) -> tuple[Project, ...]: ...

    def change_project(
        self,
        actor: Principal,
        project_id: str,
        *,
        expected: Head,
        operation_id: str,
        title: str | None = None,
        mission: str | None = None,
        lifecycle: Lifecycle | None = None,
        confirmation_project_id: str | None = None,
    ) -> Project: ...

    def set_member(
        self,
        actor: Principal,
        project_id: str,
        *,
        member: Principal,
        capability: Membership | None,
        expected: Head,
        operation_id: str,
    ) -> Project: ...

    def save_snapshot(
        self,
        actor: Principal,
        project_id: str,
        *,
        domain: str,
        object_id: str,
        input_revision: int,
        payload: RecordPayload,
        expected: Head,
        operation_id: str,
        command_hash: str | None = None,
        purpose: str = "save",
        source_commit_id: str | None = None,
        input_commit_id: str | None = None,
        retain_if_stale: bool = False,
        response_payload: bytes | None = None,
        dependencies: tuple[Dependency, ...] = (),
    ) -> SavedSnapshot: ...

    @property
    def supports_dependencies(self) -> bool: ...

    def dependencies(self, actor: Principal, project_id: str, commit_id: str) -> tuple[Dependency, ...]: ...

    def dependencies_current(self, actor: Principal, project_id: str, commit_id: str) -> bool: ...

    def resolve_snapshot(self, actor: Principal, project_id: str, commit_id: str) -> SavedSnapshot: ...

    def list_domains(self, actor: Principal, project_id: str, *, limit: int = 20, after: str = "") -> tuple[str, ...]: ...

    def project_events(self, actor: Principal, project_id: str, *, limit: int = 20, before: int | None = None) -> tuple[dict[str, object], ...]: ...

    def resolve_command(
        self, actor: Principal, project_id: str, *, operation_id: str, command_hash: str
    ) -> SavedSnapshot | None: ...

    def list_objects(
        self,
        actor: Principal,
        project_id: str,
        *,
        domain: str,
        limit: int = 20,
        after_id: str = "",
    ) -> tuple[ObjectHead, ...]: ...

    def get_snapshot(
        self,
        actor: Principal,
        project_id: str,
        *,
        domain: str,
        object_id: str,
        commit_id: str | None = None,
    ) -> SavedSnapshot: ...

    def list_commit_ids(
        self,
        actor: Principal,
        project_id: str,
        *,
        domain: str,
        object_id: str,
        limit: int = 50,
        before_version: int | None = None,
    ) -> tuple[str, ...]: ...
