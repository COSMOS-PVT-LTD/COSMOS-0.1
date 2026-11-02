"""Propulsion design persistence — dedicated store, not knowledge vault."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from pathlib import Path

from core.exceptions import InvalidInputError
from core.serialization import canonical_json_dumps
from systems.projects.authority import AccessDenied
from systems.projects.models import PropulsionDesign

__all__ = ("DesignStore",)


class ManagedDesignAccess(AccessDenied):
    """Use an authenticated project/CAS route, never an unscoped legacy route."""


class DesignStore:
    """
    JSON-file design store under an application-owned root directory.

    Authoritative engineering state — not browser localStorage, not knowledge vault.
    Writes are atomic (temp file + replace) and serialized with a process lock.
    """

    def __init__(self, root: Path | str, *, access_guard: Callable[[str | None], bool] | None = None) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.access_guard = access_guard

    def check_access(self, design_id: str | None = None) -> None:
        namespace = self.root.parent / "engineering_state"
        required = (namespace / "authority.required").exists() or (namespace / "authority.required").is_symlink() or (namespace / "v1").exists() or (namespace / "v1").is_symlink()
        if required and self.access_guard is None:
            raise AccessDenied("Engineering authority context is required; legacy access fails closed.")
        if self.access_guard is not None and self.access_guard(design_id):
            raise ManagedDesignAccess("Managed design requires an authenticated project and expected head.")

    def _path_for(self, design_id: str) -> Path:
        safe = design_id.replace("/", "_").replace("..", "_")
        return self.root / f"{safe}.json"

    def save(self, design: PropulsionDesign) -> Path:
        self.check_access(design.design_id)
        path = self._path_for(design.design_id)
        payload = design.to_canonical_dict()
        text = canonical_json_dumps(payload) + "\n"
        tmp = path.with_suffix(".json.tmp")
        with self._lock:
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(path)
        return path

    def load(self, design_id: str) -> PropulsionDesign:
        self.check_access(design_id)
        path = self._path_for(design_id)
        if not path.is_file():
            raise InvalidInputError(f"Design not found: {design_id!r}.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise InvalidInputError("Design file must contain a JSON object.")
        return PropulsionDesign.from_canonical_dict(data)

    def list_design_ids(self) -> tuple[str, ...]:
        self.check_access()
        ids = sorted(path.stem for path in self.root.glob("*.json") if path.suffix == ".json")
        allowed = []
        for design_id in ids:
            try:
                self.check_access(design_id)
            except ManagedDesignAccess:
                continue
            allowed.append(design_id)
        return tuple(allowed)

    def list_summaries(self) -> list[dict[str, object]]:
        """Return design list rows sorted by updated_at descending."""

        items: list[dict[str, object]] = []
        for design_id in self.list_design_ids():
            try:
                design = self.load(design_id)
            except (InvalidInputError, ValueError, TypeError, KeyError):
                continue
            items.append(
                {
                    "design_id": design.design_id,
                    "name": design.name,
                    "revision": design.revision,
                    "updated_at": design.updated_at,
                    "state": design.status.value,
                    "engineer": design.engineer,
                }
            )
        items.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
        return items

    def exists(self, design_id: str) -> bool:
        self.check_access(design_id)
        return self._path_for(design_id).is_file()
