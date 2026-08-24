"""Backup and restore of vault originals, manifests, jobs, and local SQLite."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import shutil
import zipfile

__all__ = ("BackupArchive", "backup_workspace_root", "restore_workspace_root")


@dataclass(frozen=True, slots=True, kw_only=True)
class BackupArchive:
    archive_path: Path
    included: tuple[str, ...]


def backup_workspace_root(root: Path, destination: Path) -> BackupArchive:
    root = Path(root)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    included: list[str] = []
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        manifest = {
            "format": "cosmos-workspace-backup-v1",
            "root_name": root.name,
        }
        archive.writestr("backup_manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        included.append("backup_manifest.json")
        for relative in ("knowledge_vault", "jobs", "conversations", "workspace.sqlite"):
            path = root / relative
            if path.is_file():
                archive.write(path, arcname=relative)
                included.append(relative)
            elif path.is_dir():
                for child in path.rglob("*"):
                    if child.is_file():
                        arcname = str(child.relative_to(root))
                        archive.write(child, arcname=arcname)
                        included.append(arcname)
    return BackupArchive(archive_path=destination, included=tuple(included))


def restore_workspace_root(archive_path: Path, destination: Path) -> Path:
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if "backup_manifest.json" not in names:
            raise ValueError("Archive is not a COSMOS workspace backup.")
        archive.extractall(destination)
    return destination
