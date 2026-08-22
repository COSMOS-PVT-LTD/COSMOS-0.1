from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "COSMOS_Space_Ecosystem_Vision.pdf"

PAGE_W, PAGE_H = A4
LEFT_MARGIN = 18 * mm
RIGHT_MARGIN = 18 * mm
TOP_MARGIN = 18 * mm
BOTTOM_MARGIN = 16 * mm
CONTENT_W = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN

INK = colors.HexColor("#101828")
MUTED = colors.HexColor("#667085")
BLUE = colors.HexColor("#175CD3")
DEEP_BLUE = colors.HexColor("#1849A9")
LIGHT_BLUE = colors.HexColor("#EAF1FF")
GREEN = colors.HexColor("#067647")
LIGHT_GREEN = colors.HexColor("#EAFBF1")
AMBER = colors.HexColor("#B54708")
LIGHT_AMBER = colors.HexColor("#FFF3E7")
RED = colors.HexColor("#B42318")
LIGHT_RED = colors.HexColor("#FEF3F2")
GREY_BG = colors.HexColor("#F8FAFC")
LINE = colors.HexColor("#D0D5DD")


class SectionRule(Flowable):
    def __init__(self, width: float = CONTENT_W, color=BLUE, thickness: float = 1.2):
        super().__init__()
        self.width = width
        self.height = 5
        self.color = color
        self.thickness = thickness

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.height / 2, self.width, self.height / 2)


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "VisionTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=30,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "VisionSubtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11.5,
            leading=16,
            textColor=MUTED,
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "SubsectionHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=DEEP_BLUE,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=12.4,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=INK,
            spaceAfter=3,
        ),
        "table": ParagraphStyle(
            "TableText",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=INK,
        ),
        "table_bold": ParagraphStyle(
            "TableBold",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=INK,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=INK,
            backColor=LIGHT_BLUE,
            borderColor=BLUE,
            borderWidth=0.6,
            borderPadding=8,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=11.6,
            textColor=INK,
            backColor=GREY_BG,
            borderColor=LINE,
            borderWidth=0.5,
            borderPadding=7,
            spaceAfter=8,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "right": ParagraphStyle(
            "Right",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=MUTED,
            alignment=TA_RIGHT,
        ),
    }


S = styles()


def p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


def bullet(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(item, "body"), leftIndent=10, bulletColor=BLUE) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=16,
        bulletFontName="Helvetica",
        bulletFontSize=5,
        spaceAfter=5,
    )


def num(items: list[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(p(item, "body"), leftIndent=10) for item in items],
        bulletType="1",
        leftIndent=18,
        spaceAfter=5,
    )


def cell(text: str, bold: bool = False) -> Paragraph:
    return p(text, "table_bold" if bold else "table")


def table(headers: list[str], rows: list[list[str]], widths: list[float] | None = None) -> Table:
    if widths is None:
        widths = [CONTENT_W / len(headers)] * len(headers)
    data = [[cell(h, True) for h in headers]]
    data.extend([[cell(v) for v in row] for row in rows])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), INK),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GREY_BG]),
            ]
        )
    )
    return t


def callout(title: str, body: str, fill=GREY_BG, border=LINE) -> Table:
    data = [[p(f"<b>{title}</b><br/>{body}", "small")]]
    t = Table(data, colWidths=[CONTENT_W], hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), fill),
                ("BOX", (0, 0), (-1, -1), 0.6, border),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return t


def section(story: list, title: str) -> None:
    story.append(Spacer(1, 4))
    story.append(p(title, "h1"))
    story.append(SectionRule())
    story.append(Spacer(1, 3))


def subsection(story: list, title: str) -> None:
    story.append(p(title, "h2"))


