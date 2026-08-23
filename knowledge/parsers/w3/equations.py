"""
Equation parsing (NEW KG-017).

Identifies equation text only — no engineering semantics or execution.
"""

from __future__ import annotations

import re

from knowledge.parsers.w3.exceptions import ParserEquationError
from knowledge.parsers.w3.identity import deterministic_element_id
from knowledge.parsers.w3.models import LocationAnchor, ParsedEquation, ParseProvenance

__all__ = (
    "extract_equations",
)

_BLOCK_EQUATION_PATTERN = re.compile(
    r"\$\$(?P<content>.+?)\$\$",
    re.DOTALL,
)
_INLINE_EQUATION_PATTERN = re.compile(
    r"(?<!\$)\$(?P<content>(?:\\.|[^$\\])+)\$(?!\$)",
)
_VARIABLE_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*")


def _base_provenance(
    *,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    document_id: str,
    parser_name: str,
    parser_version: str,
    location: LocationAnchor | None,
) -> ParseProvenance:
    return ParseProvenance(
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        document_id=document_id,
        location=location,
        parser_name=parser_name,
        parser_version=parser_version,
    )


def _reject_dangerous_equation_text(text: str) -> None:
    lowered = text.lower()

    for token in ("__import__", "eval(", "exec(", "os.system", "${"):
        if token in lowered:
            raise ParserEquationError(
                "Equation text contains disallowed executable patterns."
            )


def _extract_variables(text: str) -> tuple[str, ...]:
    return tuple(sorted({match.group(0) for match in _VARIABLE_PATTERN.finditer(text)}))


def extract_equations(
    *,
    content: str,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
) -> tuple[ParsedEquation, ...]:
    """Extract equations from markdown-like normalized content."""

    equations: list[ParsedEquation] = []
    ordering_index = 0

    for line_number, line in enumerate(content.splitlines(), start=1):
        for pattern in (_BLOCK_EQUATION_PATTERN, _INLINE_EQUATION_PATTERN):
            for match_index, match in enumerate(pattern.finditer(line)):
                normalized_text = match.group("content").strip()
                _reject_dangerous_equation_text(normalized_text)

                ordering_index += 1
                equation_id = deterministic_element_id(
                    "eq",
                    document_id,
                    str(line_number),
                    str(match_index),
                    normalized_text,
                )
                equations.append(
                    ParsedEquation(
                        equation_id=equation_id,
                        normalized_text=normalized_text,
                        provenance=_base_provenance(
                            source_id=source_id,
                            artifact_id=artifact_id,
                            content_hash=content_hash,
                            document_id=document_id,
                            parser_name=parser_name,
                            parser_version=parser_version,
                            location=LocationAnchor(line_number=line_number),
                        ),
                        ordering_index=ordering_index,
                        variable_references=_extract_variables(normalized_text),
                    ),
                )

    return tuple(equations)
