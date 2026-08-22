import os
import sys
from pathlib import Path

root_path = Path(__file__).resolve().parents[3]
src_path = root_path / 'src'

sys.path.insert(0, str(src_path))
sys.path.insert(0, str(root_path))

from knowledge.models.reference import (
    Reference,
    ReferenceType,
)
from knowledge.models.document import (
    Document,
    DocumentType,
)

def test_repository_fields_round_trip() -> None:

    document = Document(
        document_id="doc-1",
        document_version_id="v1",
        title="Sample Document",
        content="This is sample content.",
        document_type=DocumentType.MANUAL,
        reference=Reference(
            reference_id="ref-1",
            title="Example Reference",
            authors=(
                "Example Author",
            ),
            reference_type=getattr(ReferenceType, "WEBSITE"),
            url="https://example.com",
        ),
        chapter="Chapter 1",
        section="Section A",
        tags=(
            "rocket",
            "propulsion",
        ),
        metadata={
            "author":
            "NASA",
        },
    )

    payload = (
        document.to_dict()
    )

    restored = (
        Document.from_dict(
            payload
        )
    )

    assert (
        restored.chapter
        == "Chapter 1"
    )

    assert (
        restored.section
        == "Section A"
    )

    assert (
        restored.tags
        == (
            "rocket",
            "propulsion",
        )
    )

    assert (
        restored.metadata[
            "author"
        ]
        == "NASA"
    )