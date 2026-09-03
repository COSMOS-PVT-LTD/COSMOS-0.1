/**
 * Rocket Engine propulsion design suite — GUI only.
 * Live modules call /api/physics/* adapters; no Physics imports or equations here.
 */
(function () {
  "use strict";

  const MODULES = [
    {
      id: "workflow-analysis",
      title: "Workflow Analysis (E2E)",
      group: "Workflow",
      status: "live",
      description:
        "Full Systems workflow: Phase 3–4 analysis plus Phase 6 summary, consistency, design review, and JSON export. GUI calls API only — no equations in the browser.",
      reference: "COSMOS Systems Phase 3–6 · RPA/RPL layout inspiration only",
      cards: ["workflow-e2e"],
    },
    {
      id: "engine-definition",
      title: "Engine Definition",
      group: "Setup",
      status: "planned",
      description:
        "Thrust, chamber pressure, propellant pair, mixture ratio, and cycle class — mirrors RPA project setup / RPL engine definition.",
      reference: "RPA: Project setup · RPL: Engine definition",
    },
    {
      id: "propellants-combustion",
      title: "Propellants & Combustion",
      group: "Thermochemistry",
      status: "planned",
      description:
        "CEA-style propellant / combustion equilibrium (γ, Tc, molecular weight, c*). Physics thermochemistry is frozen but not yet exposed through a GUI adapter.",
      reference: "RPA: Propellant analysis · RPL: Combustion",
    },
    {
      id: "chamber-sizing",
      title: "Chamber Sizing",
      group: "Geometry",
      status: "planned",
      description:
        "Throat area from thrust / chamber pressure, L* and characteristic length, convergent section estimates.",
      reference: "RPA: Chamber design · RPL: Chamber",
    },
    {
      id: "nozzle-flow",
      title: "Nozzle Flow",
      group: "Flow",
      status: "live",
      description:
        "Isentropic stagnation relations and area–Mach (sonic throat). Live via frozen compressible-flow Physics.",
      reference: "RPA: Nozzle performance · RPL: Nozzle flow",
      cards: ["isentropic", "area-mach"],
    },
    {
      id: "nozzle-contour",
      title: "Nozzle Contour",
      group: "Geometry",
      status: "planned",
      description:
        "Conical / Rao / TIC contour generation and wall coordinates — geometry only; not yet in suite.",
      reference: "RPA: Nozzle contour (MOC) · RPL: Contour design",
    },
    {
      id: "heat-transfer",
      title: "Heat Transfer",
      group: "Thermal",
      status: "live",
      description:
        "Bartz gas-side heat-transfer coefficient at a station. Live via frozen heat-transfer Physics.",
      reference: "RPA: Cooling / heat transfer · RPL: Thermal",
      cards: ["bartz"],
    },
    {
      id: "injectors",
      title: "Injectors",
      group: "Feed",
      status: "planned",
      description:
        "Orifice sizing, pressure drop, and pattern layout for unlike-impinging and swirl injectors.",
      reference: "RPA: Injector · RPL: Injector design",
    },
    {
      id: "structures",
      title: "Structures (Thin Wall)",
      group: "Mechanics",
      status: "partial",
      description:
        "Thin-wall hoop / longitudinal stress helpers for preliminary cylinder checks. Full chamber structure analysis remains planned.",
      reference: "RPL: Structural checks · COSMOS solid mechanics (partial)",
      cards: ["thin-wall"],
    },
    {
      id: "cycle-feed",
      title: "Cycle & Performance",
      group: "System",
      status: "planned",
      description:
        "Power balance, turbopump demands, and delivered Isp for GG / expander / staged-combustion class cycles.",
      reference: "RPA: Engine cycle · RPL: Cycle analysis",
    },
  ];

  function $(id) {
    return document.getElementById(id);
  }

  function formatResult(payload) {
    if (!payload || payload.ok === false) {
      const err = (payload && payload.error) || {};
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
      `Verification: ${payload.verification?.result || ""} (${model.verification_status || ""})`,
      `Validation: ${payload.validation?.status || "NOT_CLAIMED"}`,
      "",
      "INPUTS",
    ];
    Object.entries(payload.inputs || {}).forEach(([key, item]) => {
      const value = item && typeof item === "object" ? item.value : item;
      const unit = item && typeof item === "object" ? item.unit || "" : "";
      lines.push(`${key}: ${value} ${unit}`.trim());
    });
    lines.push("", "OUTPUTS");
    Object.entries(payload.outputs || {}).forEach(([key, item]) => {
      const value = item && typeof item === "object" ? item.value : item;
      const unit = item && typeof item === "object" ? item.unit || "" : "";
      lines.push(`${key}: ${value} ${unit}`.trim());
    });
    if ((payload.warnings || []).length) {
      lines.push("", "WARNINGS");
      payload.warnings.forEach((w) => lines.push(`- ${w}`));
    }
    return lines.join("\n");
  }

  function setResult(payload) {
    const el = $("suite-result");
    if (!el) return;
    el.classList.toggle("error", !(payload && payload.ok));
    if (payload && (payload.phase3 || payload.phase4 || payload.stages)) {
      el.textContent = JSON.stringify(payload, null, 2);
      return;
    }
    el.textContent = formatResult(payload);
  }

  async function postJson(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.json().catch(() => ({
      ok: false,
      error: { code: "ParseError", message: `Bad response (${res.status})` },
    }));
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

  function buildWorkflowCard() {
    return makeCard("End-to-end propulsion workflow", (card) => {
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      const fields = [
        field("Design name", { type: "text", value: "Rocket Engine Analysis", id: "wf-name" }),
        field("Pc [Pa]", { type: "number", step: "any", value: "5000000", id: "wf-pc" }),
        field("O/F", { type: "number", step: "any", value: "2.3", id: "wf-of" }),
        field("ε (Ae/At)", { type: "number", step: "any", value: "8", id: "wf-eps" }),
        field("Propellants (OX/FUEL)", { type: "text", value: "LOX/RP-1", id: "wf-props" }),
        field("Tc assumed [K]", { type: "number", step: "any", value: "3000", id: "wf-tc" }),
        field("γ assumed", { type: "number", step: "any", value: "1.2", id: "wf-gamma" }),
        field("MW assumed [kg/mol]", { type: "number", step: "any", value: "0.022", id: "wf-mw" }),
        field("At [m²]", { type: "number", step: "any", value: "0.01", id: "wf-at" }),
        field("L* [m]", { type: "number", step: "any", value: "1.0", id: "wf-lstar" }),
        field("Wall t [m]", { type: "number", step: "any", value: "0.006", id: "wf-twall" }),
      ];
      fields.forEach((f) => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const note = document.createElement("p");
      note.className = "suite-note";
      note.textContent =
        "Phase 3–6: performance → subsystems → summary → consistency → design review → export. Thermochemistry uses ASSUMED chamber state unless CEA is bound. Injector / regen cooling remain NOT_IMPLEMENTED. Validation = NOT_CLAIMED.";
      card.appendChild(note);

      const board = document.createElement("div");
      board.className = "suite-workflow-board";
      board.id = "wf-board";
      board.setAttribute("aria-live", "polite");
      card.appendChild(board);

      const actions = document.createElement("div");
      actions.className = "suite-actions";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Run full workflow (Phase 3→6)";
      const exportBtn = document.createElement("button");
      exportBtn.type = "button";
      exportBtn.textContent = "Export design package";
      exportBtn.disabled = true;
      let lastDesignId = null;

      function renderBoard(workflow) {
        board.innerHTML = "";
        if (!workflow || !workflow.nodes) {
          board.textContent = "Workflow board will appear after a run.";
          return;
        }
        const table = document.createElement("table");
        table.className = "suite-board-table";
        const thead = document.createElement("thead");
        thead.innerHTML =
          "<tr><th>Stage</th><th>Impl</th><th>Status</th><th>Current?</th></tr>";
        table.appendChild(thead);
        const tbody = document.createElement("tbody");
        workflow.nodes.forEach((node) => {
          const tr = document.createElement("tr");
          const current = node.result_is_current ? "yes" : "no";
          tr.innerHTML =
            "<td>" +
            node.name +
            "</td><td>" +
            node.implementation_status +
            "</td><td>" +
            node.status +
            "</td><td>" +
            current +
            "</td>";
          if (node.status === "STALE") tr.classList.add("is-stale");
          if (node.status === "CURRENT") tr.classList.add("is-current");
          if (node.status === "NOT_IMPLEMENTED") tr.classList.add("is-ni");
          tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        board.appendChild(table);
      }

      btn.addEventListener("click", async () => {
        try {
          setResult({ ok: true, status: "RUNNING", message: "Creating design…" });
          const created = await postJson("/api/propulsion/designs", {
            name: $("wf-name").value,
            description: "GUI workflow Phase 3–6",
          });
          if (!created.ok) {
            setResult(created);
            return;
          }
          const designId = created.design.design_id;
          lastDesignId = designId;
          await postJson(`/api/propulsion/designs/${designId}/requirements`, {
            updates: {
              target_chamber_pressure: Number($("wf-pc").value),
              mixture_ratio: Number($("wf-of").value),
              expansion_ratio: Number($("wf-eps").value),
              propellant_selection: $("wf-props").value,
              ambient_pressure: 101325,
            },
          });
          const p3 = await postJson(`/api/propulsion/designs/${designId}/run/phase3`, {
            chamber_temperature_k: Number($("wf-tc").value),
            gamma: Number($("wf-gamma").value),
            molecular_weight_kg_per_mol: Number($("wf-mw").value),
            throat_area_m2: Number($("wf-at").value),
            expansion_ratio: Number($("wf-eps").value),
          });
          const p4 = await postJson(`/api/propulsion/designs/${designId}/run/phase4`, {
            characteristic_length_m: Number($("wf-lstar").value),
            wall_thickness_m: Number($("wf-twall").value),
          });
          const p6 = await postJson(`/api/propulsion/designs/${designId}/run/phase6`, {});
          const workflow = (p6 && p6.workflow) || (p4 && p4.workflow) || null;
          renderBoard(workflow);
          exportBtn.disabled = false;
          const review = p6 && p6.stages && p6.stages.design_review;
          const summary =
            p6 &&
            p6.stages &&
            p6.stages.performance_summary &&
            p6.stages.performance_summary.outputs &&
            p6.stages.performance_summary.outputs.consolidated;
          setResult({
            ok: Boolean(p3.ok && p4.ok && p6.ok),
            design_id: designId,
            phase3: p3,
            phase4: p4,
            phase6: p6,
            consolidated: summary || null,
            review_ready: Boolean(review && review.outputs && review.outputs.review_ready),
          });
        } catch (err) {
          setResult({
            ok: false,
            error: { code: "WorkflowError", message: String(err.message || err) },
          });
        }
      });

      exportBtn.addEventListener("click", async () => {
        if (!lastDesignId) return;
        try {
          const resp = await fetch(`/api/propulsion/designs/${lastDesignId}/export`, {
            credentials: "same-origin",
          });
          const data = await resp.json();
          if (!data.ok) {
            setResult(data);
            return;
          }
          const blob = new Blob([JSON.stringify(data.package, null, 2)], {
            type: "application/json",
          });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `cosmos_propulsion_${lastDesignId}.json`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
          setResult({
            ok: true,
            exported: true,
            design_id: lastDesignId,
            export_format: data.package.export_format,
            disclaimer: data.package.disclaimer,
          });
        } catch (err) {
          setResult({
            ok: false,
            error: { code: "ExportError", message: String(err.message || err) },
          });
        }
      });

      actions.appendChild(btn);
      actions.appendChild(exportBtn);
      card.appendChild(actions);
      renderBoard(null);
    });
  }

  function buildIsentropicCard() {
    return makeCard("Isentropic stagnation ratios", (card) => {
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      const gamma = field("γ (gamma)", {
        type: "number",
        step: "any",
        value: "1.2",
        id: "iso-gamma",
      });
      const mach = field("Mach", {
        type: "number",
        step: "any",
        value: "2.5",
        id: "iso-mach",
      });
      [gamma, mach].forEach((f) => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const actions = document.createElement("div");
      actions.className = "suite-actions";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Evaluate";
      btn.addEventListener("click", async () => {
        setResult(
          await postJson("/api/physics/compressible/isentropic", {
            mach: Number($("iso-mach").value),
            gamma: Number($("iso-gamma").value),
          })
        );
      });
      actions.appendChild(btn);
      card.appendChild(actions);
    });
  }

  function buildAreaMachCard() {
    return makeCard("Area–Mach (A/A*)", (card) => {
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      const gamma = field("γ (gamma)", {
        type: "number",
        step: "any",
        value: "1.2",
        id: "am-gamma",
      });
      const mode = selectField(
        "Mode",
        [
          ["inverse", "Mach from A/A*"],
          ["forward", "A/A* from Mach"],
        ],
        { id: "am-mode" }
      );
      const ar = field("A / A*", {
        type: "number",
        step: "any",
        value: "4",
        id: "am-ar",
      });
      const mach = field("Mach", {
        type: "number",
        step: "any",
        value: "2.5",
        id: "am-mach",
      });
      const branch = selectField(
        "Branch",
        [
          ["supersonic", "Supersonic"],
          ["subsonic", "Subsonic"],
        ],
        { id: "am-branch" }
      );
      [gamma, mode, ar, mach, branch].forEach((f) => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const actions = document.createElement("div");
      actions.className = "suite-actions";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Evaluate";
      btn.addEventListener("click", async () => {
        setResult(
          await postJson("/api/physics/compressible/area-mach", {
            mode: $("am-mode").value,
            gamma: Number($("am-gamma").value),
            mach: Number($("am-mach").value),
            area_ratio: Number($("am-ar").value),
            branch: $("am-branch").value,
          })
        );
      });
      actions.appendChild(btn);
      card.appendChild(actions);
    });
  }

  function buildBartzCard() {
    return makeCard("Bartz gas-side HTC", (card) => {
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      const fields = [
        field("Diameter [m]", {
          type: "number",
          step: "any",
          value: "0.05",
          id: "bt-d",
        }),
        field("μ [Pa·s]", {
          type: "number",
          step: "any",
          value: "1e-4",
          id: "bt-mu",
        }),
        field("k [W/(m·K)]", {
          type: "number",
          step: "any",
          value: "0.25",
          id: "bt-k",
        }),
        field("cp [J/(kg·K)]", {
          type: "number",
          step: "any",
          value: "2000",
          id: "bt-cp",
        }),
        field("Pc [Pa]", {
          type: "number",
          step: "any",
          value: "7e6",
          id: "bt-pc",
        }),
        field("c* [m/s]", {
          type: "number",
          step: "any",
          value: "1500",
          id: "bt-cstar",
        }),
        field("Mach", { type: "number", step: "any", value: "1", id: "bt-mach" }),
        field("γ (gamma)", {
          type: "number",
          step: "any",
          value: "1.2",
          id: "bt-gamma",
        }),
        field("Twall [K]", {
          type: "number",
          step: "any",
          value: "800",
          id: "bt-tw",
        }),
        field("Taw [K]", {
          type: "number",
          step: "any",
          value: "3000",
          id: "bt-taw",
        }),
        field("Curvature R [m] (opt)", {
          type: "number",
          step: "any",
          value: "",
          id: "bt-rw",
          placeholder: "optional",
        }),
      ];
      fields.forEach((f) => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const actions = document.createElement("div");
      actions.className = "suite-actions";
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
        setResult(await postJson("/api/physics/heat-transfer/bartz", body));
      });
      actions.appendChild(btn);
      card.appendChild(actions);
    });
  }

  function buildThinWallCard() {
    return makeCard("Thin-wall cylinder stress", (card) => {
      const grid = document.createElement("div");
      grid.className = "suite-grid";
      [
        field("Pressure [Pa]", {
          type: "number",
          step: "any",
          value: "7e6",
          id: "tw-p",
        }),
        field("Radius [m]", {
          type: "number",
          step: "any",
          value: "0.1",
          id: "tw-r",
        }),
        field("Thickness [m]", {
          type: "number",
          step: "any",
          value: "0.005",
          id: "tw-t",
        }),
        field("Temperature [K]", {
          type: "number",
          step: "any",
          value: "300",
          id: "tw-temp",
        }),
      ].forEach((f) => grid.appendChild(f.wrap));
      card.appendChild(grid);
      const actions = document.createElement("div");
      actions.className = "suite-actions";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Evaluate stress";
      btn.addEventListener("click", async () => {
        setResult(
          await postJson("/api/physics/structures/thin-wall", {
            pressure_pa: Number($("tw-p").value),
            radius_m: Number($("tw-r").value),
            thickness_m: Number($("tw-t").value),
            temperature_k: Number($("tw-temp").value),
          })
        );
      });
      actions.appendChild(btn);
      card.appendChild(actions);
    });
  }

  function plannedNote(mod) {
    const p = document.createElement("p");
    p.className = "suite-note";
    p.textContent =
      mod.status === "planned"
        ? `PLANNED — ${mod.description} No live API yet. validation_status remains NOT_CLAIMED until adapters exist.`
        : mod.description;
    return p;
  }

  function renderModule(mod) {
    $("suite-module-title").textContent = mod.title;
    $("suite-module-desc").textContent = mod.description;
    $("suite-module-ref").textContent = mod.reference || "";
    const forms = $("suite-forms");
    forms.innerHTML = "";
    $("suite-result").textContent = "No calculation yet.";
    $("suite-result").classList.remove("error");

    const cards = mod.cards || [];
    if (!cards.length) {
      forms.appendChild(plannedNote(mod));
      return;
    }
    cards.forEach((id) => {
      if (id === "workflow-e2e") forms.appendChild(buildWorkflowCard());
      if (id === "isentropic") forms.appendChild(buildIsentropicCard());
      if (id === "area-mach") forms.appendChild(buildAreaMachCard());
      if (id === "bartz") forms.appendChild(buildBartzCard());
      if (id === "thin-wall") forms.appendChild(buildThinWallCard());
    });
    if (mod.status === "partial") {
      forms.appendChild(plannedNote(mod));
    }
  }

  function renderNav(activeId) {
    const nav = $("suite-nav");
    if (!nav) return;
    nav.innerHTML = "";
    MODULES.forEach((mod) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = mod.id === activeId ? "active" : "";
      btn.innerHTML = `<span class="nav-group">${mod.group}</span><span class="nav-title">${mod.title}</span><span class="status ${mod.status}">${mod.status.toUpperCase()}</span>`;
      btn.addEventListener("click", () => {
        renderNav(mod.id);
        renderModule(mod);
        const url = new URL(window.location.href);
        url.searchParams.set("module", mod.id);
        window.history.replaceState({}, "", url);
      });
      nav.appendChild(btn);
    });
  }

  async function initPropulsionSuite() {
    if (window.COSMOS && typeof COSMOS.initShell === "function") {
      const session = await COSMOS.initShell({ activeNav: "command" });
      if (!session) return;
    }
    const params = new URLSearchParams(window.location.search);
    const wanted = params.get("module") || "nozzle-flow";
    const mod = MODULES.find((m) => m.id === wanted) || MODULES[3];
    renderNav(mod.id);
    renderModule(mod);
    if (window.COSMOS && typeof COSMOS.setStatusBar === "function") {
      COSMOS.setStatusBar("Rocket Engine propulsion suite", "ready", "COSMOS 0.1");
    }
  }

  window.COSMOS = window.COSMOS || {};
  window.COSMOS.initPropulsionSuite = initPropulsionSuite;
  window.COSMOS.PROPULSION_SUITE_MODULES = MODULES;
})();
