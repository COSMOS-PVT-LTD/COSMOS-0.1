"""Canonical public-identity engineering seed — bibliographic provenance only."""

from __future__ import annotations

from typing import Any

from knowledge.foundation.engineering_taxonomy import populate_engineering_taxonomy
from knowledge.foundation.keyword_index import KeywordIndex
from knowledge.foundation.material_binding import material_card
from knowledge.graph.concept_graph import ConceptEdge
from knowledge.indexing.citation_index import CitationIndexEntry
from knowledge.indexing.variable_index import VariableIndexEntry
from knowledge.interface.engineering_query import MaterialCard
from knowledge.models.assumption import Assumption
from knowledge.models.boundary_condition import BoundaryCondition
from knowledge.models.component import Component
from knowledge.models.correlation import Correlation
from knowledge.models.design_rule import DesignRule
from knowledge.models.document import Document, DocumentApprovalStatus, DocumentType, SecurityLevel
from knowledge.models.empirical_relation import EmpiricalRelation
from knowledge.models.equation import Equation, EquationCategory, EquationStatus
from knowledge.models.experiment import Experiment
from knowledge.models.failure_mode import FailureMode
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, UncertaintyRecord
from knowledge.models.physical_law import PhysicalLaw
from knowledge.models.property import PropertyDefinition, PropertyValue
from knowledge.models.reference import Reference, ReferenceStatus, ReferenceType
from knowledge.models.simulation import Simulation
from knowledge.ontology.engineering_vocabulary import EngineeringRelationship

__all__ = ("populate_seed_corpus",)


def _prov(reference_id: str, document_id: str, *, page: int | None = None, section: str | None = None) -> ProvenanceTrace:
    return ProvenanceTrace(
        source_reference_id=reference_id,
        document_id=document_id,
        page=page,
        section=section,
        extraction_method="seed-canonical",
        reviewer="kf-system-approver",
        version="1.0.0",
    )


def populate_seed_corpus(service: Any) -> None:
    """Load first-principles and named public identities into an empty service."""

    populate_engineering_taxonomy(service.ontology)
    references = _seed_references(service)
    documents = _seed_documents(service, references)
    _seed_laws(service)
    _seed_equations(service, documents, references)
    _seed_correlations(service)
    _seed_assumptions(service)
    _seed_design_rules(service)
    materials = _seed_materials(service)
    _seed_properties(service, materials)
    _seed_components(service)
    _seed_failures(service)
    _seed_boundary_conditions(service)
    _seed_experiment_and_simulation(service)
    _seed_empirical_candidate(service)
    _seed_graph(service)
    _seed_indexes(service)


def _seed_references(service: Any) -> dict[str, Reference]:
    items = (
        Reference(
            reference_id="REF-NASA-SP-8087",
            title="Liquid Rocket Engine Regenerative Cooling",
            authors=("NASA",),
            reference_type=ReferenceType.NASA_REPORT,
            publication_year=1972,
            status=ReferenceStatus.APPROVED,
            notes="Bibliographic identity only. No proprietary text is stored.",
        ),
        Reference(
            reference_id="REF-FIRST-PRINCIPLES",
            title="Classical continuum-mechanics and thermodynamics identities",
            authors=("Public domain / first principles",),
            reference_type=ReferenceType.OTHER,
            publication_year=1800,
            status=ReferenceStatus.APPROVED,
        ),
        Reference(
            reference_id="REF-PUBLIC-HEAT-TRANSFER",
            title="Named internal-flow heat-transfer identities",
            authors=("Public engineering identities",),
            reference_type=ReferenceType.OTHER,
            publication_year=1930,
            status=ReferenceStatus.APPROVED,
        ),
        Reference(
            reference_id="REF-PUBLIC-GAS-DYNAMICS",
            title="Isentropic compressible-flow identities",
            authors=("Public engineering identities",),
            reference_type=ReferenceType.OTHER,
            publication_year=1953,
            status=ReferenceStatus.APPROVED,
        ),
        Reference(
            reference_id="REF-PUBLIC-STRUCTURES",
            title="Thin-wall pressure-vessel identities",
            authors=("Public engineering identities",),
            reference_type=ReferenceType.OTHER,
            publication_year=1900,
            status=ReferenceStatus.APPROVED,
        ),
    )
    by_id = {}
    for item in items:
        service.references.create(item)
        by_id[item.reference_id] = item
    return by_id


