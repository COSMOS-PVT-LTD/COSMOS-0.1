"""Representative engineering corpus for semantic retrieval evaluation."""

from __future__ import annotations

CORPUS_MANIFEST_VERSION = "1.0.0"

REPRESENTATIVE_ENGINEERING_CORPUS: dict[str, str] = {
    "DOC-PROP-LOX": (
        "# Liquid Oxygen Propulsion\n\n"
        "LOX serves as the primary oxidizer in bipropellant rocket engines. "
        "Chamber pressure and mass flow govern thrust performance."
    ),
    "DOC-PROP-LH2": (
        "# Liquid Hydrogen Fuel\n\n"
        "LH2 fuel offers high specific impulse when paired with liquid oxygen. "
        "Cryogenic storage and turbopump feed systems are required."
    ),
    "DOC-PROP-RP1": (
        "# RP-1 Kerosene Propulsion\n\n"
        "RP-1 rocket propellant is used in gas generator and staged combustion cycles. "
        "Combustion stability depends on injector design."
    ),
    "DOC-THERMO-ENTROPY": (
        "# Thermodynamics Fundamentals\n\n"
        "Entropy and enthalpy describe energy conversion in propulsion cycles. "
        "Second law limits achievable efficiency."
    ),
    "DOC-THERMO-CYCLES": (
        "# Thermodynamic Cycles\n\n"
        "Brayton and Rankine cycles model turbine and heat exchange behavior "
        "for auxiliary power and regenerative cooling loops."
    ),
    "DOC-FLUID-REYNOLDS": (
        "# Fluid Mechanics — Reynolds Number\n\n"
        "Reynolds number predicts laminar versus turbulent flow in feed lines "
        "and cooling channels."
    ),
    "DOC-FLUID-MACH": (
        "# Compressible Flow\n\n"
        "Mach number and area ratio determine nozzle expansion and shock behavior "
        "in supersonic exhaust flow."
    ),
    "DOC-COMB-INSTABILITY": (
        "# Combustion Instability\n\n"
        "Combustion driven oscillations can damage injector plates. "
        "Chamber pressure oscillations require acoustic damping."
    ),
    "DOC-HEAT-CONDUCTION": (
        "# Heat Conduction\n\n"
        "Thermal conduction through chamber walls requires material limits "
        "and regenerative cooling analysis."
    ),
    "DOC-HEAT-CONVECTION": (
        "# Convective Heat Transfer\n\n"
        "Convection coefficients dominate coolant channel heat pickup "
        "in actively cooled nozzles."
    ),
    "DOC-HEAT-RADIATION": (
        "# Radiative Heat Transfer\n\n"
        "Radiation becomes significant at high exhaust temperature "
        "and in plume impingement zones."
    ),
    "DOC-MAT-COMPOSITE": (
        "# Composite Materials\n\n"
        "Carbon composite structures provide high strength-to-weight for "
        "intertank and payload adapters."
    ),
    "DOC-STRUCT-STRESS": (
        "# Structural Stress Analysis\n\n"
        "Stress and strain limits govern tank wall thickness under "
        "pressurization and launch loads."
    ),
    "DOC-AERO-CONTROL": (
        "# Aerospace Control Systems\n\n"
        "Thrust vector control and attitude control coordinate vehicle guidance "
        "during ascent."
    ),
    "DOC-EQ-IMPULSE": (
        "# Specific Impulse Equation\n\n"
        "Isp equals effective exhaust velocity divided by standard gravity. "
        "It measures propulsion efficiency."
    ),
}

SEMANTIC_EVALUATION_CASES: tuple[dict[str, object], ...] = (
    {
        "query_id": "Q-LOX-SYN",
        "query_text": "liquid oxygen oxidizer bipropellant",
        "relevant_document_ids": ["DOC-PROP-LOX"],
        "notes": "terminology variation — LOX vs liquid oxygen",
    },
    {
        "query_id": "Q-LH2-SYN",
        "query_text": "cryogenic hydrogen fuel high impulse",
        "relevant_document_ids": ["DOC-PROP-LH2"],
        "notes": "synonym LH2",
    },
    {
        "query_id": "Q-ISP-ABBREV",
        "query_text": "specific impulse efficiency propulsion",
        "relevant_document_ids": ["DOC-EQ-IMPULSE", "DOC-PROP-LH2"],
        "notes": "abbreviation isp",
    },
    {
        "query_id": "Q-CHAMBER-LEX",
        "query_text": "chamber pressure oscillation combustion",
        "relevant_document_ids": ["DOC-COMB-INSTABILITY", "DOC-PROP-LOX"],
        "notes": "semantic should beat pure keyword on instability doc",
    },
    {
        "query_id": "Q-HEAT-TRANSFER",
        "query_text": "thermal energy transfer cooling nozzle",
        "relevant_document_ids": [
            "DOC-HEAT-CONDUCTION",
            "DOC-HEAT-CONVECTION",
            "DOC-HEAT-RADIATION",
        ],
        "notes": "concept-to-document retrieval",
    },
    {
        "query_id": "Q-FLUID-TURB",
        "query_text": "turbulent flow in feed lines",
        "relevant_document_ids": ["DOC-FLUID-REYNOLDS"],
        "notes": "fluids domain",
    },
    {
        "query_id": "Q-STRUCT-LOAD",
        "query_text": "structural load strain tank wall",
        "relevant_document_ids": ["DOC-STRUCT-STRESS"],
        "notes": "structures domain",
    },
    {
        "query_id": "Q-TVC",
        "query_text": "thrust vector attitude guidance",
        "relevant_document_ids": ["DOC-AERO-CONTROL"],
        "notes": "aerospace systems",
    },
)
