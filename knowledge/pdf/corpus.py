"""COSMOS-authored qualification page text. No third-party prose."""

from __future__ import annotations

__all__ = (
    "AMBIGUOUS_REYNOLDS_PAGE",
    "INCONSISTENT_REYNOLDS_PAGE",
    "NO_EQUATION_PAGE",
    "NOTATION_PAGE",
    "COMPLEX_EQUATION_PAGE",
    "GREEK_SYMBOL_PAGE",
    "NASA_CLASS_PAGE",
    "REYNOLDS_PAGE",
    "TABLE_PAGE",
    "ambiguous_reynolds_pdf_bytes",
    "image_only_pdf_bytes",
    "inconsistent_reynolds_pdf_bytes",
    "mixed_reynolds_pdf_bytes",
    "no_equation_pdf_bytes",
    "notation_scanned_pdf_bytes",
    "complex_equation_pdf_bytes",
    "greek_symbol_pdf_bytes",
    "nasa_class_pdf_bytes",
    "reynolds_pdf_bytes",
    "scanned_reynolds_pdf_bytes",
    "table_scanned_pdf_bytes",
)

from knowledge.pdf.image_pdf import write_scanned_pdf
from knowledge.pdf.writer import write_extractable_pdf, write_image_only_pdf, write_mixed_pdf

REYNOLDS_PAGE: tuple[str, ...] = (
    "Chapter 1 Fluid Mechanics Identities",
    "1.1 Reynolds number",
    "The Reynolds number is the ratio of inertial to viscous forces.",
    "Eq. 1 Re = rho * V * D / mu",
    "Assumption: single characteristic velocity and length.",
    "Valid for internal and external viscous flows.",
    "Figure 1: Channel flow schematic.",
    "Table 1: Symbol definitions for Eq. 1.",
    "Bibliographic identity: Bartz is a named public heat-transfer correlation.",
)

NO_EQUATION_PAGE: tuple[str, ...] = (
    "Chapter 2 Qualitative notes",
    "This COSMOS original page contains no equation symbols or identities.",
    "It is used only to prove that missing equations are not guessed.",
)

INCONSISTENT_REYNOLDS_PAGE: tuple[str, ...] = (
    "Chapter 1 Dimensional failure fixture",
    "Eq. 1 Re = rho * V * D * mu",
)

AMBIGUOUS_REYNOLDS_PAGE: tuple[str, ...] = (
    "Chapter 1 Ambiguous symbol fixture",
    "Eq. 1 Re = u * V * D / mu",
)

TABLE_PAGE: tuple[str, ...] = (
    "Chapter 3 Symbol table",
    "Table 1: Symbol definitions",
    "Re dimensionless Reynolds number",
    "rho density kg/m^3",
    "V velocity m/s",
    "D diameter m",
    "mu viscosity Pa s",
)

NOTATION_PAGE: tuple[str, ...] = (
    "Chapter 4 Engineering notation",
    "Materials: CuCrZr GRCop Inconel 718",
    "Fluids: CH4 O2",
    "Symbols: rho mu Pc Tc Dt",
    "Scientific: 1.23e-4 W/m^2",
)

COMPLEX_EQUATION_PAGE: tuple[str, ...] = (
    "Chapter 5 Nested identities",
    "Eq. 1 Re = (rho * V * D) / mu",
    "Eq. 2 sigma = p * r / t",
    "Eq. 3 q = k * dT / dx",
    "Assumption: continuum viscous flow.",
    "Valid for internal channel flow.",
)

GREEK_SYMBOL_PAGE: tuple[str, ...] = (
    "Chapter 6 Symbol catalogue",
    "ASCII names: alpha beta gamma delta epsilon theta lambda mu nu rho sigma tau phi psi omega",
    "Engineering: rho mu nu sigma tau gamma theta omega",
    "Capitals: Delta Sigma Omega",
    "Eq. 1 Re = rho * V * D / mu",
)

NASA_CLASS_PAGE: tuple[str, ...] = (
    "COSMOS NASA-class structural fixture",
    "This is a COSMOS original. It is not a NASA publication and contains no NASA prose.",
    "Document class under test: NASA technical report structure.",
    "Eq. 1 Re = rho * V * D / mu",
    "Bibliographic identity only: NASA SP-class envelope without source text.",
)


def scanned_reynolds_pdf_bytes() -> bytes:
    return write_scanned_pdf(REYNOLDS_PAGE)


def table_scanned_pdf_bytes() -> bytes:
    return write_scanned_pdf(TABLE_PAGE)


def notation_scanned_pdf_bytes() -> bytes:
    return write_scanned_pdf(NOTATION_PAGE)


def complex_equation_pdf_bytes() -> bytes:
    return write_extractable_pdf((COMPLEX_EQUATION_PAGE,))


def greek_symbol_pdf_bytes() -> bytes:
    return write_extractable_pdf((GREEK_SYMBOL_PAGE,))


def nasa_class_pdf_bytes() -> bytes:
    return write_extractable_pdf((NASA_CLASS_PAGE,))


def reynolds_pdf_bytes() -> bytes:
    return write_extractable_pdf((REYNOLDS_PAGE,))


def no_equation_pdf_bytes() -> bytes:
    return write_extractable_pdf((NO_EQUATION_PAGE,))


def inconsistent_reynolds_pdf_bytes() -> bytes:
    return write_extractable_pdf((INCONSISTENT_REYNOLDS_PAGE,))


def ambiguous_reynolds_pdf_bytes() -> bytes:
    return write_extractable_pdf((AMBIGUOUS_REYNOLDS_PAGE,))


def image_only_pdf_bytes() -> bytes:
    return write_image_only_pdf()


def mixed_reynolds_pdf_bytes() -> bytes:
    return write_mixed_pdf(REYNOLDS_PAGE)
