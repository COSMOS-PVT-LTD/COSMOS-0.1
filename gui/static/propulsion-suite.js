/**
 * Rocket Engine propulsion design suite — GUI only.
 * Catalog and design state come from the API. No Physics imports or equations.
 */
(function () {
  "use strict";

  const STAGE_FORMS = {
    design_project: ["workflow-e2e"],
    requirements: ["engine-definition"],
    propellants: ["propellants"],
    cycle: ["cycle"],
    operating_point: ["phase3"],
    thermochemistry: ["phase3"],
    performance: ["phase3"],
    injector: ["injector-design"],
    chamber: ["chamber-sizing"],
    thermal: ["chamber-sizing", "bartz"],
    cooling: ["cooling-design"],
    nozzle: ["nozzle-design"],
    structure: ["thin-wall"],
    materials: ["chamber-sizing"],
    performance_summary: ["phase6"],
    consistency: ["phase6"],
    design_review: ["phase6"],
  };

  const PHYSICS_TOOL_IDS = ["nozzle-flow", "heat-transfer", "structures"];

  const MODULE_FORMS = {
    "workflow-analysis": ["workflow-e2e"],
    "engine-definition": ["engine-definition"],
    "propellants-combustion": ["propellants"],
    "chamber-sizing": ["chamber-sizing"],
    "nozzle-flow": ["isentropic", "area-mach"],
    "nozzle-contour": ["nozzle-design"],
    "heat-transfer": ["cooling-design", "bartz"],
    injectors: ["injector-design"],
    structures: ["thin-wall"],
    "cycle-feed": ["cycle"],
  };

  const state = {
    catalog: [],
    stages: [],
    design: null,
    workflow: null,
    lastPhase: null,
    activeKind: "stage",
    activeId: "design_project",
    drafts: {},
    dirty: false,
    busy: false,
    resultGeneration: 0,
    presentationResult: null,
    presentationComparison: null,
    presentationDisplayableAsCurrent: undefined,
    presentationLoading: false,
    draftUndo: [],
    draftRedo: [],
    supplementalDirty: null,
  };
  const fieldBeforeEdit = new Map();

  function $(id) {
    return document.getElementById(id);
  }

  function api() {
    return window.CosmosAPI;
  }

  function applyBusyState() {
    document.querySelectorAll(".design-context-actions button, .design-context-actions select, #suite-nav button, #suite-forms input, #suite-forms select, #suite-forms button").forEach((el) => {
      if (state.busy) {
        if (!el.hasAttribute("data-workspace-lock")) el.dataset.workspaceLock = el.disabled ? "disabled" : "enabled";
        el.disabled = true;
      } else if (el.hasAttribute("data-workspace-lock")) {
        el.disabled = el.dataset.workspaceLock === "disabled";
        delete el.dataset.workspaceLock;
      }
    });
  }

  async function runWorkspaceAction(action) {
    if (state.busy) return;
    const trigger = document.activeElement;
    state.busy = true;
    publishShellContext();
    state.resultGeneration += 1;
    applyBusyState();
    try {
      await action();
    } catch (error) {
      setResult({ok: false, error: {code: "WorkbenchActionError", message: error.message,
        action: "Your edits are retained. Retry the action."}});
    } finally {
      state.busy = false;
      publishShellContext();
      applyBusyState();
      if (document.activeElement === document.body && trigger) {
        const replacement = trigger.isConnected ? trigger :
          (trigger.id ? $(trigger.id) : [...$("suite-forms").querySelectorAll("button")]
            .find((button) => button.textContent === trigger.textContent));
        replacement?.focus({preventScroll: true});
      }
    }
  }

  function bindAction(button, action) {
    button?.addEventListener("click", () => runWorkspaceAction(action));
  }

  function draftKey(id) {
    const aliases = {"ed-name": "wf-name", "ed-pc": "wf-pc", "ed-thrust": "wf-thrust",
      "ed-of": "wf-of", "ed-eps": "wf-eps", "pr-of": "wf-of", "pr-ox": "wf-ox", "pr-fuel": "wf-fuel"};
    return aliases[id] || id;
  }

  function restoreDrafts() {
    $("suite-forms")?.querySelectorAll("input[id], select[id]").forEach((el) => {
      const key = draftKey(el.id);
      if (Object.hasOwn(state.drafts, key)) el.value = state.drafts[key];
    });
    $("suite-forms")?.querySelectorAll(".suite-card").forEach(card => card.updateFilmFields?.());
    updateThermochemistryFields();
    $("suite-forms")?.querySelectorAll("input[id], select[id]").forEach(el => fieldBeforeEdit.set(el.id, el.value));
  }

  function trackDraft(event) {
    const el = event.target;
    if (!el.id || !el.matches("input, select")) return;
    if (Object.hasOwn(state.drafts, draftKey(el.id)) && state.drafts[draftKey(el.id)] === el.value) return;
    state.draftRedo = [];
    state.draftUndo.push({designId: state.design?.design_id, revision: state.design?.revision,
      drafts: {...state.drafts}, dirty: state.dirty, field: el.id, value: fieldBeforeEdit.get(el.id)});
    if (state.draftUndo.length > 100) state.draftUndo.shift();
    fieldBeforeEdit.set(el.id, el.value);
    state.drafts[draftKey(el.id)] = el.value;
    state.dirty = true;
    if (el.id === "wf-thermo-mode") updateThermochemistryFields();
    renderContextBar();
  }

  function canLeaveDesign() {
    if (state.supplementalDirty?.()) {
      setResult({ok:false,error:{code:"UnsavedCycleInputs",message:"Run/retain or explicitly discard the cycle/operating draft before changing workspace or baseline."}});
      return false;
    }
    return !state.design || !state.dirty || window.confirm("This design has unsaved edits. Leave and discard them? Cancel to save first.");
  }

  function saveEdits() {
    const drafts = {...state.drafts};
    const edits = {base_revision: state.design.revision, editor_drafts: drafts};
    const thermo = thermochemistryDraftInputs(drafts);
    if (thermo) edits.thermochemistry_configuration = thermo;
    const subsystemInputs = subsystemDraftInputs(drafts);
    if (Object.keys(subsystemInputs).length) edits.subsystem_inputs = subsystemInputs;
    const numeric = (key) => drafts[key].trim() === "" ? null : Number(drafts[key]);
    const requirements = {};
    const quantityFields = {"wf-pc": ["target_chamber_pressure", "bar"],
      "wf-thrust": ["target_thrust", "kN"], "wf-pa": ["ambient_pressure", "Pa"]};
    Object.entries(quantityFields).forEach(([key, [field, unit]]) => {
      if (!Object.hasOwn(drafts, key)) return;
      const value = numeric(key);
      requirements[field] = value == null ? null : {magnitude: value, unit_symbol: unit};
      delete drafts[key];
    });
    for (const [key, field] of [["wf-of", "mixture_ratio"], ["wf-eps", "expansion_ratio"]]) {
      if (Object.hasOwn(drafts, key)) {
        requirements[field] = numeric(key);
        delete drafts[key];
      }
    }
    if (Object.keys(requirements).length) edits.requirements = requirements;
    if (Object.hasOwn(drafts, "wf-name")) {
      edits.name = drafts["wf-name"];
      delete drafts["wf-name"];
    }
    if (Object.hasOwn(drafts, "wf-ox") || Object.hasOwn(drafts, "wf-fuel")) {
      const cfg = state.design.propellant_configuration || {};
      edits.propellants = {oxidizer_id: drafts["wf-ox"] ?? cfg.oxidizer_id ?? "",
        fuel_id: drafts["wf-fuel"] ?? cfg.fuel_id ?? "",
        mixture_ratio: requirements.mixture_ratio ?? cfg.mixture_ratio ?? null};
      delete drafts["wf-ox"];
      delete drafts["wf-fuel"];
    }
    if (Object.hasOwn(drafts, "cy-type")) {
      edits.cycle_type = drafts["cy-type"];
      delete drafts["cy-type"];
    }
    return edits;
  }

  function qtyText(value, fallbackUnit) {
    if (value == null) return "—";
    if (typeof value === "object") {
      const mag = value.magnitude != null ? value.magnitude : value.value;
      const unit =
        (value.unit && value.unit.symbol) ||
        value.unit_symbol ||
        (typeof value.unit === "string" ? value.unit : "") ||
        fallbackUnit ||
        "";
      if (mag == null) return "—";
      return `${mag} ${unit}`.trim();
    }
    return String(value);
  }

  function displayEngineQty(value, displayUnit) {
    if (value == null || typeof value !== "object" || value.magnitude == null) return "—";
    const sym = (value.unit && value.unit.symbol) || "";
    const mag = Number(value.magnitude);
    if (!Number.isFinite(mag)) return "—";
    if (displayUnit === "bar" && sym === "Pa") return `${(mag / 1e5).toFixed(2)} bar`;
    if (displayUnit === "kN" && sym === "N") return `${(mag / 1000).toFixed(2)} kN`;
    if (displayUnit === "kN" && sym === "kN") return `${mag.toFixed(2)} kN`;
    if (displayUnit === "bar" && sym === "bar") return `${mag.toFixed(2)} bar`;
    return qtyText(value);
  }

  function quantityInputValue(value, displayUnit) {
    if (value == null || typeof value !== "object" || value.magnitude == null) return "";
    const sym = (value.unit && value.unit.symbol) || "";
    const mag = Number(value.magnitude);
    if (Number.isNaN(mag)) return "";
    if (displayUnit === "bar" && sym === "Pa") return String(mag / 1e5);
    if (displayUnit === "kN" && sym === "N") return String(mag / 1000);
    return String(mag);
  }

  function setFieldValue(id, value) {
    const el = $(id);
    if (el) el.value = value == null ? "" : value;
  }

  function applyDesignToForms(design) {
    if (!design) return;
    const thermo = design.thermochemistry_configuration || {};
    setFieldValue("wf-thermo-mode", defaultThermochemistryMode());
    setFieldValue("wf-fuel-temp", thermo.fuel_temperature_k);
    setFieldValue("wf-ox-temp", thermo.oxidizer_temperature_k);
    updateThermochemistryFields();
    for (const stage of ["injector", "nozzle", "cooling"]) {
      const inputs = design.subsystem_inputs?.[stage] || {};
      subsystemFields(stage).forEach(([key]) => setFieldValue(`sub-${stage}-${key}`, inputs[key]));
    }
    const req = design.requirements || {};
    const cfg = design.propellant_configuration || {};
    const op = design.operating_point || {};
    setFieldValue("wf-name", design.name);
    setFieldValue("ed-name", design.name);
    setFieldValue("wf-pc", quantityInputValue(req.target_chamber_pressure, "bar"));
    setFieldValue("ed-pc", quantityInputValue(req.target_chamber_pressure, "bar"));
    setFieldValue("wf-thrust", quantityInputValue(req.target_thrust, "kN"));
    setFieldValue("ed-thrust", quantityInputValue(req.target_thrust, "kN"));
    setFieldValue("wf-pa", quantityInputValue(req.ambient_pressure, "Pa"));
    const of = req.mixture_ratio ?? cfg.mixture_ratio;
    ["wf-of", "ed-of", "pr-of"].forEach((id) => setFieldValue(id, of));
    ["wf-eps", "ed-eps"].forEach((id) => setFieldValue(id, req.expansion_ratio));
    setFieldValue("wf-tc", quantityInputValue(op.chamber_temperature, "K"));
    setFieldValue("wf-gamma", op.gamma);
    setFieldValue("wf-mw", op.molecular_weight);
    const thermal = {...design.thermal_design, ...design.subsystem_inputs?.thermal};
    const structural = {...design.structural_design, ...design.subsystem_inputs?.structure};
    const chamber = design.chamber_design || {};
    const nozzle = design.nozzle_design || {};
    Object.entries({
      "wf-lstar": design.subsystem_inputs?.chamber?.characteristic_length_m ?? chamber.characteristic_length_m,
      "wf-cr": design.subsystem_inputs?.chamber?.contraction_ratio ?? chamber.contraction_ratio,
      "wf-at": nozzle.throat_area_m2, "wf-twall": structural.wall_thickness_m,
      "wf-pout": structural.external_pressure_pa ?? quantityInputValue(structural.external_pressure, "Pa"),
      "wf-tmaterial": structural.material_temperature_k,
      "wf-pressure-model": structural.pressure_model || "THIN_WALL",
      "wf-mu": thermal.viscosity_pa_s, "wf-k": thermal.conductivity_w_m_k,
      "wf-cp": thermal.cp_j_kg_k, "wf-tw": thermal.wall_temperature_k,
      "wf-curvature": thermal.throat_curvature_radius_m ?? nozzle.throat_curvature_radius_m,
      "wf-material": design.subsystem_inputs?.materials?.material_id ?? design.material_selection?.chamber_material_id,
      "wf-gas-property-mode": design.subsystem_inputs?.thermal?.property_mode || "EXPLICIT",
    }).forEach(([id, value]) => setFieldValue(id, value));
    if (cfg.oxidizer_id && $("wf-ox")) $("wf-ox").value = cfg.oxidizer_id;
    if (cfg.fuel_id && $("wf-fuel")) $("wf-fuel").value = cfg.fuel_id;
    if (cfg.oxidizer_id && $("pr-ox")) $("pr-ox").value = cfg.oxidizer_id;
    if (cfg.fuel_id && $("pr-fuel")) $("pr-fuel").value = cfg.fuel_id;
    setFieldValue("cy-type", design.cycle_configuration?.cycle_type);
  }

  function formatScalar(item) {
    if (item == null) return "—";
    if (typeof item !== "object") return String(item);
    if (Array.isArray(item)) return item.map(formatScalar).join("; ");
    if (item.magnitude != null || item.value != null) return qtyText(item);
    try {
      return JSON.stringify(item);
    } catch {
      return String(item);
    }
  }

  function formatResult(payload) {
    if (payload?.status === "STALE" && payload.ok !== false) {
      return "STALE — stored result for earlier inputs; not a current answer.\nRecalculate before using it.\n\n" +
        formatResult({...payload, status: "HISTORICAL"});
    }
    if (payload?.message && payload.ok !== false) {
      return `${payload.status || "SAVED"}\n${payload.message}`;
    }
    if (!payload || payload.ok === false) {
      const err = payload?.error || payload?.errors?.[0] || {};
      return [
        payload?.status === "NOT_RUN" ? "NOT RUN — missing inputs" : "CALCULATION FAILED",
        "",
        "Reason:",
        err.message || "Unknown engineering failure.",
        "",
        "Code:",
        err.code || "unknown",
        "",
        "Action:",
        err.action || "Correct the input.",
      ].join("\n");
    }
    const model = payload.model || {model_id: payload.model_id, source: payload.provenance?.source};
    const lines = [
      "MODEL",
      `Model ID: ${model.model_id || ""}`,
      `Name: ${model.model_name || ""}`,
      `Source: ${model.source || ""}`,
      `Verification: ${payload.verification?.result || payload.verification?.status || ""}`,
      `Validation: ${payload.validation?.status || "NOT_CLAIMED"}`,
      `Validity: ${payload.validity?.status || "UNKNOWN"}`,
      "",
      "INPUTS",
    ];
    Object.entries(payload.inputs || {}).forEach(([key, item]) => {
      lines.push(`${key}: ${formatScalar(item)}`);
    });
    lines.push("", "OUTPUTS");
    Object.entries(payload.outputs || {}).forEach(([key, item]) => {
      lines.push(`${key}: ${formatScalar(item)}`);
    });
    if ((payload.warnings || []).length) {
      lines.push("", "WARNINGS");
      payload.warnings.forEach((w) => lines.push(`- ${w}`));
    }
    if ((payload.assumptions || []).length) {
      lines.push("", "ASSUMPTIONS");
      payload.assumptions.forEach((w) => lines.push(`- ${w}`));
    }
    return lines.join("\n");
  }

  const rawResultInspection = (payload, title = "Raw received result DTO (JSON) · source keys and precision") => {
    const details = document.createElement("details");
    details.className = "suite-source-inspection";
    const summary = document.createElement("summary");
    summary.textContent = title;
    details.appendChild(summary);
    const pre = document.createElement("pre");
    pre.tabIndex = 0;
    pre.role = "region";
    pre.ariaLabel = `${title} — scrollable source content`;
    let placeholders = false;
    try {
      pre.textContent = JSON.stringify(payload ?? null, (_key, value) => {
        if (typeof value === "number" && !Number.isFinite(value)) {placeholders = true; return `[nonfinite: ${String(value)}]`;}
        return value;
      }, 2);
    } catch {pre.textContent = "Original DTO could not be serialized. No scientific values were inferred.";}
    if (placeholders) summary.textContent += " · nonfinite placeholders, not canonical finite data";
    details.appendChild(pre);
    return details;
  };

  // Additive DOM view; formatResult's existing string interface stays unchanged.
  const renderResultPresentation = (payload, {stageId = payload?.stage_id, diagnostics = true, displayableAsCurrent, targetComparison} = {}) => {
    const result = payload || {};
    const host = document.createElement("section");
    host.className = "suite-result-presentation";
    const add = (parent, tag, text, className) => {
      const element = document.createElement(tag);
      if (text != null) element.textContent = String(text);
      if (className) element.className = className;
      parent.appendChild(element);
      return element;
    };
    const status = result.status || "UNKNOWN";
    const current = status === "CURRENT" && result.ok !== false && displayableAsCurrent !== false;
    const performance = stageId === "performance" || String(result.calculation_type || "").startsWith("performance.");
    const unavailable = displayableAsCurrent === false ? "API envelope does not permit display as a current answer" : `${status} is not a current answer`;
    add(host, "p", current ? "CURRENT — source result freshness; not experimental validation." :
      `${status} — computed values unavailable: ${unavailable}. Inspect the unchanged stored DTO below.`, "suite-note");
    const metadata = add(host, "dl", null, "suite-result-metadata");
    const identity = [
      ["Freshness", status], ["Stage", stageId || "Not supplied"],
      ["Display eligibility", displayableAsCurrent === undefined ? "No envelope flag reported — source status applies" : String(displayableAsCurrent)],
      ["Result ID", result.result_id ?? "Not supplied"], ["Design revision", result.design_revision ?? "Not supplied"],
      ["Model", result.model_id || result.model?.model_id || "Not supplied"],
      ["Model version", result.model_version || result.model?.model_version || "Not supplied"],
      ["Source", result.provenance?.source || result.model?.source || "Not supplied"],
      ["Reference", result.provenance?.reference || "Not supplied"],
      ["Validity", result.validity?.status || "UNKNOWN"],
      ["Verification", result.verification?.status || result.verification?.result || "UNKNOWN"],
      ["Validation", result.validation?.status || "NOT_CLAIMED"],
    ];
    identity.forEach(([label, value]) => {add(metadata, "dt", label); add(metadata, "dd", value);});
    const unitText = item => (item?.unit && typeof item.unit === "object" ? item.unit.symbol : item?.unit) || item?.unit_symbol || "";
    const magnitude = item => item?.magnitude ?? item?.value;
    const isQuantity = item => item && typeof item === "object" && !Array.isArray(item) &&
      (Object.hasOwn(item, "magnitude") || Object.hasOwn(item, "value"));
    const scalar = item => {
      if (item == null) return "Unavailable — not supplied";
      if (typeof item === "number" && !Number.isFinite(item)) return "Unavailable — nonfinite value";
      if (typeof item === "object") return "Nested data — inspect raw DTO";
      return String(item);
    };
    const labels = {
      chamber_pressure: "Chamber pressure", chamber_temperature: "Chamber temperature", ambient_pressure: "Ambient pressure",
      gamma: "Gamma", molar_mass: "Molar mass", throat_area_m2: "Throat area", expansion_ratio: "Expansion ratio",
      fuel_temperature_k: "Fuel temperature", oxidizer_temperature_k: "Oxidizer temperature",
    };
    const table = (title, values, outputs = false) => {
      const scroll = add(host, "div", null, "suite-table-scroll");
      scroll.tabIndex = 0;
      scroll.role = "region";
      scroll.ariaLabel = `${title} — quantity table; scroll horizontally when needed`;
      const element = add(scroll, "table", null, "suite-quantity-table");
      add(element, "caption", title);
      const head = add(element, "thead");
      const header = add(head, "tr");
      ["Quantity / field", "Value", "Supplied unit", "Source key"].forEach(label => {const th = add(header, "th", label); th.scope = "col";});
      const body = add(element, "tbody");
      let rows = 0, limited = false;
      const row = (key, value, label = key, calculatedThrust = false) => {
        if (rows >= 64) {limited = true; return;}
        rows += 1;
        const quantity = isQuantity(value);
        const suppliedUnit = quantity ? unitText(value) : "";
        const finiteQuantity = quantity && typeof magnitude(value) === "number" && Number.isFinite(magnitude(value));
        let shown = quantity ? (finiteQuantity ? String(magnitude(value)) : "Unavailable — missing/nonfinite magnitude") : scalar(value);
        if (outputs && !current) shown = `Unavailable — ${unavailable}`;
        else if (calculatedThrust && (!finiteQuantity || !suppliedUnit)) shown = "Unavailable — finite quantity and supplied unit required";
        const tr = add(body, "tr");
        const th = add(tr, "th", label); th.scope = "row";
        const valueCell = add(tr, "td", shown);
        if ((finiteQuantity && shown === String(magnitude(value))) || (typeof value === "number" && Number.isFinite(value) && shown === String(value))) {
          valueCell.className = "suite-quantity-value";
        }
        add(tr, "td", suppliedUnit || "Not supplied"); add(tr, "td", key);
      };
      const walk = (value, key, depth = 0) => {
        if (rows >= 64) {limited = true; return;}
        if (value == null || typeof value !== "object" || isQuantity(value)) {row(key, value, Object.hasOwn(labels, key) ? labels[key] : key); return;}
        if (depth >= 3) {row(key, value); limited = true; return;}
        const entries = Array.isArray(value) ? value.slice(0, 8).map((item, index) => [String(index), item]) : Object.entries(value);
        if (Array.isArray(value) && value.length > 8) limited = true;
        if (!entries.length) row(key, null);
        for (const [child, item] of entries) {
          if (rows >= 64) {limited = true; break;}
          walk(item, key ? `${key}.${child}` : child, depth + 1);
        }
      };
      if (outputs && performance) row("thrust", values?.thrust, "Calculated thrust", true);
      for (const [key, value] of Object.entries(values || {})) {
        if (outputs && performance && key === "thrust") continue;
        walk(value, key);
      }
      if (!rows) row("—", null, "No supplied fields");
      if (limited) add(scroll, "p", "Summary limited to 64 rows, 3 nested levels and 8 array entries. All received fields remain in the raw DTO.", "suite-note");
    };
    if (performance) {
      const available = current && targetComparison?.status === 'AVAILABLE' && targetComparison.result_id === result.result_id && targetComparison.design_revision === result.design_revision;
      if (available) {
        table('Requested versus calculated thrust (backend comparison; no sizing or acceptance)', targetComparison.quantities);
        add(host, 'p', targetComparison.scope, 'suite-note');
        add(host, 'p', 'Tolerance assessment: '+targetComparison.tolerance_assessment+'. Requested/calculated values are not hardware acceptance.', 'suite-note');
      } else add(host, 'p', 'Target mismatch unavailable: '+(targetComparison?.reason || 'Reload the exact current persisted performance result. No browser calculation or silent sizing is performed.'), 'suite-note');
    }
    table(current ? "Supplied operating conditions / inputs" : "Stored operating conditions / inputs (not a current result)", result.inputs);
    table(current ? "Calculated outputs (source CURRENT)" : `Outputs unavailable as current — ${status}`, result.outputs, true);
    for (const [name, items] of [["Warnings", result.warnings], ["Assumptions", result.assumptions]]) {
      if (!Array.isArray(items) || !items.length) continue;
      add(host, "h5", name);
      const list = add(host, "ul");
      items.slice(0, 12).forEach(item => add(list, "li", scalar(item)));
      if (items.length > 12) add(list, "li", "Additional entries retained in raw DTO.");
    }
    if (diagnostics && (result.ok === false || ["FAILED", "OUT_OF_RANGE", "NOT_RUN"].includes(status))) {
      add(host, "pre", formatResult({...result, ok: false}), "suite-result-diagnostics");
    }
    host.appendChild(rawResultInspection(payload));
    return host;
  };

  function renderStructuredPhase(payload, {displayableAsCurrent} = {}) {
    const host = document.createElement("div");
    host.className = "suite-structured";
    const status = document.createElement("p");
    status.className = payload.ok ? "suite-note" : "suite-note error";
    const verdict =
      payload.stages &&
      payload.stages.design_review &&
      payload.stages.design_review.outputs &&
      payload.stages.design_review.outputs.review_verdict;
    status.textContent = [
      payload.execution_ok ? "EXECUTION SUCCEEDED" : "EXECUTION FAILED",
      `phase_status=${payload.phase_status || "UNKNOWN"}`,
      `workflow_complete=${payload.workflow_complete === true}`,
      `readiness=${payload.engineering_readiness || "INCOMPLETE"}`,
      `validation=${payload.validation_level || "NOT_CLAIMED"}`,
      verdict ? `review_verdict=${verdict}` : "",
      payload.design_id ? `design=${payload.design_id}` : "",
    ]
      .filter(Boolean)
      .join(" · ");
    host.appendChild(status);
    if ((payload.input_requests || []).length) {
      const section = document.createElement("section");
      const title = document.createElement("h4"); title.textContent = "Inputs and actions required — ready stages were still calculated";
      section.appendChild(title);
      const list = document.createElement("ul");
      payload.input_requests.forEach(item => {
        const row = document.createElement("li");
        row.textContent = `${item.stage_id}: ${(item.fields || []).join(", ")}${item.blocked_by?.length ? " · upstream: "+item.blocked_by.join(", ") : ""}. ${item.action}`;
        list.appendChild(row);
      });
      section.appendChild(list);host.appendChild(section);
    }
    if ((payload.default_assumptions || []).length) {
      const assumptions = document.createElement("div");
      assumptions.className = "suite-assumption-banner";
      assumptions.textContent = "USING DEFAULT ASSUMPTION";
      const list = document.createElement("ul");
      payload.default_assumptions.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = `${item.stage_id}${item.field ? "." + item.field : ""} — ${item.reason}`;
        list.appendChild(li);
      });
      assumptions.appendChild(list);
      host.appendChild(assumptions);
    }
    const keys = Object.keys(payload.stages || {});
    keys.forEach((stageId) => {
      const stage = payload.stages[stageId];
      const card = document.createElement("section");
      card.className = "suite-stage-result";
      const h = document.createElement("h4");
      h.textContent = `${stageId} · ${stage.status || ""} · ${stage.model_id || ""}`;
      card.appendChild(h);
      if (["FAILED", "OUT_OF_RANGE"].includes(stage.status) || stage.ok === false) {
        const pre = document.createElement("pre");
        pre.textContent = formatResult({...stage, ok: false});
        card.appendChild(pre);
      }
      const isSubsystem = ["injector", "nozzle", "cooling"].includes(stageId);
      if (isSubsystem && displayableAsCurrent !== false) appendSubsystemVisual(card, stage);
      if (stageId === "thermochemistry" && displayableAsCurrent !== false) appendCeaVisual(card, stage);
      card.appendChild(renderResultPresentation(stage, {stageId, displayableAsCurrent, diagnostics: !["FAILED", "OUT_OF_RANGE"].includes(stage.status) && stage.ok !== false}));
      host.appendChild(card);
    });
    host.appendChild(rawResultInspection(payload, "Raw received phase DTO (JSON) · all stage/source fields"));
    return host;
  }

  function appendCeaVisual(host, stage) {
    if (stage.status !== "CURRENT" || !stage.outputs?.rocket_stations?.chamber) return;
    const note = document.createElement("p");
    note.className = "suite-note";
    note.textContent = `NASA CEA ${stage.model_version} · converged equilibrium · ideal infinite-area combustor · validation NOT_CLAIMED. Gamma is the CEA isentropic exponent, not a constant Cp/Cv approximation.`;
    host.appendChild(note);
    const table = document.createElement("table");
    table.className = "suite-station-table";
    const caption = document.createElement("caption");
    caption.textContent = "CEA stations (SI); Cp and conductivity below use frozen transport properties";
    table.appendChild(caption);
    const columns = [["Station", null], ["P [Pa]", "pressure_pa"], ["T [K]", "temperature_k"],
      ["Mach", "mach"], ["γs", "gamma"], ["Ve [m/s]", "velocity_m_s"],
      ["Cp [J/(kg K)]", "cp_frozen_j_kg_k"], ["μ [Pa s]", "viscosity_pa_s"], ["k [W/(m K)]", "conductivity_frozen_w_m_k"]];
    const header = document.createElement("tr");
    columns.forEach(([label]) => { const th = document.createElement("th"); th.textContent = label; th.scope = "col"; header.appendChild(th); });
    table.appendChild(header);
    ["chamber", "throat", "exit"].forEach((name) => {
      const station = stage.outputs.rocket_stations[name];
      const row = document.createElement("tr");
      columns.forEach(([, key]) => { const td = document.createElement(key ? "td" : "th");
        td.textContent = key ? Number(station[key]).toPrecision(6) : name;
        if (!key) td.scope = "row";
        row.appendChild(td); });
      table.appendChild(row);
    });
    const scroll = document.createElement("div");
    scroll.className = "suite-table-scroll";
    scroll.appendChild(table);
    host.appendChild(scroll);
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "Chamber composition · mole fractions ≥ 10⁻⁶ (full trace species retained in JSON export)";
    details.appendChild(summary);
    const pre = document.createElement("pre");
    pre.textContent = Object.entries(stage.outputs.mole_fractions || {}).filter(([, value]) => value >= 1e-6)
      .sort((a, b) => b[1] - a[1]).map(([name, value]) => `${name.padEnd(20)} ${Number(value).toPrecision(8)}`).join("\n");
    details.appendChild(pre);
    host.appendChild(details);
  }

  function setResult(payload, {displayableAsCurrent, targetComparison} = {}) {
    state.presentationResult = payload == null ? null : JSON.parse(JSON.stringify(payload));
    state.presentationDisplayableAsCurrent = displayableAsCurrent;
    state.presentationComparison = targetComparison == null ? null : JSON.parse(JSON.stringify(targetComparison));
    publishPresentation();
    state.resultGeneration += 1; // invalidate any pending stored-result request
    const el = $("suite-result");
    if (!el) return;
    el.classList.toggle("error", Boolean(payload && (payload.ok === false || ["FAILED", "OUT_OF_RANGE"].includes(payload.status))));
    el.innerHTML = "";
    if (payload && payload.stages) {
      el.appendChild(renderStructuredPhase(payload, {displayableAsCurrent}));
      return;
    }
    if (payload?.stage_id === "thermochemistry" && payload.status === "CURRENT" && displayableAsCurrent !== false && payload.outputs?.rocket_stations?.chamber) {
      appendCeaVisual(el, payload);
      el.appendChild(renderResultPresentation(payload, {displayableAsCurrent, targetComparison}));
      return;
    }
    if (payload && ["injector", "nozzle", "cooling"].includes(payload.stage_id)) {
      if (displayableAsCurrent !== false) appendSubsystemVisual(el, payload);
      el.appendChild(renderResultPresentation(payload, {displayableAsCurrent, targetComparison}));
      return;
    }
    if (payload && (payload.outputs || payload.inputs || payload.stage_id)) {
      el.appendChild(renderResultPresentation(payload, {displayableAsCurrent, targetComparison}));
      return;
    }
    el.textContent = formatResult(payload);
  }

  function rememberDesignId(id) {
    if (!id) return;
    try {
      sessionStorage.setItem("cosmos_active_design_id", id);
    } catch {
      /* convenience only */
    }
  }

  function rememberedDesignId() {
    try {
      return sessionStorage.getItem("cosmos_active_design_id");
    } catch {
      return null;
    }
  }

  function publishShellContext() {
    if (window.CosmosShellUI) window.dispatchEvent(new CustomEvent('cosmos:design-context', {detail: shellContext()}));
    publishPresentation();
  }

  function renderContextBar() {
    publishShellContext();
    const nameEl = $("design-context-name");
    if (!nameEl) return;
    const design = state.design;
    const draftStatus = $("design-context-inputs");
    if (draftStatus) draftStatus.textContent = state.dirty ? "Unsaved edits — Save before leaving" :
      (Object.keys(state.drafts).length ? "Saved editor drafts — separate from results" : "");
    if (!design) {
      nameEl.textContent = "No active design";
      $("design-context-revision").textContent = "REV —";
      $("design-context-state").textContent = "NONE";
      $("design-context-pc").textContent = "Pc —";
      $("design-context-of").textContent = "O/F —";
      $("design-context-thrust").textContent = "Target thrust —";
      $("design-context-props").textContent = "Propellants —";
      return;
    }
    const req = design.requirements || {};
    const cfg = design.propellant_configuration || {};
    nameEl.textContent = design.name || "Untitled";
    $("design-context-revision").textContent = `REV ${design.revision ?? 0}`;
    $("design-context-state").textContent = (design.status && design.status.value) || "draft";
    $("design-context-pc").textContent = `Pc ${displayEngineQty(req.target_chamber_pressure, "bar")}`;
    $("design-context-of").textContent = `O/F ${req.mixture_ratio ?? cfg.mixture_ratio ?? "—"}`;
    $("design-context-thrust").textContent = `Target thrust ${displayEngineQty(req.target_thrust, "kN")}`;
    const ox = cfg.oxidizer_id || "—";
    const fuel = cfg.fuel_id || "—";
    $("design-context-props").textContent = `Propellants ${ox} / ${fuel}`;
  }

  async function refreshDesign(id, {loadResult = false, discardDrafts = false} = {}) {
    state.resultGeneration += 1;
    const payload = await api().getDesign(id);
    if (!payload.ok && payload.error) {
      setResult(payload);
      return null;
    }
    const switched = state.design?.design_id !== payload.design.design_id;
    const opened = window.CosmosManagedProjects?.context?.editorHeads.get(id);
    if (!switched && state.dirty && !discardDrafts && payload.authority && opened &&
        payload.authority.commit_id !== opened.commit_id) {
      setResult({ok:false,error:{code:'MANAGED_DRAFT_CONFLICT',message:'A newer saved commit exists. Your draft and original expected head are retained. Explicitly reload/discard or reconcile before saving.'}});
      return null;
    }
    if (payload.authority && !window.CosmosManagedProjects?.acceptEditor(payload)) {
      setResult({ok:false,error:{code:'STALE_MANAGED_RESPONSE',message:'A newer saved commit is known. Editor drafts are retained; reload the exact project context.'}});
      return null;
    }
    if (switched || state.design?.revision !== payload.design.revision) {state.draftUndo = []; state.draftRedo = [];}
    state.design = payload.design;
    if (switched || payload.authority && (!state.dirty || discardDrafts)) {
      state.drafts = {...(payload.design.editor_drafts || {})};
      state.dirty = false;
    }
    rememberDesignId(payload.design.design_id);
    const wf = await api().getWorkflow(payload.design.design_id);
    state.workflow = wf.workflow || null;
    renderContextBar();
    renderNav();
    fillDesignPicker();
    showActiveWorkspace(loadResult);
    applyBusyState();
    return payload.design;
  }

  async function fillDesignPicker() {
    const select = $("design-picker");
    if (!select) return;
    const listed = await api().listDesigns();
    const designs = listed.designs || [];
    const currentId = state.design && state.design.design_id;
    select.innerHTML = "";
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = designs.length ? "Open a saved design…" : "No saved designs";
    select.appendChild(blank);
    designs.forEach((row) => {
      const opt = document.createElement("option");
      opt.value = row.design_id;
      opt.textContent = `${row.name} · rev ${row.revision} · ${row.state}`;
      if (row.design_id === currentId) opt.selected = true;
      select.appendChild(opt);
    });
  }

  function renderBoard(workflow) {
    const board = $("wf-board");
    if (!board) return;
    board.innerHTML = "";
    if (!workflow || !workflow.nodes) {
      board.textContent = "Workflow board appears after a design is opened or created.";
      return;
    }
    const table = document.createElement("table");
    table.className = "suite-board-table";
    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>Stage</th><th>Model coverage</th><th>Calculation state</th><th>Current source?</th><th>Inputs / next action</th></tr>";
    table.appendChild(thead);
    const tbody = document.createElement("tbody");
    workflow.nodes.forEach((node) => {
      const tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" +
        node.name +
        "</td><td>" +
        node.implementation_status +
        "</td><td>" +
        node.status +
        "</td><td>" +
        (node.result_is_current ? "yes" : "no") +
        "</td>";
      const action = document.createElement("td");
      action.textContent = node.input_request ? [...node.input_request.fields, ...node.input_request.blocked_by].join(", ") :
        (node.diagnostics || []).filter(item => item.code).map(item => item.message).join("; ") || node.engineering_note || "";
      tr.appendChild(action);
      if (node.status === "STALE") tr.classList.add("is-stale");
      if (node.status === "CURRENT") tr.classList.add("is-current");
      if (node.implementation_status === "NOT_IMPLEMENTED") tr.classList.add("is-ni");
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    const readiness = document.createElement("p");
    readiness.className = "suite-note";
    readiness.textContent = `Engineering readiness: ${workflow.engineering_readiness || "INCOMPLETE"} · Workflow complete: ${workflow.workflow_complete === true} · Validation: ${workflow.validation_level || "NOT_CLAIMED"}. CURRENT means input freshness.`;
    board.appendChild(readiness);
    const legend = document.createElement("p");legend.className="suite-note";
    legend.textContent="Model coverage and calculation state are separate. PARTIAL means an implemented model has stated scope limits. NOT_CALCULATED means no current run/input set. FAILED means a calculation was attempted and failed. CURRENT means freshness, not physical validation.";
    board.appendChild(legend);
    board.appendChild(table);
  }

  function field(label, attrs) {
    const wrap = document.createElement("label");
    wrap.appendChild(document.createTextNode(label));
    const input = document.createElement("input");
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") input.setAttribute(k, v);
    });
    wrap.appendChild(input);
    fieldBeforeEdit.set(input.id, input.value);
    return { wrap, input };
  }

  function selectField(label, options, attrs) {
    const wrap = document.createElement("label");
    wrap.appendChild(document.createTextNode(label));
    const sel = document.createElement("select");
    Object.entries(attrs || {}).forEach(([k, v]) => sel.setAttribute(k, v));
    options.forEach(([value, text]) => {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = text;
      sel.appendChild(opt);
    });
    wrap.appendChild(sel);
    fieldBeforeEdit.set(sel.id, sel.value);
    return { wrap, input: sel };
  }

  function makeCard(title, buildFn) {
    const card = document.createElement("div");
    card.className = "suite-card";
    const h = document.createElement("h3");
    h.textContent = title;
    card.appendChild(h);
    buildFn(card);
    return card;
  }

  function requireDesign() {
    if (state.design && state.design.design_id) return state.design.design_id;
    setResult({
      ok: false,
      error: {
        code: "NoActiveDesign",
        message: "Create or open a design first. Run never creates a new design.",
        action: "Use New Design in the context bar.",
      },
    });
    return null;
  }

  function num(id) {
    const element = $(id);
    if (!element || element.value.trim() === "") return null;
    const value = Number(element.value);
    return Number.isFinite(value) ? value : null;
  }

  function phase4Inputs(prefix) {
    const read = (suffix) => {
      const id = `${prefix}-${suffix}`;
      if ($(id) || prefix !== "wf") return num(id);
      const value = state.drafts?.[id];
      return value === undefined || value.trim() === "" ? null : Number(value);
    };
    const gasMode=$(`${prefix}-gas-property-mode`)?.value || (prefix === "wf" ? state.drafts?.["wf-gas-property-mode"] : null) || null;
    return {
      characteristic_length_m: read("lstar"),
      contraction_ratio: read("cr"),
      wall_thickness_m: read(prefix === "wf" ? "twall" : "t"),
      material_id: $(`${prefix}-material`)?.value || (prefix === "wf" ? state.drafts?.["wf-material"] : null) || null,
      external_pressure_pa: read("pout"),
      external_pressure_source: "Explicit outer-wall pressure entered in the engineering form.",
      material_temperature_k: read("tmaterial"),
      viscosity_pa_s: gasMode === "CEA_CHAMBER_FROZEN_TRANSPORT" ? null : read("mu"),
      conductivity_w_m_k: gasMode === "CEA_CHAMBER_FROZEN_TRANSPORT" ? null : read("k"),
      cp_j_kg_k: gasMode === "CEA_CHAMBER_FROZEN_TRANSPORT" ? null : read("cp"),
      wall_temperature_k: read("tw"),
      throat_curvature_radius_m: read("curvature"),
      gas_property_mode: gasMode,
      pressure_model: $(`${prefix}-pressure-model`)?.value || (prefix === "wf" ? state.drafts?.["wf-pressure-model"] : null) || null,
    };
  }

  function engineeringBoundaryFields(prefix) {
    return [
      selectField("Pressure stress model (smooth cylinder only)", [["THIN_WALL","Thin-wall membrane (r/t ≥ 10)"],["LAME_CLOSED_ENDS","Lamé elastic cylinder, pressure-loaded closed ends"]], {id:`${prefix}-pressure-model`}),
      selectField("Thermal gas-property source (explicit choice)", [["EXPLICIT","Explicit gas-property inputs"],["CEA_CHAMBER_FROZEN_TRANSPORT","CURRENT CEA chamber frozen-composition transport"]], {id:`${prefix}-gas-property-mode`}),
      field("Outside wall pressure [Pa] (required; 0 for vacuum)", {type: "number", step: "any", id: `${prefix}-pout`}),
      field("Material temperature [K]", {type: "number", step: "any", id: `${prefix}-tmaterial`}),
      field("Gas viscosity [Pa·s]", {type: "number", step: "any", id: `${prefix}-mu`}),
      field("Gas conductivity [W/(m·K)]", {type: "number", step: "any", id: `${prefix}-k`}),
      field("Gas Cp [J/(kg·K)]", {type: "number", step: "any", id: `${prefix}-cp`}),
      field("Wall temperature [K]", {type: "number", step: "any", id: `${prefix}-tw`}),
      field("Throat curvature radius [m] (optional)", {type: "number", step: "any", id: `${prefix}-curvature`}),
    ];
  }

  async function createNewDesign() {
    if (!canLeaveDesign()) return;
    const initialDrafts = !state.design ? {...state.drafts} : null;
    const name = ($("wf-name") && $("wf-name").value) || "Rocket Engine Analysis";
    const created = await api().createDesign({
      name,
      description: "Rocket Engine workbench design",
    });
    if (created.ok === false) {
      setResult(created);
      return;
    }
    rememberDesignId(created.design.design_id);
    await refreshDesign(created.design.design_id);
    if (initialDrafts && Object.keys(initialDrafts).length) {
      state.drafts = initialDrafts;
      state.dirty = true;
      restoreDrafts();
      renderContextBar();
    }
    renderNav();
    setResult({
      ok: true,
      model: { model_id: "design.create" },
      outputs: { design_id: { value: created.design.design_id, unit: "1" }, name: { value: created.design.name, unit: "1" } },
    });
  }

  async function saveActive() {
    if (state.supplementalDirty?.() && !canLeaveDesign()) return;
    const id = requireDesign();
    if (!id) return;
    const edits = saveEdits();
    const saved = await api().saveDesign(id, edits);
    if (saved.ok === false) {
      setResult(saved);
      return;
    }
    state.drafts = {...edits.editor_drafts};
    state.dirty = false;
    await refreshDesign(saved.design.design_id);
    setResult({
      ok: true,
      status: "SAVED",
      message: `Design saved · revision ${saved.design.revision}. Requirements/selections are applied; other editor inputs are saved drafts until you run the relevant calculation. No solver was run.`,
    });
  }

  async function cloneActive() {
    if (!canLeaveDesign()) return;
    const id = requireDesign();
    if (!id) return;
    const cloned = await api().cloneDesign(id, `${state.design.name} (copy)`);
    if (cloned.ok === false) {
      setResult(cloned);
      return;
    }
    await refreshDesign(cloned.design.design_id);
    setResult({
      ok: true,
      model: { model_id: "design.clone" },
      outputs: { design_id: { value: cloned.design.design_id, unit: "1" } },
    });
  }

  async function persistWorkflowInputs() {
    const id = requireDesign();
    if (!id) return null;
    return persistDesignInputs(id, {
      target_chamber_pressure: num("wf-pc") == null ? null : { magnitude: num("wf-pc"), unit_symbol: "bar" },
      target_thrust: num("wf-thrust") == null ? null : { magnitude: num("wf-thrust"), unit_symbol: "kN" },
      mixture_ratio: num("wf-of"),
      expansion_ratio: num("wf-eps"),
      ambient_pressure: num("wf-pa") == null ? null : { magnitude: num("wf-pa"), unit_symbol: "Pa" },
      notes: "GUI workflow inputs. Thermochemistry assumptions are explicit.",
    }, {
      oxidizer_id: $("wf-ox")?.value || "",
      fuel_id: $("wf-fuel")?.value || "",
      mixture_ratio: num("wf-of"),
    });
  }

  async function persistDesignInputs(id, requirements, propellants) {
    const drafts = {...state.drafts};
    const thermo = thermochemistryDraftInputs(drafts);
    ["wf-name", "wf-pc", "wf-thrust", "wf-pa", "wf-of", "wf-eps", "wf-ox", "wf-fuel"]
      .forEach((key) => delete drafts[key]);
    const saved = await api().saveDesign(id, {
      base_revision: state.design.revision,
      name: $("wf-name")?.value ?? state.drafts?.["wf-name"] ?? state.design.name,
      requirements, propellants, editor_drafts: drafts,
      subsystem_inputs: subsystemDraftInputs(drafts),
      ...(thermo ? {thermochemistry_configuration: thermo} : {}),
    });
    if (saved.ok === false) return saved;
    state.drafts = drafts;
    state.dirty = false;
    await refreshDesign(id);
    return { ok: true };
  }

  function missingThermochemistryInputs(inputs) {
    // The API supports partial updates; this full-form action must not silently
    // reuse an old operating point when the user explicitly leaves a field blank.
    if (inputs.thermochemistry_configuration?.mode === "nasa_cea") {
      const cfg = inputs.thermochemistry_configuration;
      if ([cfg.fuel_temperature_k, cfg.oxidizer_temperature_k].every(value => Number.isFinite(value) && value > 0)) return null;
      return {ok: false, status: "NOT_RUN", error: {code: "MissingExplicitInputs",
        message: "CEA requires explicit fuel and oxidizer inlet temperatures [K]. No calculation was run.",
        action: "Enter the reactant temperatures; Tc, gamma and MW are calculated by CEA."}};
    }
    const names = {chamber_temperature_k: "Tc [K]", gamma: "gamma",
      molecular_weight_kg_per_mol: "MW [kg/mol]"};
    const missing = Object.entries(names).filter(([key]) =>
      inputs[key] == null || !Number.isFinite(inputs[key])).map(([, label]) => label);
    return missing.length ? {ok: false, status: "NOT_RUN", error: {code: "MissingExplicitInputs",
      message: `Missing explicit thermochemistry inputs: ${missing.join(", ")}. No calculation was run.`,
      action: "Enter the assumed inputs on 00 Design Project, then Run/Recalculate."}} : null;
  }

  function defaultThermochemistryMode() {
    return state.design?.thermochemistry_configuration?.mode ||
      (state.design?.workflow?.results?.thermochemistry ? "assumed" : "nasa_cea");
  }

  function thermochemistryDraftInputs(drafts) {
    const keys = {"wf-thermo-mode": "mode", "wf-fuel-temp": "fuel_temperature_k", "wf-ox-temp": "oxidizer_temperature_k"};
    if (!Object.keys(keys).some(key => Object.hasOwn(drafts, key))) return null;
    const cfg = {...state.design?.thermochemistry_configuration, mode: drafts["wf-thermo-mode"] || defaultThermochemistryMode()};
    Object.entries(keys).forEach(([id, key]) => {
      if (!Object.hasOwn(drafts, id)) return;
      cfg[key] = key === "mode" ? drafts[id] : drafts[id].trim() === "" ? null : Number(drafts[id]);
      delete drafts[id];
    });
    return cfg;
  }

  function withThermochemistryInputs(inputs) {
    const cfg = state.design?.thermochemistry_configuration || {};
    const read = (id, fallback) => $(id) ? $(id).value : state.drafts?.[id] ?? fallback;
    const value = (id, fallback) => { const text = read(id, fallback); return text == null || String(text).trim() === "" ? null : Number(text); };
    const mode = read("wf-thermo-mode", cfg.mode || defaultThermochemistryMode());
    const result = {...inputs, thermochemistry_configuration: {
      mode, fuel_temperature_k: value("wf-fuel-temp", cfg.fuel_temperature_k),
      oxidizer_temperature_k: value("wf-ox-temp", cfg.oxidizer_temperature_k),
    }};
    if (mode === "nasa_cea") {
      delete result.chamber_temperature_k;
      delete result.gamma;
      delete result.molecular_weight_kg_per_mol;
    }
    return result;
  }

  function thermochemistryFields() {
    return [selectField("Thermochemistry source", [["nasa_cea", "NASA CEA 3.3.4 · equilibrium"], ["assumed", "Explicit assumed chamber state"]], {id: "wf-thermo-mode"}),
      field("Fuel inlet temperature [K] · CEA", {type: "number", step: "any", id: "wf-fuel-temp"}),
      field("Oxidizer inlet temperature [K] · CEA", {type: "number", step: "any", id: "wf-ox-temp"})];
  }

  function updateThermochemistryFields() {
    const cea = $("wf-thermo-mode")?.value === "nasa_cea";
    for (const id of ["wf-tc", "wf-gamma", "wf-mw"]) if ($(id)) $(id).disabled = cea;
    for (const id of ["wf-fuel-temp", "wf-ox-temp"]) if ($(id)) $(id).disabled = !cea;
  }

  async function runWorkflow() {
    if (state.supplementalDirty?.() && !canLeaveDesign()) return;
    const id = requireDesign();
    if (!id) return;
    // Saving refreshes the forms; preserve the user's explicit solver inputs first.
    const phase3Inputs = withThermochemistryInputs({
      chamber_temperature_k: num("wf-tc"),
      gamma: num("wf-gamma"),
      molecular_weight_kg_per_mol: num("wf-mw"),
      throat_area_m2: num("wf-at"),
      expansion_ratio: num("wf-eps"),
    });
    const phase4Payload = phase4Inputs("wf");
    const missing = missingThermochemistryInputs(phase3Inputs);
    if (missing) { setResult(missing); return; }
    const saved = await persistWorkflowInputs();
    if (!saved || saved.ok === false) {
      setResult(saved);
      return;
    }
    setResult({ ok: true, status: "RUNNING", message: "Calculating ready stages and collecting explicit input requests…" });
    const p6 = await api().runDesignWorkflow(id, {phase3_inputs:phase3Inputs,phase4_inputs:phase4Payload});
    await refreshDesign(id);
    state.lastPhase = p6;
    const exportBtn = $("wf-export");
    if (exportBtn) exportBtn.disabled = false;
    setResult(p6);
  }

  function buildWorkflowCard() {
    return makeCard("End-to-end propulsion workflow", (card) => {
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      const fields = [
        ...thermochemistryFields(),
        field("Design name", { type: "text", value: "LOX/RP-1 10 kN engine", id: "wf-name" }),
        field("Pc [bar]", { type: "number", step: "any", id: "wf-pc" }),
        field("Target thrust [kN]", { type: "number", step: "any", id: "wf-thrust" }),
        field("Ambient pressure [Pa] (required)", { type: "number", step: "any", id: "wf-pa" }),
        field("O/F", { type: "number", step: "any", id: "wf-of" }),
        field("ε (Ae/At)", { type: "number", step: "any", id: "wf-eps" }),
        field("Tc assumed [K]", { type: "number", step: "any", id: "wf-tc" }),
        field("γ assumed", { type: "number", step: "any", id: "wf-gamma" }),
        field("MW assumed [kg/mol]", { type: "number", step: "any", id: "wf-mw" }),
        field("At [m²]", { type: "number", step: "any", id: "wf-at" }),
        field("L* [m]", { type: "number", step: "any", id: "wf-lstar" }),
        field("Contraction ratio", { type: "number", step: "any", id: "wf-cr" }),
        field("Wall t [m]", { type: "number", step: "any", id: "wf-twall" }),
        ...engineeringBoundaryFields("wf"),
      ];
      fields.forEach((f) => grid.appendChild(f.wrap));
      const ox = selectField("Oxidizer ID", [["LOX", "LOX"]], { id: "wf-ox" });
      const fuel = selectField("Fuel ID", [["RP1", "RP1"]], { id: "wf-fuel" });
      const material = selectField("Material", [["", "Select material…"]], {
        id: "wf-material",
      });
      grid.appendChild(ox.wrap);
      grid.appendChild(fuel.wrap);
      grid.appendChild(material.wrap);
      card.appendChild(grid);
      populateCatalogSelects();
      const note = document.createElement("p");
      note.className = "suite-note";
      note.textContent =
        "CEA calculates chamber state and ideal nozzle performance at explicit reactant temperatures. Choose a gas-property source for thermal analysis and configure injector/cooling/material inputs. Run calculates ready stages and lists missing inputs; it does not invent them. Selected steady PF/GG balance and solved operating models are available in Engine Cycle. CURRENT means freshness, not physical validation.";
      card.appendChild(note);
      const board = document.createElement("div");
      board.className = "suite-workflow-board";
      board.id = "wf-board";
      board.setAttribute("aria-live", "polite");
      card.appendChild(board);
      const actions = document.createElement("div");
      actions.className = "suite-actions";
      const run = document.createElement("button");
      run.type = "button";
      run.textContent = "Run (same design)";
      bindAction(run, () => runWorkflow());
      const exportBtn = document.createElement("button");
      exportBtn.type = "button";
      exportBtn.id = "wf-export";
      exportBtn.textContent = "Export design package";
      exportBtn.disabled = !state.design;
      exportBtn.addEventListener("click", async () => {
        const id = requireDesign();
        if (!id) return;
        const data = await api().exportDesign(id);
        if (data.ok === false) {
          setResult(data);
          return;
        }
        const blob = new Blob([JSON.stringify(data.package, null, 2)], {
          type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `cosmos_propulsion_${id}.json`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        setResult({
          ok: true,
          model: { model_id: "design.export" },
          outputs: {
            export_format: { value: data.package.export_format, unit: "1" },
            disclaimer: { value: data.package.disclaimer, unit: "1" },
          },
        });
      });
      actions.appendChild(run);
      actions.appendChild(exportBtn);
      card.appendChild(actions);
      renderBoard(state.workflow);
    });
  }

  async function populateCatalogSelects() {
    const props = await api().getPropellantCatalog();
    const ox = $("wf-ox");
    const fuel = $("wf-fuel");
    if (ox && props.oxidizer_ids) {
      ox.innerHTML = '<option value="">Select oxidizer…</option>';
      props.oxidizer_ids.forEach((id) => {
        const opt = document.createElement("option");
        opt.value = id;
        opt.textContent = id;
        ox.appendChild(opt);
      });
      const preferred = state.design?.propellant_configuration?.oxidizer_id || "";
      if ([...ox.options].some((o) => o.value === preferred)) ox.value = preferred;
    }
    if (fuel && props.fuel_ids) {
      fuel.innerHTML = '<option value="">Select fuel…</option>';
      props.fuel_ids.forEach((id) => {
        const opt = document.createElement("option");
        opt.value = id;
        opt.textContent = id;
        fuel.appendChild(opt);
      });
      const preferred = state.design?.propellant_configuration?.fuel_id || "";
      if ([...fuel.options].some((o) => o.value === preferred)) fuel.value = preferred;
    }
    const mats = await api().getMaterialCatalog();
    const material = $("wf-material") || $("ch-material");
    if (material && mats.materials) {
      const current = material.value || state.design?.material_selection?.chamber_material_id || "";
      material.innerHTML = "";
      const blank = document.createElement("option");
      blank.value = "";
      blank.textContent = "Select material…";
      material.appendChild(blank);
      mats.materials.forEach((row) => {
        const opt = document.createElement("option");
        opt.value = row.material_id;
        opt.textContent = `${row.material_id} (${row.condition})`;
        material.appendChild(opt);
      });
      if ([...material.options].some((o) => o.value === current)) material.value = current;
    }
    restoreDrafts();
  }

  function buildEngineDefinitionCard() {
    const req = (state.design && state.design.requirements) || {};
    const name = (state.design && state.design.name) || "";
    return makeCard("Engine definition (requirements)", (card) => {
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      [
        field("Name", { type: "text", id: "ed-name", value: name }),
        field("Pc [bar]", {
          type: "number",
          step: "any",
          id: "ed-pc",
          value: quantityInputValue(req.target_chamber_pressure, "bar"),
        }),
        field("Target thrust [kN]", {
          type: "number",
          step: "any",
          id: "ed-thrust",
          value: quantityInputValue(req.target_thrust, "kN"),
        }),
        field("O/F", {
          type: "number",
          step: "any",
          id: "ed-of",
          value: req.mixture_ratio != null ? String(req.mixture_ratio) : "",
        }),
        field("Expansion ratio", {
          type: "number",
          step: "any",
          id: "ed-eps",
          value: req.expansion_ratio != null ? String(req.expansion_ratio) : "",
        }),
      ].forEach((f) => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const note = document.createElement("p");
      note.className = "suite-note";
      note.textContent =
        "PARTIAL — saves requirements onto the active design. This is not a cycle or CEA solve.";
      card.appendChild(note);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Save requirements";
      bindAction(btn, async () => {
        await saveActive();
      });
      card.appendChild(btn);
    });
  }

  function buildPropellantCard() {
    return makeCard("Propellant registry selection", (card) => {
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      grid.appendChild(selectField("Oxidizer", [["", "Select oxidizer…"]], { id: "pr-ox" }).wrap);
      grid.appendChild(selectField("Fuel", [["", "Select fuel…"]], { id: "pr-fuel" }).wrap);
      grid.appendChild(field("O/F", { type: "number", step: "any", id: "pr-of", value: state.design?.propellant_configuration?.mixture_ratio ?? "" }).wrap);
      card.appendChild(grid);
      const note = document.createElement("p");
      note.className = "suite-note";
      note.textContent =
        "Registry identity and reactant phase are explicit. Configure NASA CEA and inlet temperatures on 00 Design or 05 Thermochemistry; assumed analysis remains a separate mode.";
      card.appendChild(note);
      populatePropellantCard();
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Save propellants";
      bindAction(btn, async () => {
        const id = requireDesign();
        if (!id) return;
        const result = await api().updatePropellants(id, {
          oxidizer_id: $("pr-ox").value,
          fuel_id: $("pr-fuel").value,
          mixture_ratio: num("pr-of"),
        });
        if (result.ok === false) {
          setResult(result);
          return;
        }
        await refreshDesign(id);
        setResult({
          ok: true,
          model: { model_id: "propellants.registry" },
          outputs: {
            oxidizer_id: { value: result.design.propellant_configuration.oxidizer_id, unit: "1" },
            fuel_id: { value: result.design.propellant_configuration.fuel_id, unit: "1" },
          },
        });
      });
      card.appendChild(btn);
    });
  }

  async function populatePropellantCard() {
    const catalog = await api().getPropellantCatalog();
    ["pr-ox", "wf-ox"].forEach((id) => {
      const el = $(id);
      if (!el || !catalog.oxidizer_ids) return;
      el.innerHTML = '<option value="">Select oxidizer…</option>';
      catalog.oxidizer_ids.forEach((pid) => {
        const opt = document.createElement("option");
        opt.value = pid;
        opt.textContent = pid;
        el.appendChild(opt);
      });
      el.value = state.design?.propellant_configuration?.oxidizer_id || "";
    });
    ["pr-fuel", "wf-fuel"].forEach((id) => {
      const el = $(id);
      if (!el || !catalog.fuel_ids) return;
      el.innerHTML = '<option value="">Select fuel…</option>';
      catalog.fuel_ids.forEach((pid) => {
        const opt = document.createElement("option");
        opt.value = pid;
        opt.textContent = pid;
        el.appendChild(opt);
      });
      el.value = state.design?.propellant_configuration?.fuel_id || "";
    });
    restoreDrafts();
  }

  function buildChamberCard() {
    return makeCard("Chamber sizing inputs", (card) => {
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      [
        field("L* [m]", { type: "number", step: "any", id: "ch-lstar" }),
        field("Contraction ratio", { type: "number", step: "any", id: "ch-cr" }),
        field("Wall thickness [m]", { type: "number", step: "any", id: "ch-t" }),
        ...engineeringBoundaryFields("ch"),
      ].forEach((f) => grid.appendChild(f.wrap));
      grid.appendChild(
        selectField("Material", [["", "Select material…"]], { id: "ch-material" }).wrap
      );
      card.appendChild(grid);
      const banner = document.createElement("p");
      banner.className = "suite-assumption-banner";
      banner.textContent =
        "Engineering mode: enter explicit boundary conditions and gas properties. Blank inputs fail closed. Taw is approximated by Tc; handbook materials are not certified allowables.";
      card.appendChild(banner);
      populateCatalogSelects();
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Run Phase 4 on active design";
      bindAction(btn, async () => {
        const id = requireDesign();
        if (!id) return;
        const result = await api().runPhase4(id, phase4Inputs("ch"));
        await refreshDesign(id);
        setResult(result);
      });
      card.appendChild(btn);
    });
  }

  function subsystemFields(stage) {
    return {
      injector: [
        ["oxidizer_density_kg_m3", "Oxidizer liquid density [kg/m³]"], ["fuel_density_kg_m3", "Fuel liquid density [kg/m³]"],
        ["oxidizer_viscosity_pa_s", "Oxidizer viscosity [Pa·s]"], ["fuel_viscosity_pa_s", "Fuel viscosity [Pa·s]"],
        ["oxidizer_pressure_drop_pa", "Oxidizer ΔP [Pa]"], ["fuel_pressure_drop_pa", "Fuel ΔP [Pa]"],
        ["oxidizer_cd", "Oxidizer discharge coefficient"], ["fuel_cd", "Fuel discharge coefficient"],
        ["oxidizer_hole_count", "Oxidizer hole count"], ["fuel_hole_count", "Fuel hole count"],
        ["property_source", "Properties / Cd source and operating state", "text"],
      ],
      nozzle: [
        ["length_fraction", "Length / equivalent 15° cone length"], ["start_angle_deg", "Bell start wall angle [deg]"],
        ["exit_angle_deg", "Exit wall angle [deg]"], ["blend_radius_ratio", "Divergent blend radius / throat radius"],
        ["point_count", "Contour point count (11–1001)"],
      ],
      cooling: [
        ["coolant_mass_flow_kg_s", "Coolant mass flow [kg/s]"], ["inlet_temperature_k", "Coolant inlet temperature [K]"],
        ["inlet_pressure_pa", "Coolant inlet absolute pressure [Pa]"], ["density_kg_m3", "Coolant density [kg/m³]"],
        ["viscosity_pa_s", "Coolant viscosity [Pa·s]"], ["conductivity_w_m_k", "Coolant conductivity [W/(m·K)]"],
        ["cp_j_kg_k", "Coolant Cp [J/(kg·K)]"], ["channel_width_m", "Channel width [m]"],
        ["channel_depth_m", "Channel depth [m]"], ["rib_width_m", "Rib width [m]"], ["channel_count", "Channel count"],
        ["wall_thickness_m", "Hot-wall ligament thickness [m]"], ["wall_conductivity_w_m_k", "Wall conductivity [W/(m·K)]"],
        ["min_temperature_k", "Property validity minimum [K]"], ["max_temperature_k", "Property / single-phase maximum [K]"],
        ["max_wall_temperature_k", "Hot-wall temperature limit [K]"], ["max_vapour_pressure_pa", "Maximum vapour pressure in window [Pa]"],
        ["direction", "Coolant direction", [["", "Select direction…"], ["exit_to_throat", "Exit → throat"], ["throat_to_exit", "Throat → exit"]]],
        ["property_source", "Coolant / wall property source and state", "text"],
        ["film_mode", "Film cooling", [["", "Select film mode…"], ["none", "Disabled explicitly"], ["gaseous_slot", "Gaseous tangential slot estimate"]]],
        ["film_slot_x_m", "Film slot x from throat [m]"], ["film_slot_height_m", "Film slot height [m]"],
        ["film_blowing_ratio", "Film blowing ratio F"], ["film_temperature_k", "Film coolant temperature [K]"],
        ["film_cp_j_kg_k", "Film coolant Cp [J/(kg·K)]"], ["film_delta0_m", "Boundary-layer thickness at slot [m]"],
        ["film_delta_growth_rate", "Declared thickness growth dδ/dx"], ["film_valid_length_m", "Film applicability length downstream [m]"],
        ["film_source", "Film / boundary-layer input source and applicability", "text"],
      ],
    }[stage] || [];
  }

  function subsystemDraftInputs(drafts) {
    const updates = {};
    for (const stage of ["injector", "nozzle", "cooling"]) {
      const fields = subsystemFields(stage);
      if (!fields.some(([key]) => Object.hasOwn(drafts, `sub-${stage}-${key}`))) continue;
      updates[stage] = {...state.design?.subsystem_inputs?.[stage]};
      for (const [key, , type] of fields) {
        const id = `sub-${stage}-${key}`;
        if (!Object.hasOwn(drafts, id)) continue;
        const raw = drafts[id].trim();
        updates[stage][key] = raw === "" ? null : (type ? raw : Number(raw));
        delete drafts[id];
      }
    }
    return updates;
  }

  function buildSubsystemCard(stage) {
    const titles = {injector: "Liquid injector hydraulic sizing", nozzle: "Divergent bell contour", cooling: "Regenerative / gaseous-film cooling"};
    return makeCard(titles[stage], (card) => {
      const note = document.createElement("p");
      note.className = "suite-assumption-banner";
      note.textContent = {injector: "Requires CURRENT Performance. Explicit liquid properties, pressure drops, Cd and counts; no gas injectors, spray layout or combustion stability model.",
        nozzle: "Requires CURRENT Performance. Enter angles and blend radius explicitly. Axisymmetric tangent geometry with quasi-1D stations; not optimized Rao/MOC or manufacturing-ready CAD.",
        cooling: "Run Phase 4 thermal inputs, then generate 11 Nozzle first. Divergent-nozzle coverage only. Re 10,000–100,000; smooth single-phase channels. Film is a gaseous-slot mixing estimate, not liquid-film evaporation. Coolant and film streams are not cycle-balanced."}[stage];
      card.appendChild(note);
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      subsystemFields(stage).forEach(([key, label, type]) => {
        const id = `sub-${stage}-${key}`;
        const entry = Array.isArray(type) ? selectField(label, type, {id}) : field(label, {type: type || "number", step: "any", id});
        if (key.startsWith("film_") && key !== "film_mode") entry.wrap.dataset.filmInput = "true";
        grid.appendChild(entry.wrap);
      });
      card.appendChild(grid);
      if (stage === "cooling") {
        const filmMode = grid.querySelector("#sub-cooling-film_mode");
        const updateFilmFields = () => {
          const enabled = filmMode.value === "gaseous_slot";
          grid.querySelectorAll("[data-film-input]").forEach((wrap) => { wrap.hidden = !enabled; });
        };
        filmMode.addEventListener("change", updateFilmFields);
        // The card is attached after construction; update when its saved values are applied.
        card.updateFilmFields = updateFilmFields;
        updateFilmFields();
      }
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = stage === "nozzle" ? "Generate contour on active design" : `Run ${stage} on active design`;
      bindAction(button, async () => {
        const id = requireDesign();
        if (!id) return;
        const inputs = {};
        subsystemFields(stage).forEach(([key, , type]) => {
          const raw = $(`sub-${stage}-${key}`).value.trim();
          inputs[key] = raw === "" ? null : (type ? raw : Number(raw));
        });
        const edits = saveEdits();
        edits.subsystem_inputs = {...edits.subsystem_inputs, [stage]: inputs};
        const saved = await api().saveDesign(id, edits);
        if (saved.ok === false) { setResult(saved); return; }
        state.drafts = {...edits.editor_drafts};
        state.dirty = false;
        const result = await api().runSubsystems(id, {stages: [stage]});
        await refreshDesign(id);
        setResult(result);
      });
      card.appendChild(button);
    });
  }

  function appendSubsystemVisual(host, result) {
    const current = result.status === "CURRENT" && result.ok !== false;
    const rows = result.outputs?.stations || result.outputs?.segments;
    if (!rows?.length || !current) return; // stale/failed results never offer an active export
    const contour = Boolean(result.outputs.stations);
    const title = document.createElement("p");
    title.className = "suite-note";
    title.textContent = contour ? "Divergent wall contour · metres · geometry only" : "Coolant and peak hot-wall temperatures · K · divergent nozzle only";
    host.appendChild(title);
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 600 240");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", title.textContent);
    svg.classList.add("suite-subsystem-plot");
    const maxX = Math.max(...rows.map(row => row.x_m));
    const keys = contour ? ["radius_m"] : ["coolant_out_temperature_k", "peak_hot_wall_temperature_k"];
    const maxY = Math.max(...keys.flatMap(key => rows.map(row => row[key]))) * 1.1;
    keys.forEach((key, index) => {
      const line = document.createElementNS(svg.namespaceURI, "polyline");
      line.setAttribute("points", rows.map(row => `${45 + row.x_m / maxX * 520},${205 - row[key] / maxY * 180}`).join(" "));
      line.setAttribute("fill", "none");
      line.setAttribute("stroke", index ? "#f8ba76" : "#7fd3f0");
      line.setAttribute("stroke-width", "2");
      svg.appendChild(line);
    });
    const axis = document.createElementNS(svg.namespaceURI, "path");
    axis.setAttribute("d", "M45 20 V205 H570");
    axis.setAttribute("fill", "none");
    axis.setAttribute("stroke", "#8194a5");
    svg.appendChild(axis);
    for (const [x, y, label] of [[45, 225, "x = 0 m"], [350, 225, `x max = ${maxX.toPrecision(4)} m`], [50, 16, `${contour ? "radius" : "T"} axis upper = ${maxY.toPrecision(4)} ${contour ? "m" : "K"}`]]) {
      const text = document.createElementNS(svg.namespaceURI, "text");
      text.setAttribute("x", x); text.setAttribute("y", y); text.setAttribute("fill", "#c4d0dc"); text.setAttribute("font-size", "12");
      text.textContent = label; svg.appendChild(text);
    }
    host.appendChild(svg);
    if (!contour) {
      const legend = document.createElement("p");
      legend.className = "suite-note";
      legend.textContent = "Blue: coolant bulk outlet · Orange: local peak hot wall. Pressure and temperature limits are checked by Physics.";
      host.appendChild(legend);
    }
    const download = document.createElement("button");
    download.type = "button";
    download.textContent = contour ? "Download contour / stations CSV (SI)" : "Download cooling segments CSV (SI)";
    download.addEventListener("click", () => {
      const active = state.design?.workflow?.results?.[result.stage_id];
      if (state.dirty || active?.status !== "CURRENT" || active?.result_id !== result.result_id) {
        setResult({ok: false, error: {code: "ExportNotCurrent", message: "Save and recalculate before exporting this subsystem. The displayed result must match the current saved design."}});
        return;
      }
      const fields = Object.keys(rows[0]);
      const text = [fields.join(","), ...rows.map(row => fields.map(key => row[key]).join(","))].join("\n");
      const url = URL.createObjectURL(new Blob([text], {type: "text/csv"}));
      const a = document.createElement("a");
      a.href = url; a.download = `cosmos_${result.stage_id}_${result.result_id}.csv`;
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    });
    host.appendChild(download);
  }

  function buildCycleCard() {
    return makeCard("Engine cycle", (card) => {
      const sel = selectField(
        "Cycle class",
        [
          ["UNSPECIFIED", "UNSPECIFIED"],
          ["PRESSURE_FED", "PRESSURE_FED"],
          ["GAS_GENERATOR", "GAS_GENERATOR"],
          ["STAGED_COMBUSTION", "STAGED_COMBUSTION"],
          ["EXPANDER", "EXPANDER"],
          ["ELECTRIC_PUMP", "ELECTRIC_PUMP"],
        ],
        { id: "cy-type" }
      );
      card.appendChild(sel.wrap);
      const note = document.createElement("p");
      note.className = "suite-note";
      note.textContent =
        "Implemented bounded steady pressure-fed / gas-generator balance and CEA HP operating-point solvers are available below for managed projects. Selecting a cycle class only records intent. Other cycles remain unsupported; numerical convergence is not physical validation.";
      card.appendChild(note);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Record cycle class";
      bindAction(btn, async () => {
        const id = requireDesign();
        if (!id) return;
        const result = await api().updateCycle(id, $("cy-type").value);
        if (result.ok === false) { setResult(result); return; }
        await refreshDesign(id);
        setResult({
          ok: true,
          model: { model_id: "cycle.record" },
          outputs: {
            cycle_type: { value: result.design.cycle_configuration.cycle_type, unit: "1" },
            implementation_status: {
              value: result.implementation_status,
              unit: "1",
            },
            reason: { value: result.reason, unit: "1" },
          },
        });
      });
      card.appendChild(btn);
      const open = document.createElement("button");open.type="button";open.textContent="Open selected-cycle and solved operating-point editors";
      const area = document.createElement("div");
      bindAction(open, async () => {
        if (state.supplementalDirty?.() && !canLeaveDesign()) return;
        if (state.dirty) throw new Error("Save the baseline design before opening exact-source cycle calculations.");
        const projectId=window.CosmosManagedProjects?.context?.projectId;
        if(!projectId) throw new Error("Open a managed project first; immutable cycle solves require exact baseline authority.");
        const context=await api().get('/api/projects/'+encodeURIComponent(projectId));
        const session=await api().get('/api/auth/session');
        if(context.ok===false||session.ok===false)throw new Error("Authorized managed project required.");
        const readonly=session.user.role==='VIEWER'||context.project.lifecycle!=='ACTIVE';
        open.disabled=true;
        area.replaceChildren();
        let cycleDirty=()=>false, operatingDirty=()=>false;
        state.supplementalDirty=()=>cycleDirty()||operatingDirty();
        cycleDirty=await window.CosmosManagedCycle.render(area,context.project,readonly);
        operatingDirty=await window.CosmosEngineOperating.render(area,context.project,readonly);
        open.hidden=true;
        area.addEventListener('input',publishShellContext);
        area.addEventListener('change',publishShellContext);
        // Editors complete/abandon/discard asynchronously inside this subtree.
        // Reflect their tracker state without observing or rewriting their data.
        const editorObserver=new MutationObserver(()=>publishShellContext());
        editorObserver.observe(area,{childList:true,subtree:true,characterData:true});
        const detachedObserver=new MutationObserver(()=>{
          if(!area.isConnected){editorObserver.disconnect();detachedObserver.disconnect();}
        });
        detachedObserver.observe($('suite-forms'),{childList:true});
      });
      card.append(open,area);
    });
  }

  function standaloneExampleNote(card) {
    const note = document.createElement("p");
    note.className = "suite-assumption-banner";
    note.textContent = "Standalone example calculator: prefilled values are demonstrator assumptions, not active engineering-design inputs. Results do not populate the design workflow.";
    card.appendChild(note);
  }

  function buildIsentropicCard() {
    return makeCard("Isentropic stagnation ratios", (card) => {
      standaloneExampleNote(card);
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      grid.appendChild(field("γ (gamma)", { type: "number", step: "any", value: "1.2", id: "iso-gamma" }).wrap);
      grid.appendChild(field("Mach", { type: "number", step: "any", value: "2.5", id: "iso-mach" }).wrap);
      card.appendChild(grid);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Evaluate (standalone Physics)";
      bindAction(btn, async () => {
        setResult(
          await api().post("/api/physics/compressible/isentropic", {
            mach: Number($("iso-mach").value),
            gamma: Number($("iso-gamma").value),
          })
        );
      });
      card.appendChild(btn);
    });
  }

  function buildAreaMachCard() {
    return makeCard("Area–Mach (A/A*)", (card) => {
      standaloneExampleNote(card);
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      [
        field("γ (gamma)", { type: "number", step: "any", value: "1.2", id: "am-gamma" }),
        selectField(
          "Mode",
          [
            ["inverse", "Mach from A/A*"],
            ["forward", "A/A* from Mach"],
          ],
          { id: "am-mode" }
        ),
        field("A / A*", { type: "number", step: "any", value: "4", id: "am-ar" }),
        field("Mach", { type: "number", step: "any", value: "2.5", id: "am-mach" }),
        selectField(
          "Branch",
          [
            ["supersonic", "Supersonic"],
            ["subsonic", "Subsonic"],
          ],
          { id: "am-branch" }
        ),
      ].forEach((f) => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Evaluate (standalone Physics)";
      bindAction(btn, async () => {
        setResult(
          await api().post("/api/physics/compressible/area-mach", {
            mode: $("am-mode").value,
            gamma: Number($("am-gamma").value),
            mach: Number($("am-mach").value),
            area_ratio: Number($("am-ar").value),
            branch: $("am-branch").value,
          })
        );
      });
      card.appendChild(btn);
    });
  }

  function buildBartzCard() {
    return makeCard("Bartz gas-side HTC", (card) => {
      standaloneExampleNote(card);
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      [
        field("Diameter [m]", { type: "number", step: "any", value: "0.05", id: "bt-d" }),
        field("μ [Pa·s]", { type: "number", step: "any", value: "1e-4", id: "bt-mu" }),
        field("k [W/(m·K)]", { type: "number", step: "any", value: "0.25", id: "bt-k" }),
        field("cp [J/(kg·K)]", { type: "number", step: "any", value: "2000", id: "bt-cp" }),
        field("Pc [Pa]", { type: "number", step: "any", value: "7e6", id: "bt-pc" }),
        field("c* [m/s]", { type: "number", step: "any", value: "1500", id: "bt-cstar" }),
        field("Mach", { type: "number", step: "any", value: "1", id: "bt-mach" }),
        field("γ (gamma)", { type: "number", step: "any", value: "1.2", id: "bt-gamma" }),
        field("Twall [K]", { type: "number", step: "any", value: "800", id: "bt-tw" }),
        field("Taw [K]", { type: "number", step: "any", value: "3000", id: "bt-taw" }),
        field("Curvature R [m] (opt)", { type: "number", step: "any", value: "", id: "bt-rw", placeholder: "optional" }),
      ].forEach((f) => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Evaluate Bartz";
      bindAction(btn, async () => {
        const body = {
          diameter_m: Number($("bt-d").value),
          viscosity_pa_s: Number($("bt-mu").value),
          conductivity_w_m_k: Number($("bt-k").value),
          cp_j_kg_k: Number($("bt-cp").value),
          chamber_pressure_pa: Number($("bt-pc").value),
          cstar_m_s: Number($("bt-cstar").value),
          mach: Number($("bt-mach").value),
          gamma: Number($("bt-gamma").value),
          wall_temperature_k: Number($("bt-tw").value),
          adiabatic_wall_temperature_k: Number($("bt-taw").value),
        };
        const rw = $("bt-rw").value;
        if (rw !== "") body.curvature_radius_m = Number(rw);
        setResult(await api().post("/api/physics/heat-transfer/bartz", body));
      });
      card.appendChild(btn);
    });
  }

  function buildThinWallCard() {
    return makeCard("Thin-wall cylinder stress", (card) => {
      standaloneExampleNote(card);
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      [
        field("Pressure differential Δp [Pa]", { type: "number", step: "any", value: "7e6", id: "tw-p" }),
        field("Radius [m]", { type: "number", step: "any", value: "0.1", id: "tw-r" }),
        field("Thickness [m]", { type: "number", step: "any", value: "0.005", id: "tw-t" }),
        field("Temperature [K]", { type: "number", step: "any", value: "300", id: "tw-temp" }),
      ].forEach((f) => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Evaluate stress";
      bindAction(btn, async () => {
        setResult(
          await api().post("/api/physics/structures/thin-wall", {
            pressure_pa: Number($("tw-p").value),
            radius_m: Number($("tw-r").value),
            thickness_m: Number($("tw-t").value),
            temperature_k: Number($("tw-temp").value),
          })
        );
      });
      card.appendChild(btn);
    });
  }

  function buildPhase3Card() {
    return makeCard("Run Phase 3 on the active design", (card) => {
      const note = document.createElement("p");
      note.className = "suite-note";
      note.textContent =
        "NASA CEA computes equilibrium chamber/throat/exit states and ideal performance. Enter reactant temperatures, throat area and expansion ratio explicitly. No fallback on solver failure. Use 00 Design for assumed-state inputs.";
      card.appendChild(note);
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      [...thermochemistryFields(), field("At [m²]", {type: "number", step: "any", id: "wf-at"}),
        field("ε (Ae/At > 1)", {type: "number", step: "any", id: "wf-eps"})].forEach(f => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Run Phase 3 (same design)";
      bindAction(btn, async () => {
        const id = requireDesign();
        if (!id) return;
        const inputs = withThermochemistryInputs({throat_area_m2: num("wf-at"), expansion_ratio: num("wf-eps")});
        if (inputs.thermochemistry_configuration.mode === "nasa_cea") {
          const missing = missingThermochemistryInputs(inputs);
          if (missing) { setResult(missing); return; }
        }
        // Keep the edited expansion and reactant configuration authoritative
        // across a reload; do not leave epsilon only on a run-time override.
        const edits = saveEdits();
        const saved = await api().saveDesign(id, edits);
        if (saved.ok === false) { setResult(saved); return; }
        state.drafts = {...edits.editor_drafts};
        state.dirty = false;
        const result = await api().runPhase3(id, inputs);
        await refreshDesign(id);
        setResult(result);
      });
      card.appendChild(btn);
    });
  }

  function buildPhase6Card() {
    return makeCard("Summary / consistency / design review", (card) => {
      const note = document.createElement("p");
      note.className = "suite-note";
      note.textContent =
        "Phase 6 aggregates CURRENT results. Missing required inputs or deferred cycle power balance keep the review INCOMPLETE. CURRENT is freshness, not physical validation.";
      card.appendChild(note);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Run Phase 6 (same design)";
      bindAction(btn, async () => {
        const id = requireDesign();
        if (!id) return;
        const result = await api().runPhase6(id);
        await refreshDesign(id);
        setResult(result);
      });
      card.appendChild(btn);
    });
  }

  function liveStageRow(stageId) {
    const nodes = (state.workflow && state.workflow.nodes) || [];
    return nodes.find((node) => node.stage_id === stageId) || null;
  }

  function geometryStatusBanner() {
    const design = state.design;
    if (!design) return null;
    const slots = [
      ["nozzle_design", "Nozzle geometry"],
      ["chamber_design", "Chamber geometry"],
      ["thermal_design", "Thermal slot"],
      ["injector_design", "Injector sizing"],
      ["cooling_design", "Cooling slot"],
      ["structural_design", "Structure slot"],
    ];
    const stale = slots.filter((pair) => {
      const slot = design[pair[0]];
      return slot && slot.geometry_status === "STALE";
    });
    if (!stale.length) return null;
    const banner = document.createElement("p");
    banner.className = "suite-assumption-banner";
    banner.textContent =
      "STALE GEOMETRY — " +
      stale.map((pair) => pair[1]).join(", ") +
      ". Recalculate before treating these slots as current.";
    return banner;
  }

  async function showStoredStageResult(stageId) {
    const id = state.design && state.design.design_id;
    if (!id || stageId === "design_project") return;
    const generation = state.resultGeneration;
    state.presentationLoading = true;
    if (typeof publishPresentation === "function") publishPresentation();
    const payload = await api().getStageResult(id, stageId, true);
    if (generation !== state.resultGeneration || state.design?.design_id !== id ||
        state.activeKind !== "stage" || state.activeId !== stageId) return;
    state.presentationLoading = false;
    // Missing stored slot is the established NOT_CALCULATED case, not an outage.
    // New diagnostics are read-only; do not alter legacy solver/write behavior.
    if (payload?.ok === false && !(payload.error?.code === "KeyError" && payload.error?.message === `Missing field: '${stageId}'`)) {
      state.presentationResult = JSON.parse(JSON.stringify(payload));
      state.presentationDisplayableAsCurrent = false;
    }
    if (typeof publishPresentation === "function") publishPresentation();
    if (payload && payload.result) {
      // Envelope eligibility is presentation metadata, never a source DTO edit.
      setResult(payload.result, {displayableAsCurrent: payload.displayable_as_current === true, targetComparison: payload.target_comparison});
    }
  }

  function renderStage(stage, loadResult = true) {
    state.presentationResult = null;
    state.presentationDisplayableAsCurrent = undefined;
    state.presentationLoading = false;
    state.resultGeneration += 1;
    const live = liveStageRow(stage.stage_id) || {};
    const impl = live.implementation_status || stage.implementation_status;
    const status = live.status || stage.status || "NOT_CALCULATED";
    $("suite-module-title").textContent = `${stage.stage_index || ""} ${stage.name}`.trim();
    $("suite-module-desc").textContent = `${impl} · result ${status}`;
    $("suite-module-ref").textContent = stage.engineering_note || "";
    const forms = $("suite-forms");
    forms.innerHTML = "";
    const result = $("suite-result");
    result.textContent = "No calculation yet.";
    result.classList.remove("error");
    const stale = geometryStatusBanner();
    if (stale) forms.appendChild(stale);
    const cards = STAGE_FORMS[stage.stage_id] || [];
    if (!cards.length || (impl === "NOT_IMPLEMENTED" && stage.stage_id !== "cycle")) {
      const p = document.createElement("p");
      p.className = "suite-note";
      p.textContent =
        (stage.engineering_note || `${impl} — no fake calculator.`) +
        " Validation remains NOT_CLAIMED.";
      forms.appendChild(p);
      if (state.design && loadResult) showStoredStageResult(stage.stage_id);
      return;
    }
    const builders = {
      "workflow-e2e": buildWorkflowCard,
      "engine-definition": buildEngineDefinitionCard,
      propellants: buildPropellantCard,
      "chamber-sizing": buildChamberCard,
      cycle: buildCycleCard,
      isentropic: buildIsentropicCard,
      "area-mach": buildAreaMachCard,
      bartz: buildBartzCard,
      "thin-wall": buildThinWallCard,
      phase3: buildPhase3Card,
      phase6: buildPhase6Card,
      "injector-design": () => buildSubsystemCard("injector"),
      "nozzle-design": () => buildSubsystemCard("nozzle"),
      "cooling-design": () => buildSubsystemCard("cooling"),
    };
    cards.forEach((id) => {
      if (builders[id]) forms.appendChild(builders[id]());
    });
    if (state.design) {
      applyDesignToForms(state.design);
      restoreDrafts();
      if (loadResult) showStoredStageResult(stage.stage_id);
    }
    renderBoard(state.workflow);
  }

  function showActiveWorkspace(loadResult = true) {
    if (state.activeKind === "stage") {
      const stage =
        state.stages.find((item) => item.stage_id === state.activeId) || state.stages[0];
      if (stage) renderStage(stage, loadResult);
      return;
    }
    const mod =
      state.catalog.find((item) => (item.module_id || item.id) === state.activeId) ||
      state.catalog[0];
    if (mod) renderModule(mod);
  }

  function plannedNote(mod) {
    const p = document.createElement("p");
    p.className = "suite-note";
    const status = (mod.status || "planned").toUpperCase();
    p.textContent =
      status === "PLANNED" || status === "NOT_IMPLEMENTED"
        ? `${status} — ${mod.description} No fake calculator. Validation remains NOT_CLAIMED.`
        : mod.description;
    return p;
  }

  function renderModule(mod) {
    state.presentationResult = null;
    state.presentationDisplayableAsCurrent = undefined;
    state.presentationLoading = false;
    state.resultGeneration += 1;
    $("suite-module-title").textContent = mod.title;
    $("suite-module-desc").textContent = mod.description;
    $("suite-module-ref").textContent = mod.reference_note || mod.reference || "";
    const forms = $("suite-forms");
    forms.innerHTML = "";
    const result = $("suite-result");
    result.textContent = "No calculation yet.";
    result.classList.remove("error");
    const cards = MODULE_FORMS[mod.module_id || mod.id] || [];
    if (!cards.length) {
      forms.appendChild(plannedNote(mod));
      return;
    }
    const builders = {
      "workflow-e2e": buildWorkflowCard,
      "engine-definition": buildEngineDefinitionCard,
      propellants: buildPropellantCard,
      "chamber-sizing": buildChamberCard,
      cycle: buildCycleCard,
      isentropic: buildIsentropicCard,
      "area-mach": buildAreaMachCard,
      bartz: buildBartzCard,
      "thin-wall": buildThinWallCard,
      "injector-design": () => buildSubsystemCard("injector"),
      "nozzle-design": () => buildSubsystemCard("nozzle"),
      "cooling-design": () => buildSubsystemCard("cooling"),
    };
    cards.forEach((id) => {
      if (builders[id]) forms.appendChild(builders[id]());
    });
    if (mod.status === "partial") forms.appendChild(plannedNote(mod));
    applyDesignToForms(state.design);
    restoreDrafts();
    forms.querySelectorAll(".suite-card").forEach(card => card.updateFilmFields?.());
  }

  function heading(text) {
    const h = document.createElement("p");
    h.className = "nav-heading";
    h.textContent = text;
    return h;
  }

  function setWorkspaceUrl() {
    const url = new URL(window.location.href);
    if (state.activeKind === "stage") {
      url.searchParams.set("stage", state.activeId);
      url.searchParams.delete("module");
    } else {
      url.searchParams.set("module", state.activeId);
      url.searchParams.delete("stage");
    }
    window.history.replaceState({}, "", url);
  }

  function renderNav() {
    const nav = $("suite-nav");
    if (!nav) return;
    const scrollTop = nav.scrollTop;
    const focusedId = nav.contains(document.activeElement) ? document.activeElement.dataset.workspaceId : null;
    nav.innerHTML = "";
    nav.appendChild(heading("Workflow 00–16"));
    state.stages.forEach((stage) => {
      const live = liveStageRow(stage.stage_id) || {};
      const impl = (live.implementation_status || stage.implementation_status || "").toLowerCase();
      const status = live.status || stage.status || "";
      const btn = document.createElement("button");
      btn.type = "button";
      const active = state.activeKind === "stage" && state.activeId === stage.stage_id;
      btn.dataset.workspaceId = stage.stage_id;
      if (active) btn.setAttribute("aria-current", "step");
      btn.className = active ? "active" : "";
      const implClass = impl.replaceAll("_", "-");
      btn.innerHTML =
        `<span class="nav-index">${stage.stage_index || ""}</span>` +
        `<span class="nav-title">${stage.name}</span>` +
        `<span class="status ${implClass}">${(live.implementation_status || stage.implementation_status || "").replaceAll("_", " ")}</span>` +
        `<span class="nav-group">${status}</span>`;
      btn.addEventListener("click", () => {
        if(state.supplementalDirty?.()&&!canLeaveDesign())return;
        state.supplementalDirty=null;
        state.activeKind = "stage";
        state.activeId = stage.stage_id;
        renderNav();
        renderStage(stage);
        setWorkspaceUrl();
      });
      nav.appendChild(btn);
    });
    nav.appendChild(heading("Physics tools"));
    state.catalog
      .filter((mod) => PHYSICS_TOOL_IDS.includes(mod.module_id || mod.id))
      .forEach((mod) => {
        const id = mod.module_id || mod.id;
        const btn = document.createElement("button");
        btn.dataset.workspaceId = id;
        if (state.activeKind === "module" && state.activeId === id) btn.setAttribute("aria-current", "page");
        btn.type = "button";
        btn.className = state.activeKind === "module" && state.activeId === id ? "active" : "";
        btn.innerHTML =
          `<span class="nav-group">${mod.group}</span>` +
          `<span class="nav-title">${mod.title}</span>` +
          `<span class="status ${mod.status}">${String(mod.status).toUpperCase()}</span>`;
        btn.addEventListener("click", () => {
          if(state.supplementalDirty?.()&&!canLeaveDesign())return;
          state.supplementalDirty=null;
          state.activeKind = "module";
          state.activeId = id;
          renderNav();
          renderModule(mod);
          setWorkspaceUrl();
        });
        nav.appendChild(btn);
      });
    nav.scrollTop = scrollTop;
    if (focusedId) [...nav.querySelectorAll("button")].find((btn) => btn.dataset.workspaceId === focusedId)?.focus({preventScroll: true});
  }

  async function runWorkflowFromDesign(id) {
    const req = state.design?.requirements || {};
    const op = state.design?.operating_point || {};
    const cfg = state.design?.propellant_configuration || {};
    const readNum = (id, fallback) => {
      const el = $(id);
      if (el) return num(id);
      const draft = state.drafts?.[id];
      return draft === undefined ? fallback : (draft.trim() === "" ? null : Number(draft));
    };
    const pcBar =
      readNum("wf-pc", req.target_chamber_pressure
        ? Number(quantityInputValue(req.target_chamber_pressure, "bar"))
        : null);
    const thrustKn =
      readNum("wf-thrust", req.target_thrust ? Number(quantityInputValue(req.target_thrust, "kN")) : null);
    const of = readNum("wf-of", req.mixture_ratio ?? cfg.mixture_ratio ?? null);
    const eps = readNum("wf-eps", req.expansion_ratio ?? null);
    const phase3Inputs = withThermochemistryInputs({
      chamber_temperature_k: readNum("wf-tc", op.chamber_temperature?.magnitude ?? null),
      gamma: readNum("wf-gamma", op.gamma ?? null),
      molecular_weight_kg_per_mol: readNum("wf-mw", op.molecular_weight ?? null),
      throat_area_m2: readNum("wf-at", state.design?.nozzle_design?.throat_area_m2 ?? null),
      expansion_ratio: eps,
    });
    const phase4Payload = phase4Inputs("wf");
    const missing = missingThermochemistryInputs(phase3Inputs);
    if (missing) return missing;
    const saved = await persistDesignInputs(id, {
      target_chamber_pressure: pcBar == null ? null : { magnitude: pcBar, unit_symbol: "bar" },
      target_thrust: thrustKn == null ? null : { magnitude: thrustKn, unit_symbol: "kN" },
      mixture_ratio: of,
      expansion_ratio: eps,
      ambient_pressure: readNum("wf-pa", req.ambient_pressure?.magnitude ?? null) == null ? null :
        {magnitude: readNum("wf-pa", req.ambient_pressure?.magnitude ?? null), unit_symbol: "Pa"},
      notes: "Recalculate from Rocket Engine workbench.",
    }, {
      oxidizer_id: $("wf-ox") ? $("wf-ox").value : state.drafts?.["wf-ox"] ?? cfg.oxidizer_id ?? "",
      fuel_id: $("wf-fuel") ? $("wf-fuel").value : state.drafts?.["wf-fuel"] ?? cfg.fuel_id ?? "",
      mixture_ratio: of,
    });
    if (saved.ok === false) return saved;
    setResult({ ok: true, status: "RUNNING", message: "Calculating ready stages and collecting explicit input requests…" });
    const p6 = await api().runDesignWorkflow(id, {phase3_inputs:phase3Inputs,phase4_inputs:phase4Payload});
    await refreshDesign(id);
    state.lastPhase = p6;
    return p6;
  }

  async function recalculateActive() {
    if (state.supplementalDirty?.() && !canLeaveDesign()) return;
    const id = requireDesign();
    if (!id) return;
    const result = await runWorkflowFromDesign(id);
    setResult(result);
  }

  function bindContextActions() {
    $("suite-forms")?.addEventListener("input", trackDraft);
    $("suite-forms")?.addEventListener("change", trackDraft);
    window.addEventListener("beforeunload", (event) => {
      if (!state.dirty && !state.supplementalDirty?.()) return;
      event.preventDefault();
      event.returnValue = "";
    });
    bindAction($("design-new"), () => createNewDesign());
    bindAction($("design-save"), () => saveActive());
    bindAction($("design-clone"), () => cloneActive());
    bindAction($("design-recalculate"), () => recalculateActive());
    bindAction($("design-reload"), async () => {
      const id = requireDesign();
      if (!id) return;
      await refreshDesign(id, {loadResult: true});
    });
    bindAction($("design-review"), async () => {
      const id = requireDesign();
      if (!id) return;
      const result = await api().runPhase6(id);
      await refreshDesign(id);
      setResult(result);
    });
    $("design-picker")?.addEventListener("change", async (event) => {
      const id = event.target.value;
      if (!id) return;
      if (!canLeaveDesign()) {
        event.target.value = state.design?.design_id || "";
        return;
      }
      await runWorkspaceAction(() => refreshDesign(id, {loadResult: true}));
    });
  }

  async function initPropulsionSuite() {
    try {
      if (window.COSMOS && typeof window.COSMOS.initShell === "function") {
        await window.COSMOS.initShell({ activeNav: "propulsion" });
      }
    } catch (err) {
      console.warn("Shell enhancement failed; Rocket Engine continues.", err);
    }
    try {
      const [catalog, stages] = await Promise.all([
        api().getSuiteCatalog(),
        api().getWorkflowCatalog(),
      ]);
      if (catalog.ok === false || !catalog.modules) {
        $("suite-nav").textContent = catalog.error?.message || "Suite catalog unavailable.";
        return;
      }
      if (stages.ok === false || !stages.nodes) {
        $("suite-nav").textContent = stages.error?.message || "Workflow catalog unavailable.";
        return;
      }
      state.catalog = catalog.modules;
      state.stages = stages.nodes;
      bindContextActions();
      await fillDesignPicker();
      const params = new URLSearchParams(window.location.search);
      const remembered = params.get('design') || rememberedDesignId();
      if (remembered) {
        await refreshDesign(remembered);
      }
      const MODULE_TO_STAGE = {
        "workflow-analysis": "design_project",
        "engine-definition": "requirements",
        "propellants-combustion": "propellants",
        "chamber-sizing": "chamber",
        "nozzle-flow": "nozzle",
        "nozzle-contour": "nozzle",
        injectors: "injector",
        structures: "structure",
        "cycle-feed": "cycle",
        "heat-transfer": "thermal",
      };
      const wantedStage = params.get("stage");
      const wantedModule = params.get("module");
      if (wantedStage && state.stages.some((item) => item.stage_id === wantedStage)) {
        state.activeKind = "stage";
        state.activeId = wantedStage;
      } else if (wantedModule && PHYSICS_TOOL_IDS.includes(wantedModule)) {
        state.activeKind = "module";
        state.activeId = wantedModule;
      } else if (wantedModule && MODULE_TO_STAGE[wantedModule]) {
        state.activeKind = "stage";
        state.activeId = MODULE_TO_STAGE[wantedModule];
      } else if (wantedModule && state.catalog.some((item) => (item.module_id || item.id) === wantedModule)) {
        state.activeKind = "module";
        state.activeId = wantedModule;
      } else {
        state.activeKind = "stage";
        state.activeId = "design_project";
      }
      renderNav();
      showActiveWorkspace();
      renderContextBar();
      if (params.get("from") === "physics") {
        const forms = $("suite-forms");
        if (forms && !forms.querySelector(".suite-redirect-note")) {
          const note = document.createElement("p");
          note.className = "suite-note suite-redirect-note";
          note.textContent =
            "The standalone compressible-flow page now lives here as stage 11 Nozzle / Physics tools. No second solver was added.";
          forms.prepend(note);
        }
      }
      if (window.COSMOS && typeof window.COSMOS.setStatusBar === "function") {
        window.COSMOS.setStatusBar(
          state.design ? `Design: ${state.design.name}` : "Create or open a design to begin",
          state.design ? "ready" : "idle",
          "Rocket Engine",
        );
      }
    } catch (err) {
      console.error("Propulsion suite initialization failed.", err);
      const nav = $("suite-nav");
      if (nav) nav.textContent = "Propulsion suite failed to initialize. Check login and reload.";
      setResult({
        ok: false,
        error: {
          code: "InitFailed",
          message: String(err && err.message ? err.message : err),
          action: "Reload the page or sign in again.",
        },
      });
    }
  }

  if (typeof window.COSMOS !== "object" || window.COSMOS === null) {
    window.COSMOS = {};
  }
  window.COSMOS.initPropulsionSuite = initPropulsionSuite;
  function shellContext() {
    const saved = window.CosmosManagedProjects?.context?.editorHeads.get(state.design?.design_id);
    return Object.freeze({designId: state.design?.design_id || null, name: state.design?.name || null,
      revision: state.design?.revision ?? null, dirty: state.dirty || Boolean(state.supplementalDirty?.()), busy: state.busy,
      ...(saved ? {projectId: saved.project_id, savedVersion: saved.head.version,
        savedCommitId: saved.commit_id, savedContentHash: saved.head.content_hash} : {})});
  }
  function immutableCopy(value) {
    const copy = value == null ? null : JSON.parse(JSON.stringify(value));
    const freeze = item => {
      if (item && typeof item === "object") { Object.values(item).forEach(freeze); Object.freeze(item); }
      return item;
    };
    return freeze(copy);
  }
  function publishPresentation() {
    window.dispatchEvent(new CustomEvent("cosmos:rocket-context"));
  }
  function applyDraftHistory(entry) {
    state.drafts = {...entry.drafts}; state.dirty = entry.dirty;
    if (state.design) applyDesignToForms(state.design);
    restoreDrafts();
    const restored = [...($('suite-forms')?.querySelectorAll('input[id], select[id]') || [])].find(input => draftKey(input.id) === draftKey(entry.field));
    if (restored && entry.value !== undefined) {restored.value = entry.value; fieldBeforeEdit.set(restored.id, restored.value); restored.focus();}
    renderContextBar();
  }
  function moveDraftHistory(from, to) {
    const entry = from.at(-1);
    if (state.busy || !entry || entry.designId !== state.design?.design_id || entry.revision !== state.design?.revision) return false;
    to.push({designId:entry.designId,revision:entry.revision,drafts:{...state.drafts},dirty:state.dirty,field:entry.field,value:fieldBeforeEdit.get(entry.field)});
    if (to.length > 100) to.shift();
    from.pop(); applyDraftHistory(entry); return true;
  }
  window.COSMOS.rocketPresentation = Object.freeze({
    restoreNavigation() { renderNav(); applyBusyState(); },
    retryResult() { if (!state.busy && state.activeKind === "stage") return showStoredStageResult(state.activeId); },
    readContext() {
      const undo = state.draftUndo.at(-1), redo = state.draftRedo.at(-1);
      return immutableCopy({...shellContext(), activeKind: state.activeKind, activeId: state.activeId,
        resultGeneration: state.resultGeneration,
        resultDisplayableAsCurrent: state.presentationDisplayableAsCurrent,
        loading: state.presentationLoading,
        canUndo: !state.busy && Boolean(undo && undo.designId === state.design?.design_id && undo.revision === state.design?.revision),
        canRedo: !state.busy && Boolean(redo && redo.designId === state.design?.design_id && redo.revision === state.design?.revision),
        stages: state.stages.map(stage => ({...stage, ...(liveStageRow(stage.stage_id) || {})}))});
    },
    readResult() { return immutableCopy(state.presentationResult); },
    readTargetComparison() {return immutableCopy(state.presentationComparison);},
    undoDraft() {
      return moveDraftHistory(state.draftUndo, state.draftRedo);
    },
    redoDraft() {return moveDraftHistory(state.draftRedo, state.draftUndo);},
  });
  // Read-only context; design switching delegates to the existing dirty/busy guards.
  window.COSMOS.propulsionShellContext = shellContext;
  window.COSMOS.selectPropulsionDesign = async id => {
    if (state.busy || !canLeaveDesign()) return false;
    let selected = false;
    await runWorkspaceAction(async () => { selected = Boolean(await refreshDesign(id, {discardDrafts:true})); });
    return selected;
  };
})();
