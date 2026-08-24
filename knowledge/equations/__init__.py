"""Source-faithful equation extraction — candidates only until governed approval."""

from __future__ import annotations

from knowledge.equations.conflicts import (
    CONTRADICTION_DETECTED,
    REPRESENTATION_CONFLICT,
    detect_equation_conflicts,
    detect_representation_conflicts,
)
from knowledge.equations.detector import detect_source_equations
from knowledge.equations.models import (
    EquationClassification,
    EquationValidationState,
    SourceEquationCandidate,
    ValidatedEquationCandidate,
)
from knowledge.equations.reconstruction import EquationReconstruction, reconstruct_equation
from knowledge.equations.review import (
    EquationReviewPackage,
    build_review_package,
    review_validated_equation,
)
from knowledge.equations.uncertainty import Uncertainty
from knowledge.equations.validation import validate_equation_candidate

__all__ = (
    "CONTRADICTION_DETECTED",
    "EquationClassification",
    "EquationReviewPackage",
    "EquationReconstruction",
    "EquationValidationState",
    "REPRESENTATION_CONFLICT",
    "SourceEquationCandidate",
    "Uncertainty",
    "ValidatedEquationCandidate",
    "build_review_package",
    "detect_equation_conflicts",
    "detect_representation_conflicts",
    "detect_source_equations",
    "reconstruct_equation",
    "review_validated_equation",
    "validate_equation_candidate",
)