def header_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(LEFT_MARGIN, PAGE_H - 11 * mm, "COSMOS Space Ecosystem Vision")
    canvas.drawRightString(PAGE_W - RIGHT_MARGIN, PAGE_H - 11 * mm, "Confidential founder strategy")
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(LEFT_MARGIN, PAGE_H - 13 * mm, PAGE_W - RIGHT_MARGIN, PAGE_H - 13 * mm)
    canvas.drawCentredString(PAGE_W / 2, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


def cover_header_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(DEEP_BLUE)
    canvas.rect(0, PAGE_H - 34 * mm, PAGE_W, 34 * mm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawRightString(PAGE_W - RIGHT_MARGIN, PAGE_H - 13 * mm, "CONFIDENTIAL FOUNDER VISION")
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(PAGE_W / 2, 9 * mm, "COSMOS - RecycleGURU - Advanced Materials - Reusable Space Logistics")
    canvas.restoreState()


def build_story() -> list:
    story: list = []

    story.append(Spacer(1, 50))
    story.append(p("COSMOS SPACE ECOSYSTEM VISION", "title"))
    story.append(
        p(
            "A founder strategy for building an Indian space-industrial ecosystem through "
            "AI-assisted engineering software, sovereign aerospace materials, reusable launch "
            "vehicles, orbital manufacturing, and deep-space logistics.",
            "subtitle",
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        callout(
            "Working identity",
            "COSMOS - To Infinity And Beyond is treated here as an internal working phrase. "
            "Before public use, the phrase and any mark around it should receive trademark and brand clearance.",
            fill=LIGHT_AMBER,
            border=AMBER,
        )
    )
    story.append(
        table(
            ["Item", "Definition"],
            [
                ["Founder vision", "Build a private Indian space ecosystem spanning materials, propulsion, launch, reusable return, orbital manufacturing, and deep-space communications."],
                ["Core companies", "COSMOS for engineering intelligence, rocket systems, reusable transport, and space logistics. RecycleGURU for aerospace materials, recycling, process control, and certification intelligence."],
                ["Strategic partner concept", "A future PPP or JV with HMT/HMT Machine Tools or a government-supported successor entity to scale advanced metals production using public-sector land, capital, and manufacturing infrastructure."],
                ["Prepared on", date.today().isoformat()],
                ["Status", "Founder vision document - strategic planning draft, not legal, safety, export-control, or investment advice."],
            ],
            [42 * mm, CONTENT_W - 42 * mm],
        )
    )
    story.append(Spacer(1, 16))
    story.append(
        p(
            "North Star: build the industrial and software backbone that lets India design, "
            "manufacture, validate, launch, recover, and reuse space systems at national scale.",
            "quote",
        )
    )
    story.append(PageBreak())

    section(story, "1. Executive Thesis")
    story.append(
        p(
            "The COSMOS ecosystem should not be presented first as a shuttle dream, Mars dream, "
            "or broad space empire. The investable thesis is narrower and stronger: India needs "
            "sovereign aerospace materials, validated propulsion hardware, traceable engineering "
            "software, and eventually reusable space logistics. COSMOS and RecycleGURU together "
            "can become the industrial control layer for that future."
        )
    )
    story.append(
        p(
            "The long-term destination is ambitious: reusable cargo and human-rated shuttle variants, "
            "orbital manufacturing stations, lunar and Mars logistics, and deep-space communications. "
            "The path to that destination must start with materials, process certification, propulsion "
            "hardware, and validated engineering documentation."
        )
    )
    story.append(
        table(
            ["Founder Ambition", "Investor Translation"],
            [
                ["Build rockets and shuttles", "First prove propulsion, materials, testing, and cadence."],
                ["Use AI to design engines", "Build a traceable computational engineering system, not an unchecked chatbot."],
                ["Control aerospace materials", "Create qualified materials, material passports, recurring sales, and supply security."],
                ["Create orbital factories", "First build reliable upmass, gentle downmass, station logistics, and customers."],
                ["Serve Moon and Mars", "Develop deep-space transport after LEO logistics and reentry recovery are repeatable."],
            ],
            [55 * mm, CONTENT_W - 55 * mm],
        )
    )

    section(story, "2. India Market Context")
    story.append(
        p(
            "The timing is favorable. Indian Space Policy 2023 encourages private participation "
            "across the space value chain and explicitly recognizes private development and operation "
            "of space transportation systems, including launch vehicles, shuttles, reusable systems, "
            "recoverable systems, and launch infrastructure, subject to IN-SPACe authorization. "
            "Official statements also project India's space economy growing from about USD 8.4 billion "
            "in 2023 to about USD 44 billion by 2033 and USD 100 billion by 2040."
        )
    )
    story.append(
        p(
            "In parallel, India is pursuing critical-mineral security and recycling under the National "
            "Critical Mineral Mission. This makes RecycleGURU strategically relevant beyond COSMOS: "
            "aerospace materials are not only an input cost, they are national industrial infrastructure."
        )
    )
    story.append(
        table(
            ["Signal", "Meaning For The Ecosystem"],
            [
                ["Private space policy", "COSMOS can be framed as an IN-SPACe-aligned private space transportation and engineering company."],
                ["Space economy growth target", "The macro story supports launch, satellite, ground infrastructure, in-space services, and advanced manufacturing demand."],
                ["Critical mineral mission", "RecycleGURU can align with national priorities in recycling, processing, R&D, patents, and resilient supply chains."],
                ["HMT strategic manufacturing role", "A PPP/JV proposal can be positioned around machine tools, foundry capability, defence, aerospace, advanced manufacturing, and PSU modernization."],
                ["ISRO RLV demonstrations", "India has technical and policy interest in reusable winged return systems, validating the long-term shuttle direction."],
            ],
            [47 * mm, CONTENT_W - 47 * mm],
        )
    )

    section(story, "3. The Ecosystem Flywheel")
    story.append(
        p(
            "The durable advantage comes from linking software, materials, manufacturing, testing, "
            "and flight operations into one closed loop. Each company strengthens the other. "
            "RecycleGURU supplies materials and process intelligence. COSMOS uses those materials "
            "inside engines and vehicles. Flight and test data feed back into material qualification "
            "and engineering software."
        )
    )
    story.append(
        table(
            ["Layer", "Role", "Recurring Revenue Potential"],
            [
                ["RecycleGURU Materials", "Aerospace-grade alloys, powders, billets, forgings, heat treatment, HIP, NDT, and material passports.", "Material sales, certification fees, testing services, capacity reservation, scrap take-back."],
                ["COSMOS Software", "RAG knowledge base, deterministic solvers, CAD generation, topology optimization, external simulation comparison, release documentation.", "Enterprise licenses, engineering reports, solver modules, traceability subscriptions."],
                ["COSMOS Propulsion", "Regeneratively cooled chambers, injectors, igniters, manifolds, turbopump parts, reusable engine families.", "Engine sales, launch internalization, MRO, test services, design validation packages."],
                ["COSMOS Launch", "Reusable launch vehicles, cargo logistics, human-rated transport, launch services.", "Launch contracts, station logistics, defence and commercial payload transport."],
                ["Orbital Infrastructure", "Manufacturing stations, docking, cargo return, crew ferry, microgravity production support.", "Station lease, power/thermal/data services, downmass logistics, premium return cargo."],
                ["Deep Space Network", "Lunar/Mars communications, relay, navigation, data services.", "Service contracts, government anchor customers, commercial relay subscriptions."],
            ],
            [33 * mm, 80 * mm, CONTENT_W - 113 * mm],
        )
    )
    story.append(KeepTogether([
        p("Strategic principle", "h2"),
        callout(
            "Build from the bottleneck outward",
            "The first defensible bottleneck is not the shuttle. It is qualified materials plus propulsion process intelligence. Once COSMOS can design, build, test, document, and improve engines faster than others, the vehicle vision becomes credible.",
            fill=LIGHT_GREEN,
            border=GREEN,
        ),
    ]))

    section(story, "4. COSMOS: Computational Engineering And Propulsion")
    story.append(
        p(
            "COSMOS should be developed as a proprietary computational engineering platform "
            "for rocket propulsion and eventually whole-vehicle design. It should not imitate "
            "another company's system. Its unique pattern should be traceable, evidence-bound, "
            "solver-verified, and human-reviewed."
        )
    )
    story.append(
        table(
            ["COSMOS Capability", "What It Must Do"],
            [
                ["Knowledge/RAG foundation", "Extract approved equations, assumptions, constants, materials, limits, manufacturing constraints, and references."],
                ["Engineering solvers", "Compute thrust, chamber pressure, mass flow, mixture ratio, throat area, expansion ratio, heat flux, cooling, pressure drop, stresses, and margins."],
                ["CAD generators", "Generate parametric thrust chambers, throats, nozzles, regen channels, injectors, igniters, manifolds, mounts, and interfaces."],
                ["Topology optimization", "Improve manifolds, jackets, supports, brackets, and additive structures, then reconstruct candidates into clean CAD and reanalyze."],
                ["Simulation loop", "Export cases to Fluent, OpenFOAM, Ansys, Nastran, Abaqus, NX, and related tools; ingest results for side-by-side comparison."],
                ["Engineering documentation", "Generate design basis, calculation package, CAD report, analysis report, change report, and manufacturing release passport."],
                ["Human release gate", "Block 3D-printable release until external review, evidence, checksums, waivers, and signoff are complete."],
            ],
            [43 * mm, CONTENT_W - 43 * mm],
        )
    )
    story.append(
        p(
            "The first COSMOS product should be a narrow propulsion design loop: propellant pair, "
            "thrust, chamber pressure, burn time, cooling strategy, and material constraints in; "
            "validated design state, calculation package, parametric CAD, analysis package, and "
            "manufacturing-review documentation out."
        )
    )

    section(story, "5. RecycleGURU: Materials As The Strategic Base")
    story.append(
        p(
            "RecycleGURU should not be treated as a commodity recycling business. It should be "
            "built as an aerospace materials and process-intelligence company. The objective is "
            "to reduce import dependency and create qualified domestic supply for rocket, aviation, "
            "defence, energy, and advanced manufacturing customers."
        )
    )
    story.append(
        table(
            ["Material Family", "Strategic Use"],
            [
                ["Inconel 718 and nickel superalloys", "Injectors, manifolds, turbopump components, hot structures, engine mounts, high-temperature AM parts."],
                ["CuCrZr and GRCop-type copper alloys", "Regeneratively cooled chamber liners, throat regions, heat exchangers, high-heat-flux components."],
                ["Al-Li alloys", "Lightweight tanks and structural elements where qualification supports use."],
                ["6000 and 7000 series aluminium, including 7075", "Vehicle structures, tooling, fixtures, ground support, avionics bays, and qualified non-hot structural uses."],
                ["Powder metallurgy and AM powders", "Repeatable additive manufacturing for engine parts, manifolds, channels, injector heads, and heat exchangers."],
                ["Closed-loop scrap streams", "Recover high-value alloy content from aerospace offcuts, failed builds, machining scrap, and end-of-life strategic components."],
            ],
            [55 * mm, CONTENT_W - 55 * mm],
        )
    )
    story.append(
        p(
            "The economic leverage is schedule control. Material access influences design iteration, "
            "hot-fire cadence, inventory cost, repair time, and manufacturing reliability. COSMOS "
            "can only become a high-cadence launch company if its critical materials and process "
            "qualification are predictable."
        )
    )

    section(story, "6. PPP/JV Strategy With HMT")
    story.append(
        p(
            "The proposed public-private strategy should avoid permanently transferring RecycleGURU's "
            "core IP into a government-controlled vehicle. The stronger structure is an IP-controlled "
            "PPP or joint venture: RecycleGURU owns the metallurgy intelligence and licenses it into "
            "a scaling platform where HMT or a government-backed entity contributes land, capital, "
            "machine-tool infrastructure, public-sector credibility, and manufacturing depth."
        )
    )
    story.append(
        table(
            ["Entity", "Contribution", "Protected Interest"],
            [
                ["RecycleGURU IP HoldCo", "Alloy/process know-how, process-control software, certification datasets, material passports, QA algorithms, AM parameters.", "Retains ownership of core IP; earns royalties, license fees, and technical-service revenue."],
                ["HMT-RecycleGURU Advanced Materials JV", "Scaled production, plants, machinery, workforce, customer delivery, government-aligned expansion.", "Uses licensed IP under field, territory, quality, and sublicensing limits."],
                ["HMT / public partner", "Land, capital, equipment ecosystem, PSU credibility, strategic-sector access.", "Receives industrial revival, national capability, jobs, export potential, and revenue share."],
                ["COSMOS", "Anchor demand for propulsion and reusable vehicle materials; real test and flight feedback.", "Gets priority capacity, material traceability, and faster engineering iteration."],
                ["External customers", "Aerospace, defence, rail, energy, nuclear, heavy engineering, and advanced manufacturing demand.", "Access to domestic qualified materials and certification support."],
            ],
            [37 * mm, 76 * mm, CONTENT_W - 113 * mm],
        )
    )
    story.append(
        callout(
            "PPP caution",
            "A government-linked PPP will require formal legal, procurement, competition, national-security, export-control, and cabinet/ministry-level navigation. The founder should prepare a national-industrial proposal, not a private backroom merger proposal.",
            fill=LIGHT_RED,
            border=RED,
        )
    )

    section(story, "7. Revenue Model")
    story.append(
        p(
            "The strongest business model is recurring industrial revenue first, launch revenue later. "
            "Launch revenue can be large but lumpy and technically risky. Materials, process services, "
            "qualification, testing, and software evidence can compound earlier."
        )
    )
    story.append(
        table(
            ["Revenue Stream", "Buyer", "Why It Recurs"],
            [
                ["Qualified metal sales", "Aerospace, defence, launch, energy, advanced manufacturing", "Programs need repeat batches across development, qualification, production, and sustainment."],
                ["AM powder supply", "Rocket companies, AM bureaus, defence labs, turbine/thermal companies", "Powder lots must be repeated, tested, documented, and matched to machine parameters."],
                ["Material passport and certification", "Customers requiring traceability", "Every batch, heat, powder lot, and critical part needs documentation."],
                ["Testing and NDT services", "Internal and external engineering teams", "Tensile, fatigue, creep, CT, metallography, chemistry, HIP, heat-treatment validation recur per lot and per program."],
                ["Capacity reservation", "Strategic customers", "Customers pay to secure furnace, atomization, HIP, AM, and inspection capacity."],
                ["COSMOS software modules", "Internal teams, selected aerospace customers", "Design, simulation comparison, traceability, and documentation are ongoing workflows."],
                ["Launch and logistics", "Satellite, station, defence, research, manufacturing customers", "Once vehicle reliability exists, transport becomes recurring demand."],
            ],
            [42 * mm, 58 * mm, CONTENT_W - 100 * mm],
        )
    )

    section(story, "8. Reusable Shuttle Direction")
    story.append(
        p(
            "The shuttle vision is a long-term product family, not the first product. Its strategic "
            "case is gentle, precise, reusable downmass. A gliding or lifting-body return vehicle "
            "can serve humans, delicate cargo, microgravity-manufactured products, lab samples, "
            "biomedical payloads, optical materials, semiconductor crystals, and high-value station "
            "equipment better than simple ballistic return."
        )
    )
    story.append(
        table(
            ["Vehicle Concept", "Strategic Role", "Key Reality Check"],
            [
                ["Cargo shuttle - up to 70 ton target", "Autonomous or crew-capable cargo return for orbital manufacturing and station logistics.", "This is far beyond the historical Space Shuttle payload-to-LEO class and requires major propulsion, TPS, structure, landing, and operations maturity."],
                ["Human-rated shuttle", "Convert cargo volume to human transport for up to 15 people, life support, lab, lavatory, docking hatch, EVA hatch, and limited cargo.", "Human rating must follow after repeated cargo flights, abort systems, reliability data, and regulatory maturity."],
                ["Deep-space station logistics", "Use modular LEO stations as aggregation points for lunar and Mars transport.", "Requires propulsion depots, radiation protection, closed-loop life support, docking, power, thermal, and deep-space communications."],
                ["Moon/Mars communications", "Relay, navigation, and internet-like services for lunar and Mars activity.", "Likely needs government anchor customers and phased deployment from cislunar service outward."],
            ],
            [42 * mm, 64 * mm, CONTENT_W - 106 * mm],
        )
    )
    story.append(
        p(
            "Compared with vertical propulsive landing systems such as Starship, a shuttle-like "
            "vehicle is less likely to win pure bulk-cargo cost at first. Its premium market is "
            "valuable downmass, crew comfort, precise runway recovery, lower landing shock, and "
            "fast post-landing cargo access. That is the market COSMOS should investigate before "
            "committing to a heavy shuttle architecture."
        )
    )

    section(story, "9. Investor-Grade Honest Review")
    story.append(
        table(
            ["Dimension", "Assessment"],
            [
                ["Vision", "Very high upside. It is nationally relevant and industrially important."],
                ["Fundability as one giant story", "Weak. Rockets, AI software, metallurgy, PPP, shuttles, stations, Mars, and communications are too broad for an initial financing narrative."],
                ["Fundability as a wedge", "Strong if narrowed to aerospace materials plus propulsion validation plus COSMOS engineering documentation."],
                ["Primary risk", "Execution overload. Each sub-vision can consume an entire company."],
                ["Primary moat", "Qualified materials, process datasets, material passports, engine hot-fire feedback, and traceable engineering software."],
                ["Investor ask", "Show one qualified material, one engine component, one hot-fire/test loop, one paying customer, and one recurring-revenue contract."],
            ],
            [48 * mm, CONTENT_W - 48 * mm],
        )
    )
    story.append(
        p(
            "The investor path is to prove credibility with narrow milestones. The founder should "
            "not hide the large vision, but should sequence it. Investors fund believable momentum, "
            "not only final-state ambition."
        )
    )

    section(story, "10. Phased Roadmap")
    story.append(
        table(
            ["Phase", "Time Horizon", "Focus", "Proof"],
            [
                ["0", "0-18 months", "COSMOS architecture, RAG knowledge foundation, finite numeric validation, first material database, first process-control dataset.", "Working software prototype and controlled material test records."],
                ["1", "18-36 months", "Inconel 718 AM powder or process route, CuCrZr/GRCop-type copper route, material passports, coupon testing.", "Repeatable batches, test reports, third-party lab validation."],
                ["2", "3-5 years", "Regeneratively cooled chamber, injector, igniter, parametric CAD, CFD/FEA export/import, hot-fire loop.", "Engine component test with traceable design-to-test documentation."],
                ["3", "5-8 years", "External aerospace/defence material sales and JV/PPP scaling proposal.", "Recurring material revenue and government/PSU-backed scaling pathway."],
                ["4", "8-12 years", "Small launch vehicle or propulsion subsystem supplier role; reusable demonstrators.", "Operational cadence, customer contracts, reliability data."],
                ["5", "12-20 years", "Reusable launch architecture, cargo return demonstrator, station logistics.", "Repeat reentry/recovery, protected downmass, contracted station service."],
                ["6", "20-30 years", "Human-rated shuttle-class system, orbital manufacturing stations, lunar/Mars logistics and relay.", "Regulated human flight, station lease revenue, deep-space service contracts."],
            ],
            [18 * mm, 27 * mm, 88 * mm, CONTENT_W - 133 * mm],
        )
    )

    section(story, "11. Operating Doctrine")
    story.append(
        num(
            [
                "Prove materials before claiming vehicles.",
                "Prove process control before claiming production scale.",
                "Prove hot-fire and failure analysis before claiming engine maturity.",
                "Prove documentation and traceability before claiming certification readiness.",
                "Prove cargo return before claiming human-rated shuttle capability.",
                "Prove LEO logistics before claiming Moon and Mars transport.",
                "Keep core IP in private control; license it carefully into PPP/JV structures.",
                "Use government partnerships for scale, not for giving away proprietary intelligence.",
            ]
        )
    )
    story.append(
        callout(
            "Founder discipline",
            "The long vision is acceptable only if the near-term plan is disciplined. The first empire to build is not in orbit. It is a disciplined engineering, materials, and validation engine on Earth.",
            fill=LIGHT_GREEN,
            border=GREEN,
        )
    )

    section(story, "12. Immediate Action Plan")
    story.append(
        table(
            ["Action", "Owner", "Output"],
            [
                ["Define RecycleGURU's first two material beachheads.", "Founder + materials advisor", "One-page material thesis for Inconel 718 and CuCrZr/GRCop-type copper route."],
                ["Create IP map.", "Founder + IP counsel", "Trade secret register, patent candidates, freedom-to-operate review, licensing boundaries."],
                ["Create COSMOS design-state schema.", "COSMOS engineering", "Traceable data object linking requirements, equations, materials, CAD, analysis, and documents."],
                ["Build material passport template.", "RecycleGURU + COSMOS", "Batch record, chemistry, heat treatment, NDT, test results, certificate, allowed-use status."],
                ["Prepare HMT/PPP concept note.", "Founder + policy/legal advisor", "National industrial proposal showing jobs, strategic supply, export potential, PSU revival, and protected private IP."],
                ["Find first non-COSMOS customer.", "Business development", "LOI/MOU for qualified material, testing, or process service revenue."],
                ["Run first integrated demo.", "Both companies", "Material batch -> component design -> CAD -> analysis -> test report -> material passport."],
            ],
            [55 * mm, 42 * mm, CONTENT_W - 97 * mm],
        )
    )

    section(story, "13. Risks And Controls")
    story.append(
        table(
            ["Risk", "Control"],
            [
                ["Scope explosion", "Fund and execute one technical wedge at a time."],
                ["PPP bureaucracy", "Use clear governance, private IP licensing, milestones, exit clauses, and defined operating authority."],
                ["IP leakage", "Separate IP HoldCo, trade secret controls, limited licenses, audit rights, employee invention assignment, and supplier NDAs."],
                ["Material qualification delay", "Start with coupon/test data, third-party labs, narrow part families, and repeatable process windows."],
                ["Regulatory/export-control exposure", "Build legal review into every launch, reentry, material export, and defence customer workflow."],
                ["Investor skepticism", "Show paid contracts, test results, batch repeatability, and narrow milestone completion."],
                ["Brand/trademark risk", "Clear public slogans and marks before use; keep working phrases internal until counsel approves."],
            ],
            [46 * mm, CONTENT_W - 46 * mm],
        )
    )

    section(story, "14. Final Founder Vision")
    story.append(
        p(
            "COSMOS should become the company that turns India's space ambition into a repeatable "
            "industrial system: requirements become validated design states; materials become "
            "certified and traceable; engines become test-backed products; vehicles become reusable "
            "logistics platforms; orbital stations become leased manufacturing infrastructure; and "
            "deep-space communications become the nervous system connecting Earth, Moon, and Mars."
        )
    )
    story.append(
        p(
            "RecycleGURU is the industrial root. COSMOS software is the intelligence layer. COSMOS "
            "propulsion and vehicles are the proof. Orbital infrastructure is the long-term business. "
            "The founder's task is to sequence this correctly so that each decade funds and validates "
            "the next."
        )
    )
    story.append(
        p(
            "The goal is not to copy any existing company or historical vehicle. The goal is to build "
            "an Indian space ecosystem with its own materials base, its own computational engineering "
            "pattern, its own reusable logistics architecture, and its own economic logic."
        )
    )

    section(story, "References")
    refs = [
        "Indian Space Policy 2023, ISRO / Department of Space: https://www.isro.gov.in/media_isro/pdf/IndianSpacePolicy2023.pdf",
        "PIB Department of Space statement on India's space economy projection, 2026: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2248424&lang=1&reg=1",
        "PIB National Critical Mineral Mission note, 2025: https://www.pib.gov.in/PressNoteDetails.aspx?ModuleId=3&NoteId=155158&lang=2&reg=3",
        "Ministry of Heavy Industries profile for HMT Machine Tools Limited: https://heavyindustries.gov.in/en/hmt-machine-tools-ltd-0",
        "PPP in India FAQ, Ministry of Finance / Department of Economic Affairs: https://www.pppinindia.gov.in/faqs",
        "ISRO RLV-LEX3 reusable launch vehicle landing experiment: https://www.isro.gov.in/ISRO_Completes_RLV_Technology_Demonstrations_RLV-LEX3.html",
        "NASA Space Shuttle reference: https://www.nasa.gov/reference/the-space-shuttle/",
        "NASA Glenn, Space Shuttle as a glider: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/space-shuttle-as-a-glider/",
        "NASA NTRS GRCop-42 development and hot-fire testing: https://ntrs.nasa.gov/citations/20190030433",
    ]
    story.append(bullet(refs))
    story.append(
        p(
            "Note: This document captures a founder strategy and vision based on the conversation and "
            "public references above. It is not legal advice, investment advice, export-control advice, "
            "flight-safety certification, or a substitute for formal aerospace engineering review.",
            "callout",
        )
    )
    return story


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="COSMOS Space Ecosystem Vision",
        author="COSMOS Founder Strategy",
        subject="Vision for COSMOS, RecycleGURU, aerospace materials, reusable launch, orbital infrastructure",
    )
    story = build_story()
    doc.build(story, onFirstPage=cover_header_footer, onLaterPages=header_footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
