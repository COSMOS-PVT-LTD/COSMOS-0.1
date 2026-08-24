"""Durable artifact vault. Directory layout is not the source of truth."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import shutil

from knowledge.source.exceptions import IntegrityMismatchError, IntegrityValidationError
from knowledge.source.integrity import sha256_bytes_digest, verify_digest
from knowledge.workspace.models import SourceRecord

__all__ = ("DurableArtifactVault", "VaultError")


class VaultError(RuntimeError):
    """Artifact vault operation failed."""


class DurableArtifactVault:
    """Store originals and derivatives on disk or in memory."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root is not None else None
        self._memory_originals: dict[str, bytes] = {}
        self._memory_derivatives: dict[tuple[str, str], bytes] = {}
        self._records: dict[str, SourceRecord] = {}
        if self.root is not None:
            for name in (
                "originals",
                "derivatives",
                "page_images",
                "ocr",
                "equations",
                "extracted",
                "datasets",
                "manifests",
            ):
                (self.root / name).mkdir(parents=True, exist_ok=True)
            self._load_manifests()

    def store_original(self, record: SourceRecord, content: bytes) -> SourceRecord:
        digest = sha256_bytes_digest(content)
        if digest != record.sha256:
            raise VaultError("Record sha256 does not match content.")
        uri = self._original_uri(record.source_id, digest)
        stored = replace(record, storage_uri=uri, integrity_status="VERIFIED")
        if self.root is None:
            self._memory_originals[record.source_id] = content
        else:
            path = self._original_path(record.source_id, digest)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                existing = path.read_bytes()
                verify_digest(existing, digest)
            else:
                path.write_bytes(content)
            self._write_manifest(stored)
        self._records[stored.source_id] = stored
        return stored

    def retrieve_original(self, source_id: str) -> bytes:
        record = self.get(source_id)
        if self.root is None:
            try:
                return self._memory_originals[source_id]
            except KeyError as exc:
                raise VaultError(f"Original for '{source_id}' was not found.") from exc
        path = Path(record.storage_uri)
        if not path.is_file():
            raise VaultError(f"Original for '{source_id}' was not found.")
        content = path.read_bytes()
        verify_digest(content, record.sha256)
        return content

    def store_derivative(self, source_id: str, kind: str, content: bytes) -> str:
        digest = sha256_bytes_digest(content)
        if self.root is None:
            self._memory_derivatives[(source_id, kind)] = content
            return f"memory://{kind}/{source_id}/{digest}"
        path = self.root / "derivatives" / source_id / kind
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def retrieve_derivative(self, source_id: str, kind: str) -> bytes:
        if self.root is None:
            try:
                return self._memory_derivatives[(source_id, kind)]
            except KeyError as exc:
                raise VaultError(f"Derivative '{kind}' for '{source_id}' was not found.") from exc
        path = self.root / "derivatives" / source_id / kind
        if not path.is_file():
            raise VaultError(f"Derivative '{kind}' for '{source_id}' was not found.")
        return path.read_bytes()

    def delete_derivative(self, source_id: str, kind: str) -> None:
        self._memory_derivatives.pop((source_id, kind), None)
        if self.root is None:
            return
        path = self.root / "derivatives" / source_id / kind
        if path.is_file():
            path.unlink()

    def get(self, source_id: str) -> SourceRecord:
        try:
            return self._records[source_id]
        except KeyError as exc:
            raise VaultError(f"Source '{source_id}' was not found.") from exc

    def find_by_hash(self, sha256: str) -> tuple[SourceRecord, ...]:
        return tuple(item for item in self._records.values() if item.sha256 == sha256)

    def find_by_filename(self, filename: str) -> tuple[SourceRecord, ...]:
        return tuple(item for item in self._records.values() if item.filename == filename)

    def list_sources(self) -> tuple[SourceRecord, ...]:
        return tuple(sorted(self._records.values(), key=lambda item: item.ingested_at))

    def update_record(self, record: SourceRecord) -> SourceRecord:
        self._records[record.source_id] = record
        if self.root is not None:
            self._write_manifest(record)
        return record

    def verify(self, source_id: str) -> bool:
        record = self.get(source_id)
        try:
            content = self.retrieve_original(source_id)
            verify_digest(content, record.sha256)
        except (VaultError, IntegrityMismatchError, IntegrityValidationError):
            return False
        return True

    def delete_source(self, source_id: str) -> None:
        record = self.get(source_id)
        self._records.pop(source_id, None)
        self._memory_originals.pop(source_id, None)
        keys = [key for key in self._memory_derivatives if key[0] == source_id]
        for key in keys:
            self._memory_derivatives.pop(key, None)
        if self.root is None:
            return
        manifest = self.root / "manifests" / f"{source_id}.json"
        if manifest.is_file():
            manifest.unlink()
        original_dir = self.root / "originals" / source_id
        if original_dir.is_dir():
            shutil.rmtree(original_dir, ignore_errors=True)
        derivative_dir = self.root / "derivatives" / source_id
        if derivative_dir.is_dir():
            shutil.rmtree(derivative_dir, ignore_errors=True)
        for folder in ("page_images", "ocr", "equations", "extracted", "datasets"):
            extra = self.root / folder / source_id
            if extra.is_dir():
                shutil.rmtree(extra, ignore_errors=True)
        del record

    def export_tree(self, destination: Path) -> None:
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        if self.root is not None:
            if destination.resolve() != self.root.resolve():
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(self.root, destination)
            return
        originals = destination / "originals"
        manifests = destination / "manifests"
        originals.mkdir(parents=True, exist_ok=True)
        manifests.mkdir(parents=True, exist_ok=True)
        for record in self._records.values():
            content = self._memory_originals[record.source_id]
            path = originals / record.source_id / record.sha256
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            (manifests / f"{record.source_id}.json").write_text(
                json.dumps(record.to_mapping(), indent=2, sort_keys=True),
                encoding="utf-8",
            )

    def _original_uri(self, source_id: str, digest: str) -> str:
        if self.root is None:
            return f"memory://originals/{source_id}/{digest}"
        return str(self._original_path(source_id, digest))

    def _original_path(self, source_id: str, digest: str) -> Path:
        if self.root is None:
            raise VaultError("In-memory vault has no filesystem path.")
        return self.root / "originals" / source_id / digest

    def _write_manifest(self, record: SourceRecord) -> None:
        if self.root is None:
            return
        path = self.root / "manifests" / f"{record.source_id}.json"
        path.write_text(json.dumps(record.to_mapping(), indent=2, sort_keys=True), encoding="utf-8")

    def _load_manifests(self) -> None:
        if self.root is None:
            return
        directory = self.root / "manifests"
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            record = SourceRecord.from_mapping(payload)
            self._records[record.source_id] = record
