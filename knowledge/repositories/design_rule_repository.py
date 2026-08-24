"""Design-rule repository facade."""

from __future__ import annotations

from knowledge.models.design_rule import DesignRule
from knowledge.repository.knowledge_repository import KnowledgeRepository

__all__ = ("DesignRuleRepository",)


class DesignRuleRepository(KnowledgeRepository[DesignRule]):
    def __init__(self) -> None:
        super().__init__(id_of=lambda item: item.rule_id, lifecycle_of=lambda item: item.lifecycle)
