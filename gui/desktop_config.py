"""Explicit desktop workspace registrations, not migration or discovery."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

FLAGS = (
    "COSMOS_NEW_SHELL",
    "COSMOS_DURABLE_PROJECTS",
    "COSMOS_NGG",
    "COSMOS_NEW_SIM_UI",
    "COSMOS_NEW_VV_UI",
    "COSMOS_NEW_KNOWLEDGE_REPORTS_UI",
)
RUNTIMES = ("COSMOS_NGG_RUNTIME_CONFIG", "COSMOS_PICOGK_COMPONENT_CONFIG")


@dataclass(frozen=True)
class Workspace:
    key: str
    label: str
    root: Path


def existing_root(root: Path) -> Path:
    root = root.expanduser().absolute()
    if not root.is_dir() or not (root / "auth/users.sqlite").is_file():
        raise ValueError(
            "Select an existing COSMOS app-data folder containing auth/users.sqlite. Nothing was initialized or migrated."
        )
    return root.resolve()


def read_profile(path: Path):
    value = json.loads(path.read_text())
    if value.get("schema") != "cosmos.desktop-profile.v1" or not value.get(
        "workspaces"
    ):
        raise ValueError("An explicit registered desktop workspace profile is required")
    workspaces = []
    for row in value["workspaces"]:
        if set(row) != {"key", "label", "root"} or not all(
            type(v) is str and v for v in row.values()
        ):
            raise ValueError("Invalid desktop workspace registration")
        if (
            not Path(row["root"]).is_absolute()
            or not row["key"].replace("-", "").isalnum()
        ):
            raise ValueError("Workspace identifiers and absolute data roots required")
        workspaces.append(Workspace(row["key"], row["label"], Path(row["root"])))
    if len({w.key for w in workspaces}) != len(workspaces):
        raise ValueError("Duplicate desktop workspace identifier")
    runtimes = value.get("runtimes", {})
    if set(runtimes) != set(RUNTIMES):
        raise ValueError("Both explicit CAD runtime profiles required")
    resolved = {}
    for name, relative in runtimes.items():
        if type(relative) is not str or Path(relative).is_absolute():
            raise ValueError("Runtime paths must be bundle-relative")
        target = (path.parent / relative).resolve()
        if not target.is_relative_to(path.parent.resolve()) or not target.is_file():
            raise ValueError("Runtime profile missing or outside the bundle")
        resolved[name] = str(target)
    return workspaces, resolved


def enable_workspaces(runtimes):
    for flag in FLAGS:
        os.environ[flag] = "1"
    os.environ.update(runtimes)
    os.environ.pop("COSMOS_RELEASE_PROFILE", None)
