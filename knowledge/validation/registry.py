"""Validation rule registry for KG-BLOCK-009."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from knowledge.validation.exceptions import ValidationRegistryError, ValidationRuleError
from knowledge.validation.models import ValidationCategory, ValidationContext, ValidationFinding, ValidationSeverity

__all__ = (
    "ValidationRule",
    "ValidationRuleRegistry",
)


ValidatorCallable = Callable[[ValidationContext], tuple[ValidationFinding, ...]]


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationRule:
    """Explicit inspectable validation rule."""

    rule_id: str
    name: str
    category: ValidationCategory
    severity: ValidationSeverity
    description: str
    validator: ValidatorCallable


class ValidationRuleRegistry:
    """Deterministic validation rule registry."""

    def __init__(self) -> None:
        self._rules: dict[str, ValidationRule] = {}

    def register(self, rule: ValidationRule) -> None:
        """Register a validation rule."""

        if rule.rule_id in self._rules:
            raise ValidationRuleError(
                f"Validation rule '{rule.rule_id}' is already registered."
            )

        self._rules[rule.rule_id] = rule

    def get(self, rule_id: str) -> ValidationRule:
        """Return a registered rule by identifier."""

        try:
            return self._rules[rule_id]
        except KeyError as exc:
            raise ValidationRegistryError(
                f"Validation rule '{rule_id}' was not found."
            ) from exc

    def list_rules(self) -> tuple[ValidationRule, ...]:
        """Return rules in deterministic rule_id order."""

        return tuple(self._rules[rule_id] for rule_id in sorted(self._rules))