def _seed_documents(service: Any, references: dict[str, Reference]) -> dict[str, Document]:
    items = (
        Document(
            document_id="DOC-SP-8087",
            document_version_id="v1",
            title="NASA SP-8087 bibliographic envelope",
            content="Bibliographic envelope for regenerative-cooling identities. No source prose stored.",
            document_type=DocumentType.NASA_REPORT,
            reference=references["REF-NASA-SP-8087"],
            approval_status=DocumentApprovalStatus.APPROVED,
            security_level=SecurityLevel.PUBLIC,
        ),
        Document(
            document_id="DOC-FIRST-PRINCIPLES",
            document_version_id="v1",
            title="First-principles identity envelope",
            content="Public first-principles identities used by the knowledge foundation seed.",
            document_type=DocumentType.OTHER,
            reference=references["REF-FIRST-PRINCIPLES"],
            approval_status=DocumentApprovalStatus.APPROVED,
            security_level=SecurityLevel.PUBLIC,
        ),
        Document(
            document_id="DOC-PUBLIC-HEAT-TRANSFER",
            document_version_id="v1",
            title="Public heat-transfer identity envelope",
            content="Named public heat-transfer correlations.",
            document_type=DocumentType.TEXTBOOK,
            reference=references["REF-PUBLIC-HEAT-TRANSFER"],
            approval_status=DocumentApprovalStatus.APPROVED,
            security_level=SecurityLevel.PUBLIC,
        ),
    )
    by_id = {}
    for item in items:
        service.documents.create(item)
        by_id[item.document_id] = item
    return by_id


