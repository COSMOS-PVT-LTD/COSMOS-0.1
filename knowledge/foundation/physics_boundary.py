"""Physics integration boundary — solvers query knowledge, they do not copy it."""

from __future__ import annotations

from knowledge.interface.engineering_query import EngineeringQueryService, QueryConstraints
from knowledge.models.correlation import Correlation
from knowledge.models.design_rule import DesignRule
from knowledge.models.physical_law import PhysicalLaw

__all__ = ("PhysicsKnowledgeGateway", "PhysicsKnowledgeError")


class PhysicsKnowledgeError(LookupError):
    """Requested approved knowledge is not available through the gateway."""


class PhysicsKnowledgeGateway:
    """The only knowledge entry point physics modules should use."""

    def __init__(self, query: EngineeringQueryService) -> None:
        self._query = query

    def get_approved_correlation(self, name: str, *, reynolds_number: float | None = None) -> Correlation:
        hits = self._query.find_correlation(
            name,
            QueryConstraints(require_approved=True, reynolds_number=reynolds_number),
        )
        if not hits:
            raise PhysicsKnowledgeError(f"No approved correlation matches '{name}'.")
        return hits[0]

    def get_approved_law(self, name: str) -> PhysicalLaw:
        hits = self._query.find_physical_law(name, QueryConstraints(require_approved=True))
        if not hits:
            raise PhysicsKnowledgeError(f"No approved physical law matches '{name}'.")
        return hits[0]

    def get_approved_design_rule(self, query: str) -> DesignRule:
        hits = self._query.find_design_rule(query, QueryConstraints(require_approved=True))
        if not hits:
            raise PhysicsKnowledgeError(f"No approved design rule matches '{query}'.")
        return hits[0]

    def get_physical_law(self, name: str) -> PhysicalLaw:
        """Alias for get_approved_law. Unapproved laws remain unreachable."""

        return self.get_approved_law(name)

    def get_correlation(self, name: str, *, reynolds_number: float | None = None) -> Correlation:
        """Alias for get_approved_correlation."""

        return self.get_approved_correlation(name, reynolds_number=reynolds_number)

    def get_design_rule(self, query: str) -> DesignRule:
        """Alias for get_approved_design_rule."""

        return self.get_approved_design_rule(query)
