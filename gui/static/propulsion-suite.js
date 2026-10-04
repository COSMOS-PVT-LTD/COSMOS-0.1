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
    injector: [],
    chamber: ["chamber-sizing"],
    thermal: ["chamber-sizing", "bartz"],
    cooling: [],
    nozzle: ["isentropic", "area-mach"],
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
    "nozzle-contour": [],
    "heat-transfer": ["bartz"],
    injectors: [],
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
  };

  function $(id) {
    return document.getElementById(id);
  }

  function api() {
    return window.CosmosAPI;
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
    if (Number.isNaN(mag)) return "—";
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
    const thermal = design.thermal_design || {};
    const structural = design.structural_design || {};
    const chamber = design.chamber_design || {};
    const nozzle = design.nozzle_design || {};
    Object.entries({
      "wf-lstar": chamber.characteristic_length_m, "wf-cr": chamber.contraction_ratio,
      "wf-at": nozzle.throat_area_m2, "wf-twall": structural.wall_thickness_m,
      "wf-pout": quantityInputValue(structural.external_pressure, "Pa"),
      "wf-tmaterial": structural.material_temperature_k,
      "wf-mu": thermal.viscosity_pa_s, "wf-k": thermal.conductivity_w_m_k,
      "wf-cp": thermal.cp_j_kg_k, "wf-tw": thermal.wall_temperature_k,
      "wf-curvature": thermal.throat_curvature_radius_m ?? nozzle.throat_curvature_radius_m,
      "wf-material": design.material_selection?.chamber_material_id,
    }).forEach(([id, value]) => setFieldValue(id, value));
    if (cfg.oxidizer_id && $("wf-ox")) $("wf-ox").value = cfg.oxidizer_id;
    if (cfg.fuel_id && $("wf-fuel")) $("wf-fuel").value = cfg.fuel_id;
    if (cfg.oxidizer_id && $("pr-ox")) $("pr-ox").value = cfg.oxidizer_id;
    if (cfg.fuel_id && $("pr-fuel")) $("pr-fuel").value = cfg.fuel_id;
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
    if (!payload || payload.ok === false) {
      const err = payload?.error || payload?.errors?.[0] || {};
      return [
        "CALCULATION FAILED",
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
    const model = payload.model || {};
    const lines = [
      "MODEL",
      `Model ID: ${model.model_id || ""}`,
      `Name: ${model.model_name || ""}`,
      `Source: ${model.source || ""}`,
      `Verification: ${payload.verification?.result || payload.verification?.status || ""}`,
      `Validation: ${payload.validation?.status || "NOT_CLAIMED"}`,
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

  function renderStructuredPhase(payload) {
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
      const pre = document.createElement("pre");
      pre.textContent = formatResult({ ok: !["FAILED", "OUT_OF_RANGE"].includes(stage.status), ...stage });
      card.appendChild(pre);
      host.appendChild(card);
    });
    return host;
  }

  function setResult(payload) {
    const el = $("suite-result");
    if (!el) return;
    el.classList.toggle("error", Boolean(payload && payload.ok === false));
    el.innerHTML = "";
    if (payload && payload.stages) {
      el.appendChild(renderStructuredPhase(payload));
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

  function renderContextBar() {
    const nameEl = $("design-context-name");
    if (!nameEl) return;
    const design = state.design;
    if (!design) {
      nameEl.textContent = "No active design";
      $("design-context-revision").textContent = "REV —";
      $("design-context-state").textContent = "NONE";
      $("design-context-pc").textContent = "Pc —";
      $("design-context-of").textContent = "O/F —";
      $("design-context-thrust").textContent = "Thrust —";
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
    $("design-context-thrust").textContent = `Thrust ${displayEngineQty(req.target_thrust, "kN")}`;
    const ox = cfg.oxidizer_id || "—";
    const fuel = cfg.fuel_id || "—";
    $("design-context-props").textContent = `Propellants ${ox} / ${fuel}`;
  }

  async function refreshDesign(id) {
    const payload = await api().getDesign(id);
    if (!payload.ok && payload.error) {
      setResult(payload);
      return null;
    }
    state.design = payload.design;
    rememberDesignId(payload.design.design_id);
    const wf = await api().getWorkflow(payload.design.design_id);
    state.workflow = wf.workflow || null;
    renderContextBar();
    renderBoard(state.workflow);
    fillDesignPicker();
    showActiveWorkspace();
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
    thead.innerHTML = "<tr><th>Stage</th><th>Impl</th><th>Status</th><th>Current?</th></tr>";
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
    return {
      characteristic_length_m: num(`${prefix}-lstar`),
      contraction_ratio: num(`${prefix}-cr`),
      wall_thickness_m: num(prefix === "wf" ? "wf-twall" : "ch-t"),
      material_id: $(`${prefix}-material`)?.value || null,
      external_pressure_pa: num(`${prefix}-pout`),
      external_pressure_source: "Explicit outer-wall pressure entered in the engineering form.",
      material_temperature_k: num(`${prefix}-tmaterial`),
      viscosity_pa_s: num(`${prefix}-mu`),
      conductivity_w_m_k: num(`${prefix}-k`),
      cp_j_kg_k: num(`${prefix}-cp`),
      wall_temperature_k: num(`${prefix}-tw`),
      throat_curvature_radius_m: num(`${prefix}-curvature`),
    };
  }

  function engineeringBoundaryFields(prefix) {
    return [
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
    const name = ($("wf-name") && $("wf-name").value) || "Rocket Engine Analysis";
    const created = await api().createDesign({
      name,
      description: "Rocket Engine workbench design",
    });
    if (created.ok === false) {
      setResult(created);
      return;
    }
    state.design = created.design;
    rememberDesignId(created.design.design_id);
    await refreshDesign(created.design.design_id);
    renderNav();
    setResult({
      ok: true,
      model: { model_id: "design.create" },
      outputs: { design_id: { value: created.design.design_id, unit: "1" }, name: { value: created.design.name, unit: "1" } },
    });
  }

  async function saveActive() {
    const id = requireDesign();
    if (!id) return;
    const saved = await api().saveDesign(id);
    if (saved.ok === false) {
      setResult(saved);
      return;
    }
    state.design = saved.design;
    await refreshDesign(saved.design.design_id);
    setResult({
      ok: true,
      model: { model_id: "design.save" },
      outputs: { revision: { value: saved.design.revision, unit: "1" } },
    });
  }

  async function cloneActive() {
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
    const req = await api().updateRequirements(id, {
      target_chamber_pressure: num("wf-pc") == null ? null : { magnitude: num("wf-pc"), unit_symbol: "bar" },
      target_thrust: num("wf-thrust") == null ? null : { magnitude: num("wf-thrust"), unit_symbol: "kN" },
      mixture_ratio: num("wf-of"),
      expansion_ratio: num("wf-eps"),
      ambient_pressure: num("wf-pa") == null ? null : { magnitude: num("wf-pa"), unit_symbol: "Pa" },
      notes: "GUI workflow inputs. Thermochemistry assumptions are explicit.",
    });
    if (req.ok === false) return req;
    const ox = $("wf-ox")?.value || "";
    const fuel = $("wf-fuel")?.value || "";
    const props = await api().updatePropellants(id, {
      oxidizer_id: ox,
      fuel_id: fuel,
      mixture_ratio: num("wf-of"),
    });
    if (props.ok === false) return props;
    await refreshDesign(id);
    return { ok: true };
  }

  async function runWorkflow() {
    const id = requireDesign();
    if (!id) return;
    // Saving refreshes the forms; preserve the user's explicit solver inputs first.
    const phase3Inputs = {
      chamber_temperature_k: num("wf-tc"),
      gamma: num("wf-gamma"),
      molecular_weight_kg_per_mol: num("wf-mw"),
      throat_area_m2: num("wf-at"),
      expansion_ratio: num("wf-eps"),
    };
    const phase4Payload = phase4Inputs("wf");
    const saved = await persistWorkflowInputs();
    if (!saved || saved.ok === false) {
      setResult(saved);
      return;
    }
    setResult({ ok: true, status: "RUNNING", message: "Running Phase 3 on the active design…" });
    const p3 = await api().runPhase3(id, phase3Inputs);
    if (p3.ok === false) {
      setResult(p3);
      await refreshDesign(id);
      return;
    }
    const p4 = await api().runPhase4(id, phase4Payload);
    if (p4.ok === false) {
      setResult(p4);
      await refreshDesign(id);
      return;
    }
    const p6 = await api().runPhase6(id);
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
        field("Design name", { type: "text", value: "LOX/RP-1 10 kN engine", id: "wf-name" }),
        field("Pc [bar]", { type: "number", step: "any", id: "wf-pc" }),
        field("Thrust [kN]", { type: "number", step: "any", id: "wf-thrust" }),
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
        "Engineering mode requires explicit inputs; blank values are not defaulted. Outside wall pressure is separate from nozzle ambient pressure. Taw is approximated by Tc. Injector and regenerative cooling remain NOT_IMPLEMENTED. CURRENT means input freshness; validation is NOT_CLAIMED.";
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
      run.addEventListener("click", () => runWorkflow());
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
        field("Thrust [kN]", {
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
      btn.addEventListener("click", async () => {
        const id = requireDesign();
        if (!id) return;
        const result = await api().updateRequirements(id, {
          target_chamber_pressure: num("ed-pc") == null ? null : { magnitude: num("ed-pc"), unit_symbol: "bar" },
          target_thrust: num("ed-thrust") == null ? null : { magnitude: num("ed-thrust"), unit_symbol: "kN" },
          mixture_ratio: num("ed-of"),
          expansion_ratio: num("ed-eps"),
        });
        if (result.ok === false) {
          setResult(result);
          return;
        }
        await refreshDesign(id);
        setResult({
          ok: true,
          model: { model_id: "requirements.save" },
          outputs: { revision: { value: result.design.revision, unit: "1" } },
          warnings: ["Changing Pc invalidates downstream CURRENT results (STALE)."],
        });
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
        "PARTIAL — Physics registry identity only. CEA: UNAVAILABLE / NOT_BOUND. Thermochemistry remains ASSUMED until a versioned CEA binding exists.";
      card.appendChild(note);
      populatePropellantCard();
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Save propellants";
      btn.addEventListener("click", async () => {
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
      btn.addEventListener("click", async () => {
        const id = requireDesign();
        if (!id) return;
        const result = await api().runPhase4(id, phase4Inputs("ch"));
        await refreshDesign(id);
        setResult(result);
      });
      card.appendChild(btn);
    });
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
        "NOT_IMPLEMENTED — no validated cycle power-balance model exists in COSMOS 0.1 Physics. Selecting a class records intent only.";
      card.appendChild(note);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Record cycle class";
      btn.addEventListener("click", async () => {
        const id = requireDesign();
        if (!id) return;
        const result = await api().updateCycle(id, $("cy-type").value);
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
      btn.addEventListener("click", async () => {
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
      btn.addEventListener("click", async () => {
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
      btn.addEventListener("click", async () => {
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
      btn.addEventListener("click", async () => {
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
        "Uses the saved design. CEA remains UNAVAILABLE; supply assumed Tc/γ/MW on 00 Design if you need a solve.";
      card.appendChild(note);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Run Phase 3 (same design)";
      btn.addEventListener("click", async () => {
        const id = requireDesign();
        if (!id) return;
        const result = await api().runPhase3(id, {});
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
        "Phase 6 aggregates CURRENT results. review_ready stays false while injector, cooling, or cycle are NOT_IMPLEMENTED.";
      card.appendChild(note);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Run Phase 6 (same design)";
      btn.addEventListener("click", async () => {
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
    if (!id) return;
    const payload = await api().getStageResult(id, stageId, true);
    if (payload && payload.result) {
      const wrapped = {
        ok: payload.displayable_as_current !== false && payload.ok !== false,
        ...payload.result,
        warnings: [
          ...((payload.result && payload.result.warnings) || []),
          payload.displayable_as_current
            ? ""
            : "This stored result is not the active CURRENT answer.",
        ].filter(Boolean),
      };
      setResult(wrapped);
    }
  }

  function renderStage(stage) {
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
    if (!cards.length || impl === "NOT_IMPLEMENTED") {
      const p = document.createElement("p");
      p.className = "suite-note";
      p.textContent =
        (stage.engineering_note || `${impl} — no fake calculator.`) +
        " Validation remains NOT_CLAIMED.";
      forms.appendChild(p);
      if (state.design) showStoredStageResult(stage.stage_id);
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
    };
    cards.forEach((id) => {
      if (builders[id]) forms.appendChild(builders[id]());
    });
    if (state.design) {
      applyDesignToForms(state.design);
      showStoredStageResult(stage.stage_id);
    }
  }

  function showActiveWorkspace() {
    if (state.activeKind === "stage") {
      const stage =
        state.stages.find((item) => item.stage_id === state.activeId) || state.stages[0];
      if (stage) renderStage(stage);
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
    };
    cards.forEach((id) => {
      if (builders[id]) forms.appendChild(builders[id]());
    });
    if (mod.status === "partial") forms.appendChild(plannedNote(mod));
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
    nav.innerHTML = "";
    nav.appendChild(heading("Workflow 00–16"));
    state.stages.forEach((stage) => {
      const live = liveStageRow(stage.stage_id) || {};
      const impl = (live.implementation_status || stage.implementation_status || "").toLowerCase();
      const status = live.status || stage.status || "";
      const btn = document.createElement("button");
      btn.type = "button";
      const active = state.activeKind === "stage" && state.activeId === stage.stage_id;
      btn.className = active ? "active" : "";
      const implClass = impl.replaceAll("_", "-");
      btn.innerHTML =
        `<span class="nav-index">${stage.stage_index || ""}</span>` +
        `<span class="nav-title">${stage.name}</span>` +
        `<span class="status ${implClass}">${(live.implementation_status || stage.implementation_status || "").replaceAll("_", " ")}</span>` +
        `<span class="nav-group">${status}</span>`;
      btn.addEventListener("click", () => {
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
        btn.type = "button";
        btn.className = state.activeKind === "module" && state.activeId === id ? "active" : "";
        btn.innerHTML =
          `<span class="nav-group">${mod.group}</span>` +
          `<span class="nav-title">${mod.title}</span>` +
          `<span class="status ${mod.status}">${String(mod.status).toUpperCase()}</span>`;
        btn.addEventListener("click", () => {
          state.activeKind = "module";
          state.activeId = id;
          renderNav();
          renderModule(mod);
          setWorkspaceUrl();
        });
        nav.appendChild(btn);
      });
  }

  async function runWorkflowFromDesign(id) {
    const req = state.design?.requirements || {};
    const op = state.design?.operating_point || {};
    const cfg = state.design?.propellant_configuration || {};
    const readNum = (id, fallback) => {
      const el = $(id);
      return el ? num(id) : fallback;
    };
    const pcBar =
      readNum("wf-pc", req.target_chamber_pressure
        ? Number(quantityInputValue(req.target_chamber_pressure, "bar"))
        : null);
    const thrustKn =
      readNum("wf-thrust", req.target_thrust ? Number(quantityInputValue(req.target_thrust, "kN")) : null);
    const of = readNum("wf-of", req.mixture_ratio ?? cfg.mixture_ratio ?? null);
    const eps = readNum("wf-eps", req.expansion_ratio ?? null);
    const phase3Inputs = {
      chamber_temperature_k: readNum("wf-tc", op.chamber_temperature?.magnitude ?? null),
      gamma: readNum("wf-gamma", op.gamma ?? null),
      molecular_weight_kg_per_mol: readNum("wf-mw", op.molecular_weight ?? null),
      throat_area_m2: readNum("wf-at", state.design?.nozzle_design?.throat_area_m2 ?? null),
      expansion_ratio: eps,
    };
    const phase4Payload = phase4Inputs("wf");
    const saved = await api().updateRequirements(id, {
      target_chamber_pressure: pcBar == null ? null : { magnitude: pcBar, unit_symbol: "bar" },
      target_thrust: thrustKn == null ? null : { magnitude: thrustKn, unit_symbol: "kN" },
      mixture_ratio: of,
      expansion_ratio: eps,
      ambient_pressure: $("wf-pa") ? (num("wf-pa") == null ? null : { magnitude: num("wf-pa"), unit_symbol: "Pa" }) : req.ambient_pressure ?? null,
      notes: "Recalculate from Rocket Engine workbench.",
    });
    if (saved.ok === false) return saved;
    const props = await api().updatePropellants(id, {
      oxidizer_id: $("wf-ox") ? $("wf-ox").value : cfg.oxidizer_id || "",
      fuel_id: $("wf-fuel") ? $("wf-fuel").value : cfg.fuel_id || "",
      mixture_ratio: of,
    });
    if (props.ok === false) return props;
    await refreshDesign(id);
    setResult({ ok: true, status: "RUNNING", message: "Running Phase 3→6 on the active design…" });
    const p3 = await api().runPhase3(id, phase3Inputs);
    if (p3.ok === false) {
      await refreshDesign(id);
      return p3;
    }
    const p4 = await api().runPhase4(id, phase4Payload);
    if (p4.ok === false) {
      await refreshDesign(id);
      return p4;
    }
    const p6 = await api().runPhase6(id);
    await refreshDesign(id);
    state.lastPhase = p6;
    return p6;
  }

  async function recalculateActive() {
    const id = requireDesign();
    if (!id) return;
    const result = await runWorkflowFromDesign(id);
    setResult(result);
  }

  function bindContextActions() {
    $("design-new")?.addEventListener("click", () => createNewDesign());
    $("design-save")?.addEventListener("click", () => saveActive());
    $("design-clone")?.addEventListener("click", () => cloneActive());
    $("design-recalculate")?.addEventListener("click", () => recalculateActive());
    $("design-reload")?.addEventListener("click", async () => {
      const id = requireDesign();
      if (!id) return;
      await refreshDesign(id);
    });
    $("design-review")?.addEventListener("click", async () => {
      const id = requireDesign();
      if (!id) return;
      const result = await api().runPhase6(id);
      await refreshDesign(id);
      setResult(result);
    });
    $("design-picker")?.addEventListener("change", async (event) => {
      const id = event.target.value;
      if (!id) return;
      await refreshDesign(id);
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
      const remembered = rememberedDesignId();
      if (remembered) {
        await refreshDesign(remembered);
      }
      const params = new URLSearchParams(window.location.search);
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
})();