def _seed_laws(service: Any) -> None:
    laws = (
        PhysicalLaw(
            law_id="LAW-NEWTON-2",
            name="Newton's Second Law",
            description="Force equals mass times acceleration in an inertial frame.",
            mathematical_formulation="F = m*a",
            variables=("F", "m", "a"),
            units=("N", "kg", "m/s^2"),
            assumptions=("inertial frame", "point mass or mass-center form"),
            domain="DYNAMICS",
            applicability="inertial frames",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Mechanics"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-MASS",
            name="Conservation of Mass",
            description="Mass is conserved for a closed continuum system without nuclear sources.",
            mathematical_formulation="d/dt ∫ rho dV + ∫ rho V·n dA = 0",
            variables=("rho", "V"),
            units=("kg/m^3", "m/s"),
            assumptions=("continuum", "no nuclear mass conversion"),
            domain="FLUID_MECHANICS",
            applicability="continuum mass balance",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Continuity"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-ENERGY",
            name="First Law of Thermodynamics",
            description="Energy is conserved; heat and work change the internal energy of a system.",
            mathematical_formulation="dE = dQ - dW",
            variables=("E", "Q", "W"),
            units=("J", "J", "J"),
            assumptions=("closed system form shown",),
            domain="THERMODYNAMICS",
            applicability="thermodynamic systems with defined boundary work/heat",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="First Law"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-FOURIER",
            name="Fourier's Law",
            description="Conductive heat flux is proportional to the negative temperature gradient.",
            mathematical_formulation="q = -k * dT/dx",
            variables=("q", "k", "dT", "dx"),
            units=("W/m^2", "W/m-K", "K", "m"),
            assumptions=("isotropic Fourier conduction",),
            domain="HEAT_TRANSFER",
            applicability="continuum conduction",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Conduction"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-REYNOLDS",
            name="Reynolds Number",
            description="Ratio of inertial to viscous forces.",
            mathematical_formulation="Re = rho*V*D/mu",
            variables=("Re", "rho", "V", "D", "mu"),
            units=("1", "kg/m^3", "m/s", "m", "Pa·s"),
            assumptions=("single characteristic velocity and length",),
            domain="FLUID_MECHANICS",
            applicability="internal and external viscous flows",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Dimensionless groups"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-BERNOULLI",
            name="Bernoulli Equation",
            description="Mechanical energy along a streamline for steady inviscid incompressible flow.",
            mathematical_formulation="p/rho + V^2/2 + g*z = constant",
            variables=("p", "rho", "V", "g", "z"),
            units=("Pa", "kg/m^3", "m/s", "m/s^2", "m"),
            assumptions=("steady", "inviscid", "incompressible", "along a streamline"),
            domain="FLUID_MECHANICS",
            applicability="incompressible streamline flow without shaft work",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Bernoulli"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-THRUST",
            name="Rocket Thrust",
            description="Momentum and pressure thrust of a rocket nozzle.",
            mathematical_formulation="F = mdot*ve + (pe-pa)*Ae",
            variables=("F", "mdot", "ve", "pe", "pa", "Ae"),
            units=("N", "kg/s", "m/s", "Pa", "Pa", "m^2"),
            assumptions=("one-dimensional exhaust", "control-volume at exit"),
            domain="ROCKET_PROPULSION",
            applicability="chemical rocket nozzles",
            provenance=_prov("REF-PUBLIC-GAS-DYNAMICS", "DOC-FIRST-PRINCIPLES", section="Thrust"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-ISP",
            name="Specific Impulse",
            description="Thrust per unit weight-flow of propellant.",
            mathematical_formulation="Isp = F/(mdot*g0)",
            variables=("Isp", "F", "mdot", "g0"),
            units=("s", "N", "kg/s", "m/s^2"),
            assumptions=("g0 is standard gravity",),
            domain="ROCKET_PROPULSION",
            applicability="rocket performance reporting",
            provenance=_prov("REF-PUBLIC-GAS-DYNAMICS", "DOC-FIRST-PRINCIPLES", section="Isp"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-CSTAR",
            name="Characteristic Velocity",
            description="Chamber-performance parameter c*.",
            mathematical_formulation="cstar = pc*At/mdot",
            variables=("cstar", "pc", "At", "mdot"),
            units=("m/s", "Pa", "m^2", "kg/s"),
            assumptions=("one-dimensional throat definition",),
            domain="ROCKET_PROPULSION",
            applicability="liquid and solid rocket chambers",
            provenance=_prov("REF-PUBLIC-GAS-DYNAMICS", "DOC-FIRST-PRINCIPLES", section="c*"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-CF",
            name="Thrust Coefficient",
            description="Nozzle thrust coefficient CF.",
            mathematical_formulation="CF = F/(pc*At)",
            variables=("CF", "F", "pc", "At"),
            units=("1", "N", "Pa", "m^2"),
            assumptions=("consistent chamber-pressure definition",),
            domain="ROCKET_PROPULSION",
            applicability="nozzle performance",
            provenance=_prov("REF-PUBLIC-GAS-DYNAMICS", "DOC-FIRST-PRINCIPLES", section="CF"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        PhysicalLaw(
            law_id="LAW-HOOP",
            name="Thin-Wall Hoop Stress",
            description="Circumferential stress in a thin-walled cylinder.",
            mathematical_formulation="sigma = p*r/t",
            variables=("sigma", "p", "r", "t"),
            units=("Pa", "Pa", "m", "m"),
            assumptions=("thin wall", "r/t >> 1"),
            domain="STRUCTURES",
            applicability="cylindrical pressure vessels and chambers",
            provenance=_prov("REF-PUBLIC-STRUCTURES", "DOC-FIRST-PRINCIPLES", section="Hoop stress"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
    )
    for law in laws:
        service.physical_laws.create(law)


def _seed_equations(
    service: Any,
    documents: dict[str, Document],
    references: dict[str, Reference],
) -> None:
    equation = Equation(
        equation_id="EQ-RE-001",
        equation_name="Reynolds number",
        equation_category=EquationCategory.FLUID_DYNAMICS,
        equation_version="1.0.0",
        source_document=documents["DOC-FIRST-PRINCIPLES"],
        source_reference=references["REF-FIRST-PRINCIPLES"],
        expression="Re = rho*V*D/mu",
        latex_expression=r"Re = \rho V D / \mu",
        symbolic_expression="Re = rho*V*D/mu",
        normalized_expression="Re = rho*V*D/mu",
        chapter="Fluid Mechanics",
        section="Dimensionless groups",
        page_number=1,
        extracted_by="seed-canonical",
        extraction_confidence=1.0,
        status=EquationStatus.APPROVED,
    )
    service.equations.create(equation)


def _seed_correlations(service: Any) -> None:
    items = (
        Correlation(
            correlation_id="CORR-DITTUS-BOELTER",
            name="Dittus-Boelter",
            equation="Nu = 0.023 * Re**0.8 * Pr**n",
            variables=("Nu", "Re", "Pr"),
            dimensionless_groups=("Nu", "Re", "Pr"),
            applicable_fluid="single-phase liquid or gas",
            geometry="smooth circular tube",
            reynolds_range=(1.0e4, 1.2e5),
            prandtl_range=(0.7, 160.0),
            uncertainty=UncertaintyRecord(kind="correlation", magnitude=0.25, unit="fraction"),
            accuracy="typical textbook scatter band",
            assumptions=("fully developed turbulent flow", "n=0.4 heating / 0.3 cooling"),
            provenance=_prov("REF-PUBLIC-HEAT-TRANSFER", "DOC-PUBLIC-HEAT-TRANSFER", section="Internal forced convection"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
            domain="HEAT_TRANSFER",
        ),
        Correlation(
            correlation_id="CORR-GNIELINSKI",
            name="Gnielinski",
            equation="Nu = (f/8)*(Re-1000)*Pr / (1 + 12.7*sqrt(f/8)*(Pr**(2/3)-1))",
            variables=("Nu", "Re", "Pr", "f"),
            dimensionless_groups=("Nu", "Re", "Pr"),
            applicable_fluid="single-phase fluid",
            geometry="circular tube",
            reynolds_range=(3.0e3, 5.0e6),
            prandtl_range=(0.5, 2000.0),
            uncertainty=UncertaintyRecord(kind="correlation", magnitude=0.15, unit="fraction"),
            assumptions=("transitional-to-turbulent internal flow",),
            provenance=_prov("REF-PUBLIC-HEAT-TRANSFER", "DOC-PUBLIC-HEAT-TRANSFER", section="Gnielinski"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
            domain="HEAT_TRANSFER",
        ),
        Correlation(
            correlation_id="CORR-SIEDER-TATE",
            name="Sieder-Tate",
            equation="Nu = 0.027 * Re**0.8 * Pr**(1/3) * (mu/mu_w)**0.14",
            variables=("Nu", "Re", "Pr", "mu", "mu_w"),
            dimensionless_groups=("Nu", "Re", "Pr"),
            applicable_fluid="single-phase liquid",
            geometry="circular tube",
            reynolds_range=(1.0e4, 1.0e6),
            provenance=_prov("REF-PUBLIC-HEAT-TRANSFER", "DOC-PUBLIC-HEAT-TRANSFER", section="Sieder-Tate"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
            domain="HEAT_TRANSFER",
        ),
        Correlation(
            correlation_id="CORR-DARCY-WEISBACH",
            name="Darcy-Weisbach",
            equation="dP = f * (L/D) * (rho * V**2 / 2)",
            variables=("dP", "f", "L", "D", "rho", "V"),
            dimensionless_groups=("f",),
            applicable_fluid="incompressible or locally incompressible pipe flow",
            geometry="circular pipe",
            reynolds_range=(1.0e2, 1.0e8),
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Pipe flow"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
            domain="FLUID_MECHANICS",
        ),
        Correlation(
            correlation_id="CORR-COLEBROOK",
            name="Colebrook",
            equation="1/sqrt(f) = -2*log10(eps/D/3.7 + 2.51/(Re*sqrt(f)))",
            variables=("f", "eps", "D", "Re"),
            dimensionless_groups=("f", "Re"),
            applicable_fluid="Newtonian pipe flow",
            geometry="circular pipe",
            reynolds_range=(4.0e3, 1.0e8),
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Friction factor"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
            domain="FLUID_MECHANICS",
        ),
        Correlation(
            correlation_id="CORR-BARTZ",
            name="Bartz",
            equation="hg = (0.026/Dt**0.2)*(mu**0.2*cp/Pr**0.6)*(pc/cstar)**0.8*(Dt/R)**0.1*sigma",
            variables=("hg", "Dt", "mu", "cp", "Pr", "pc", "cstar", "R", "sigma"),
            dimensionless_groups=("Re", "Pr"),
            applicable_fluid="hot gas / regenerative coolant side as published",
            geometry="rocket nozzle regenerative cooling",
            reynolds_range=(1.0e4, 1.0e7),
            prandtl_range=(0.5, 2.0),
            uncertainty=UncertaintyRecord(
                kind="correlation",
                magnitude=0.2,
                unit="fraction",
                notes="Representative published scatter; not a COSMOS hot-fire measurement.",
            ),
            assumptions=("single-phase coolant when applied on the coolant side", "axisymmetric nozzle"),
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", page=12, section="Regenerative cooling"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
            domain="HEAT_TRANSFER",
        ),
    )
    for item in items:
        service.correlations.create(item)


def _seed_assumptions(service: Any) -> None:
    service.assumptions.create(
        Assumption(
            assumption_id="ASM-SINGLE-PHASE",
            statement="Coolant is treated as single-phase.",
            category="thermal",
            affected_entity_ids=("CORR-BARTZ",),
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", page=12, section="Assumptions"),
            justification="Named regenerative-cooling application envelope.",
            applicability="specified pressure/temperature range without bulk boiling",
            confidence=0.8,
            lifecycle=KnowledgeLifecycle.APPROVED,
            created_by="kf-system-approver",
            approved_by="kf-system-approver",
        ),
    )
    service.assumptions.create(
        Assumption(
            assumption_id="ASM-IDEAL-GAS",
            statement="Chamber gas is treated as an ideal gas for isentropic nozzle relations.",
            category="gas-dynamics",
            affected_entity_ids=("LAW-THRUST", "LAW-CSTAR"),
            provenance=_prov("REF-PUBLIC-GAS-DYNAMICS", "DOC-FIRST-PRINCIPLES", section="Isentropic flow"),
            justification="Standard compressible-flow identity envelope.",
            applicability="calorically perfect gas nozzle estimates",
            confidence=0.7,
            lifecycle=KnowledgeLifecycle.APPROVED,
            created_by="kf-system-approver",
            approved_by="kf-system-approver",
        ),
    )


def _seed_design_rules(service: Any) -> None:
    service.design_rules.create(
        DesignRule(
            rule_id="RULE-TWALL-MAX",
            statement="Maximum wall temperature shall not exceed the material temperature limit.",
            formula="T_wall <= T_material_limit",
            parameters=("T_wall", "T_material_limit"),
            applicability="regeneratively cooled chambers and nozzles",
            authority="NASA SP-8087 bibliographic envelope",
            severity="CRITICAL",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Design limits"),
            domain="HEAT_TRANSFER",
            lifecycle=KnowledgeLifecycle.APPROVED,
            approval="kf-system-approver",
            validation_status="APPROVED",
        ),
    )
    service.design_rules.create(
        DesignRule(
            rule_id="RULE-INJECTOR-DP",
            statement="Injector pressure drop must remain large enough to isolate chamber oscillations.",
            formula="dP_inj >= k * pc",
            parameters=("dP_inj", "k", "pc"),
            applicability="liquid injectors",
            authority="public injector-design practice",
            severity="HIGH",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Injector"),
            domain="INJECTOR",
            lifecycle=KnowledgeLifecycle.APPROVED,
            approval="kf-system-approver",
            validation_status="APPROVED",
        ),
    )
    service.design_rules.create(
        DesignRule(
            rule_id="RULE-SF-MIN",
            statement="Minimum structural safety factor shall be respected for chamber pressure.",
            formula="SF >= SF_min",
            parameters=("SF", "SF_min"),
            applicability="thin-wall chambers",
            authority="public pressure-vessel practice",
            severity="CRITICAL",
            provenance=_prov("REF-PUBLIC-STRUCTURES", "DOC-FIRST-PRINCIPLES", section="Safety factor"),
            domain="STRUCTURES",
            lifecycle=KnowledgeLifecycle.APPROVED,
            approval="kf-system-approver",
            validation_status="APPROVED",
        ),
    )


def _seed_materials(service: Any) -> dict[str, MaterialCard]:
    cards = (
        material_card(
            material_id="MAT-WATER",
            name="Water",
            aliases=("H2O", "water"),
            classification="FLUID",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Properties"),
        ),
        material_card(
            material_id="MAT-CU-OFHC",
            name="OFHC Copper",
            aliases=("copper", "Cu", "OFHC"),
            classification="COPPER",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Materials"),
        ),
        material_card(
            material_id="MAT-GRCOP-42",
            name="GRCop-42",
            aliases=("GRCop-42", "CuCrNb"),
            classification="COPPER_ALLOY",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Materials"),
        ),
        material_card(
            material_id="MAT-IN718",
            name="Inconel 718",
            aliases=("IN718", "Alloy 718"),
            classification="NICKEL_SUPERALLOY",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Materials"),
        ),
        material_card(
            material_id="MAT-304L",
            name="Stainless Steel 304L",
            aliases=("304L", "SS304L"),
            classification="AUSTENITIC_STAINLESS",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Materials"),
        ),
        material_card(
            material_id="MAT-316L",
            name="Stainless Steel 316L",
            aliases=("316L", "SS316L"),
            classification="AUSTENITIC_STAINLESS",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Materials"),
        ),
    )
    for card in cards:
        service.materials.append(card)
    return {card.material_id: card for card in cards}


def _seed_properties(service: Any, materials: dict[str, MaterialCard]) -> None:
    definitions = (
        PropertyDefinition(
            property_id="PROP-DENSITY",
            name="density",
            symbol="rho",
            dimension="M L^-3",
            unit="kg/m^3",
            description="Mass density",
            domain="MATERIALS",
        ),
        PropertyDefinition(
            property_id="PROP-VISCOSITY",
            name="dynamic viscosity",
            symbol="mu",
            dimension="M L^-1 T^-1",
            unit="Pa·s",
            description="Dynamic viscosity",
            domain="MATERIALS",
        ),
        PropertyDefinition(
            property_id="PROP-K",
            name="thermal conductivity",
            symbol="k",
            dimension="M L T^-3 Θ^-1",
            unit="W/m-K",
            description="Thermal conductivity",
            domain="HEAT_TRANSFER",
        ),
        PropertyDefinition(
            property_id="PROP-CP",
            name="specific heat",
            symbol="cp",
            dimension="L^2 T^-2 Θ^-1",
            unit="J/kg-K",
            description="Specific heat at constant pressure",
            domain="THERMODYNAMICS",
        ),
    )
    for definition in definitions:
        service.properties.definitions.create(definition)

    service.properties.values.create(
        PropertyValue(
            value_id="PV-WATER-DENSITY-298",
            property_id="PROP-DENSITY",
            material_id=materials["MAT-WATER"].material_id,
            numeric_value=997.0,
            unit="kg/m^3",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Water"),
            temperature_k=298.15,
            pressure_pa=101325.0,
            validity_range="273 K to 373 K at 1 atm, liquid water",
            lifecycle=KnowledgeLifecycle.APPROVED,
        ),
    )
    service.properties.values.create(
        PropertyValue(
            value_id="PV-CU-DENSITY-293",
            property_id="PROP-DENSITY",
            material_id=materials["MAT-CU-OFHC"].material_id,
            numeric_value=8960.0,
            unit="kg/m^3",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Copper"),
            temperature_k=293.15,
            pressure_pa=101325.0,
            validity_range="near 293 K, commercially pure copper",
            lifecycle=KnowledgeLifecycle.APPROVED,
        ),
    )


def _seed_components(service: Any) -> None:
    for component in (
        Component(
            component_id="COMP-INJECTOR",
            name="Injector",
            classification="PROPULSION",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Injector"),
            geometry="faceplate with orifices",
            material_ids=("MAT-IN718",),
            design_rule_ids=("RULE-INJECTOR-DP",),
            failure_mode_ids=("FM-CAVITATION",),
            lifecycle=KnowledgeLifecycle.APPROVED,
            verification_status="REVIEWED",
        ),
        Component(
            component_id="COMP-CHAMBER",
            name="Combustion Chamber",
            classification="PROPULSION",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Chamber"),
            material_ids=("MAT-GRCOP-42", "MAT-CU-OFHC"),
            design_rule_ids=("RULE-TWALL-MAX", "RULE-SF-MIN"),
            failure_mode_ids=("FM-BURNTHROUGH", "FM-THERMAL-FATIGUE"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            verification_status="REVIEWED",
        ),
        Component(
            component_id="COMP-NOZZLE",
            name="Nozzle",
            classification="PROPULSION",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Nozzle"),
            material_ids=("MAT-GRCOP-42",),
            design_rule_ids=("RULE-TWALL-MAX",),
            failure_mode_ids=("FM-BURNTHROUGH",),
            lifecycle=KnowledgeLifecycle.APPROVED,
            verification_status="REVIEWED",
        ),
        Component(
            component_id="COMP-TURBOPUMP",
            name="Turbopump",
            classification="TURBOMACHINERY",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Turbopump"),
            failure_mode_ids=("FM-CAVITATION",),
            lifecycle=KnowledgeLifecycle.APPROVED,
            verification_status="REVIEWED",
        ),
    ):
        service.components.create(component)


def _seed_failures(service: Any) -> None:
    for item in (
        FailureMode(
            failure_mode_id="FM-BURNTHROUGH",
            name="burn-through",
            mechanism="local wall temperature exceeds material capability",
            cause="insufficient coolant heat transfer or hot-gas streaking",
            effect="chamber or nozzle wall rupture",
            severity="CATASTROPHIC",
            likelihood="MEDIUM",
            mitigation="regenerative cooling and wall-temperature design rule",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Failure modes"),
            design_rule_ids=("RULE-TWALL-MAX",),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        FailureMode(
            failure_mode_id="FM-THERMAL-FATIGUE",
            name="thermal fatigue",
            mechanism="cyclic thermal strain in the hot wall",
            cause="repeated hot-fire thermal gradients",
            effect="ligament cracking",
            severity="HIGH",
            likelihood="MEDIUM",
            mitigation="life-limited duty cycle and material selection",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Failure modes"),
            design_rule_ids=("RULE-TWALL-MAX",),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
        FailureMode(
            failure_mode_id="FM-CAVITATION",
            name="cavitation",
            mechanism="local pressure falls below vapor pressure",
            cause="insufficient NPSH or injector manifold pressure",
            effect="erosion and unsteady mass flow",
            severity="HIGH",
            likelihood="MEDIUM",
            mitigation="NPSH margin and injector pressure-drop rule",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Cavitation"),
            design_rule_ids=("RULE-INJECTOR-DP",),
            lifecycle=KnowledgeLifecycle.APPROVED,
            validation_status="APPROVED",
        ),
    ):
        service.failure_modes.create(item)


def _seed_boundary_conditions(service: Any) -> None:
    service.boundary_conditions.create(
        BoundaryCondition(
            boundary_condition_id="BC-CHAMBER-HEAT-FLUX",
            name="Chamber wall heat flux",
            quantity="heat_flux",
            value_expression="q_wall from approved hot-gas correlation",
            unit="W/m^2",
            geometry_location="chamber hot wall",
            applicable_solver="thermal / CFD",
            applicable_physics="conjugate heat transfer",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Boundary conditions"),
            assumption_ids=("ASM-SINGLE-PHASE",),
            validity="within Bartz applicability envelope",
            lifecycle=KnowledgeLifecycle.APPROVED,
            verification_status="REVIEWED",
        ),
    )
    service.boundary_conditions.create(
        BoundaryCondition(
            boundary_condition_id="BC-NOZZLE-TWALL",
            name="Nozzle wall temperature limit",
            quantity="wall_temperature",
            value_expression="T_wall <= T_material_limit",
            unit="K",
            geometry_location="nozzle hot wall",
            applicable_solver="thermal",
            applicable_physics="heat transfer",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Boundary conditions"),
            validity="material-limit design rule",
            lifecycle=KnowledgeLifecycle.APPROVED,
            verification_status="REVIEWED",
        ),
    )


def _seed_experiment_and_simulation(service: Any) -> None:
    service.experiments.create(
        Experiment(
            experiment_id="EXP-REGEN-001",
            objective="Validate regenerative-cooling heat-transfer applicability of Bartz.",
            hypothesis="Single-phase coolant Bartz estimates bound measured wall temperatures.",
            test_article="regeneratively cooled subscale nozzle",
            test_configuration="hot-fire, LOX/CH4, recorded wall thermocouples",
            instrumentation=("wall thermocouples", "chamber pressure", "coolant delta-T"),
            input_conditions="recorded pc, mdot, coolant inlet T",
            measured_quantities=("T_wall", "q_coolant"),
            procedure="Compare predicted h to inferred coolant-side heat pickup.",
            results="Synthetic qualification record — no proprietary measurements stored.",
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Validation"),
            validation_conclusion="Envelope B synthetic validation placeholder.",
            lifecycle=KnowledgeLifecycle.APPROVED,
        ),
    )
    service.simulations.create(
        Simulation(
            simulation_id="SIM-CHAMBER-CFD-001",
            solver="generic-cfd",
            physics_model="RANS conjugate heat transfer",
            geometry="axisymmetric chamber-nozzle",
            boundary_condition_ids=("BC-CHAMBER-HEAT-FLUX", "BC-NOZZLE-TWALL"),
            provenance=_prov("REF-NASA-SP-8087", "DOC-SP-8087", section="Simulation"),
            material_model_ids=("MAT-GRCOP-42",),
            software_version="unspecified-local",
            verification_status="REVIEWED",
            validation_status="REVIEWED",
            lifecycle=KnowledgeLifecycle.APPROVED,
        ),
    )


def _seed_empirical_candidate(service: Any) -> None:
    service.empirical.create(
        EmpiricalRelation(
            relation_id="EMP-INJECTOR-CD-FIT",
            name="Injector discharge fit",
            equation="Cd = a + b*Re",
            variables=("Cd", "Re"),
            domain="INJECTOR",
            data_basis="unreviewed synthetic series",
            provenance=_prov("REF-FIRST-PRINCIPLES", "DOC-FIRST-PRINCIPLES", section="Empirical"),
            lifecycle=KnowledgeLifecycle.CANDIDATE,
            validation_status="UNREVIEWED",
        ),
    )


def _seed_graph(service: Any) -> None:
    edges = (
        ConceptEdge(source_id="CORR-BARTZ", target_id="LAW-REYNOLDS", relationship=EngineeringRelationship.USES),
        ConceptEdge(source_id="CORR-BARTZ", target_id="ASM-SINGLE-PHASE", relationship=EngineeringRelationship.REQUIRES),
        ConceptEdge(source_id="CORR-BARTZ", target_id="COMP-NOZZLE", relationship=EngineeringRelationship.VALID_FOR),
        ConceptEdge(source_id="CORR-BARTZ", target_id="EXP-REGEN-001", relationship=EngineeringRelationship.VALIDATED_BY),
        ConceptEdge(source_id="CORR-BARTZ", target_id="DOC-SP-8087", relationship=EngineeringRelationship.DERIVED_FROM),
        ConceptEdge(source_id="RULE-TWALL-MAX", target_id="FM-BURNTHROUGH", relationship=EngineeringRelationship.MITIGATES),
        ConceptEdge(source_id="COMP-CHAMBER", target_id="COMP-NOZZLE", relationship=EngineeringRelationship.PART_OF),
        ConceptEdge(source_id="COMP-INJECTOR", target_id="COMP-CHAMBER", relationship=EngineeringRelationship.PART_OF),
        ConceptEdge(source_id="LAW-HOOP", target_id="COMP-CHAMBER", relationship=EngineeringRelationship.VALID_FOR),
        ConceptEdge(source_id="LAW-THRUST", target_id="COMP-NOZZLE", relationship=EngineeringRelationship.USES),
        ConceptEdge(source_id="SIM-CHAMBER-CFD-001", target_id="BC-CHAMBER-HEAT-FLUX", relationship=EngineeringRelationship.REQUIRES),
        ConceptEdge(source_id="FM-CAVITATION", target_id="COMP-TURBOPUMP", relationship=EngineeringRelationship.VALID_FOR),
    )
    for edge in edges:
        service.graph.add(edge)


def _seed_indexes(service: Any) -> None:
    keywords: KeywordIndex = service.keywords
    for law in service.physical_laws.query():
        keywords.add(
            entity_id=law.law_id,
            entity_type="PhysicalLaw",
            title=law.name,
            terms=(law.name, law.mathematical_formulation, law.domain, *law.variables),
            lifecycle=law.lifecycle,
            provenance_id=law.provenance.source_reference_id,
        )
        service.embeddings.embed(
            entity_id=law.law_id,
            entity_type="PhysicalLaw",
            text=f"{law.name} {law.mathematical_formulation}",
        )
        service.citation_index.add(
            CitationIndexEntry(
                reference_id=law.provenance.source_reference_id,
                entity_id=law.law_id,
                entity_type="PhysicalLaw",
                document_id=law.provenance.document_id,
                page=law.provenance.page,
            ),
        )
    for item in service.correlations.query():
        keywords.add(
            entity_id=item.correlation_id,
            entity_type="Correlation",
            title=item.name,
            terms=(item.name, item.equation, item.domain, *(item.geometry or "", item.applicable_fluid or "")),
            lifecycle=item.lifecycle,
            provenance_id=item.provenance.source_reference_id if item.provenance else None,
        )
        service.embeddings.embed(
            entity_id=item.correlation_id,
            entity_type="Correlation",
            text=f"{item.name} {item.equation}",
        )
        if item.provenance:
            service.citation_index.add(
                CitationIndexEntry(
                    reference_id=item.provenance.source_reference_id,
                    entity_id=item.correlation_id,
                    entity_type="Correlation",
                    document_id=item.provenance.document_id,
                    page=item.provenance.page,
                ),
            )
    for item in service.design_rules.query():
        keywords.add(
            entity_id=item.rule_id,
            entity_type="DesignRule",
            title=item.statement,
            terms=(item.statement, item.formula, item.domain),
            lifecycle=item.lifecycle,
            provenance_id=item.provenance.source_reference_id,
        )
    for card in service.materials:
        keywords.add(
            entity_id=card.material_id,
            entity_type="Material",
            title=card.name,
            terms=(card.name, *card.aliases, card.classification),
            lifecycle=card.lifecycle,
            provenance_id=card.source_reference_id,
        )
    for equation in service.equations.query():
        service.equation_index.add(equation, variables=("Re", "rho", "V", "D", "mu"))
        keywords.add(
            entity_id=equation.equation_id,
            entity_type="Equation",
            title=equation.equation_name,
            terms=(equation.equation_name, equation.expression, "Re"),
            lifecycle=KnowledgeLifecycle.APPROVED,
            provenance_id=equation.source_reference.reference_id,
        )
    service.variable_index.add(
        VariableIndexEntry(
            variable_id="VAR-RE",
            symbol="Re",
            name="Reynolds number",
            equation_ids=("EQ-RE-001", "CORR-BARTZ", "CORR-DITTUS-BOELTER"),
        ),
    )
    service.variable_index.add(
        VariableIndexEntry(
            variable_id="VAR-PR",
            symbol="Pr",
            name="Prandtl number",
            equation_ids=("CORR-BARTZ", "CORR-DITTUS-BOELTER"),
        ),
    )
    service.variable_index.add(
        VariableIndexEntry(
            variable_id="VAR-NU",
            symbol="Nu",
            name="Nusselt number",
            equation_ids=("CORR-DITTUS-BOELTER", "CORR-GNIELINSKI"),
        ),
    )
    service.citation_index.add(
        CitationIndexEntry(
            reference_id="REF-NASA-SP-8087",
            entity_id="CORR-BARTZ",
            entity_type="Correlation",
            document_id="DOC-SP-8087",
            page=12,
        ),
    )
