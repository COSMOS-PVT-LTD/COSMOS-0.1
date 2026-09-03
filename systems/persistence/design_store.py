"""Propulsion design persistence — dedicated store, not knowledge vault."""

from __future__ import annotations

import json
from pathlib import Path

from core.exceptions import InvalidInputError
from core.serialization import canonical_json_dumps

from systems.projects.models import PropulsionDesign

__all__ = ("DesignStore",)


class DesignStore:
    """
    JSON-file design store under an application-owned root directory.

    Authoritative engineering state — not browser localStorage, not knowledge vault.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, design_id: str) -> Path:
        safe = design_id.replace("/", "_").replace("..", "_")
        return self.root / f"{safe}.json"

    def save(self, design: PropulsionDesign) -> Path:
        path = self._path_for(design.design_id)
        payload = design.to_canonical_dict()
        text = canonical_json_dumps(payload)
        path.write_text(text + "\n", encoding="utf-8")
        return path

    def load(self, design_id: str) -> PropulsionDesign:
        path = self._path_for(design_id)
        if not path.is_file():
            raise InvalidInputError(f"Design not found: {design_id!r}.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise InvalidInputError("Design file must contain a JSON object.")
        return PropulsionDesign.from_canonical_dict(data)

    def list_design_ids(self) -> tuple[str, ...]:
        ids = sorted(path.stem for path in self.root.glob("*.json"))
        return tuple(ids)

    def exists(self, design_id: str) -> bool:
        return self._path_for(design_id).is_file()
