"""Repository ingestion adapter (NEW KG-013)."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path

from knowledge.ingestion.models import SourceFormat
from knowledge.ingestion_adapters.exceptions import (
    AdapterValidationError,
    RepositoryBoundaryError,
)
from knowledge.source.integrity import sha256_bytes_digest
from knowledge.source.vault import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata

__all__ = (
    "RepositoryIngestionAdapter",
    "RepositoryIngestionConfig",
    "RepositoryIngestionResult",
)

_DEFAULT_EXCLUDES = (
    ".env",
    ".env.*",
    "*credentials*",
    "*secret*",
    "*.pem",
    "*.key",
)


def _is_within_root(path: Path, root: Path) -> bool:
    """Return True when path resolves inside root (no prefix-collision bypass)."""

    try:
        path.relative_to(root)
    except ValueError:
        return False

    return True


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise AdapterValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise AdapterValidationError(f"{field_name} must not be blank.")

    return cleaned


@dataclass(frozen=True, slots=True, kw_only=True)
class RepositoryIngestionConfig:
    """Bounded configuration for repository ingestion."""

    root_path: str
    source_id: str
    include_globs: tuple[str, ...] = ("*",)
    exclude_globs: tuple[str, ...] = _DEFAULT_EXCLUDES
    max_files: int = 1000

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "root_path",
            _validate_non_empty_string("root_path", self.root_path),
        )
        object.__setattr__(
            self,
            "source_id",
            _validate_non_empty_string("source_id", self.source_id),
        )

        if not isinstance(self.max_files, int) or isinstance(self.max_files, bool):
            raise AdapterValidationError("max_files must be an integer.")

        if self.max_files <= 0:
            raise AdapterValidationError("max_files must be positive.")


@dataclass(frozen=True, slots=True, kw_only=True)
class RepositoryIngestionResult:
    """Deterministic repository ingestion summary."""

    source_id: str
    root_path: str
    artifact_ids: tuple[str, ...]
    file_count: int

    def to_mapping(self) -> dict[str, object]:
        return {
            "artifact_ids": list(self.artifact_ids),
            "file_count": self.file_count,
            "root_path": self.root_path,
            "source_id": self.source_id,
        }


def _source_format_for_suffix(suffix: str) -> SourceFormat | None:
    mapping = {
        ".pdf": SourceFormat.PDF,
        ".docx": SourceFormat.DOCX,
        ".pptx": SourceFormat.PPTX,
        ".xlsx": SourceFormat.XLSX,
        ".html": SourceFormat.HTML,
        ".htm": SourceFormat.HTML,
        ".md": SourceFormat.MARKDOWN,
        ".markdown": SourceFormat.MARKDOWN,
    }

    return mapping.get(suffix.lower())


class RepositoryIngestionAdapter:
    """
    Bounded local repository ingestion.

    Enumerates files deterministically and stores supported artifacts in the vault.
    Does not execute code or fetch network resources.
    """

    adapter_name = "cosmos-repository-ingestion"
    adapter_version = "0.1.0"

    def __init__(
        self,
        vault: InMemorySourceVault,
        config: RepositoryIngestionConfig,
    ) -> None:
        self._vault = vault
        self._config = config
        self._root = Path(config.root_path).resolve()

    def ingest_repository(self) -> RepositoryIngestionResult:
        if not self._root.is_dir():
            raise RepositoryBoundaryError(
                "Repository root path does not exist or is not a directory."
            )

        files = self._enumerate_files()
        artifact_ids: list[str] = []

        for relative_path in files:
            absolute_path = (self._root / relative_path).resolve()

            if not _is_within_root(absolute_path, self._root):
                raise RepositoryBoundaryError(
                    "Repository path escaped configured root boundary."
                )

            content = absolute_path.read_bytes()
            content_hash = sha256_bytes_digest(content)
            artifact_id = relative_path.as_posix()
            source_format = _source_format_for_suffix(absolute_path.suffix)

            metadata = VaultArtifactMetadata(
                source_format=(
                    source_format.value if source_format is not None else None
                ),
                media_type=absolute_path.suffix.lower() or None,
            )

            self._vault.store(
                VaultArtifact(
                    source_id=self._config.source_id,
                    artifact_id=artifact_id,
                    content=content,
                    content_hash=content_hash,
                    metadata=metadata,
                ),
            )
            artifact_ids.append(artifact_id)

        return RepositoryIngestionResult(
            source_id=self._config.source_id,
            root_path=str(self._root),
            artifact_ids=tuple(sorted(artifact_ids)),
            file_count=len(artifact_ids),
        )

    def _enumerate_files(self) -> tuple[Path, ...]:
        discovered: list[Path] = []

        for path in sorted(self._root.rglob("*")):
            if not path.is_file():
                continue

            relative = path.relative_to(self._root)

            if self._is_excluded(relative.as_posix()):
                continue

            if not self._is_included(relative.as_posix()):
                continue

            discovered.append(relative)

            if len(discovered) > self._config.max_files:
                raise RepositoryBoundaryError(
                    "Repository ingestion exceeded configured max_files bound."
                )

        return tuple(discovered)

    def _is_excluded(self, relative_path: str) -> bool:
        name = Path(relative_path).name

        return any(
            fnmatch.fnmatch(name, pattern)
            or fnmatch.fnmatch(relative_path, pattern)
            for pattern in self._config.exclude_globs
        )

    def _is_included(self, relative_path: str) -> bool:
        return any(
            fnmatch.fnmatch(relative_path, pattern)
            for pattern in self._config.include_globs
        )
