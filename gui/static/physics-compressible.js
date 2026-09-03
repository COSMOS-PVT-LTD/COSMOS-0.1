/* Compressible-flow GUI vertical slice — presentation only; no Physics equations. */
(function () {
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
      `Version: ${model.version || ""}`,
      `Source: ${model.source || ""}`,
      `Validity: ${model.validity_range || ""}`,
      `Verification: ${payload.verification?.result || ""} (${model.verification_status || ""})`,
      `Validation: ${payload.validation?.status || "NOT_CLAIMED"}`,
      "",
      "INPUTS",
    ];
    Object.entries(payload.inputs || {}).forEach(([key, item]) => {
      lines.push(`${key}: ${item.value} ${item.unit || ""}`.trim());
    });
    lines.push("", "OUTPUTS");
    Object.entries(payload.outputs || {}).forEach(([key, item]) => {
      lines.push(`${key}: ${item.value} ${item.unit || ""}`.trim());
    });
    if ((payload.warnings || []).length) {
      lines.push("", "WARNINGS");
      payload.warnings.forEach((w) => lines.push(`- ${w}`));
    }
    if ((model.assumptions || []).length) {
      lines.push("", "ASSUMPTIONS");
      model.assumptions.forEach((a) => lines.push(`- ${a}`));
    }
    return lines.join("\n");
  }

  async function postJson(url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    return { response, payload };
  }

  function show(payload) {
    const node = document.getElementById("physics-result");
    if (!node) return;
    node.textContent = formatResult(payload);
    node.classList.toggle("error", !(payload && payload.ok));
  }

  window.COSMOS = window.COSMOS || {};
  COSMOS.initPhysicsCompressiblePage = async function initPhysicsCompressiblePage() {
    const session = await this.initShell({ activeNav: "physics" });
    if (!session) return;

    document.getElementById("isen-run")?.addEventListener("click", async () => {
      const mach = Number(document.getElementById("isen-mach").value);
      const gamma = Number(document.getElementById("isen-gamma").value);
      const { payload } = await postJson("/api/physics/compressible/isentropic", { mach, gamma });
      show(payload);
    });

    document.getElementById("am-run")?.addEventListener("click", async () => {
      const mode = document.getElementById("am-mode").value;
      const gamma = Number(document.getElementById("am-gamma").value);
      const body = {
        mode,
        gamma,
        mach: Number(document.getElementById("am-mach").value),
        area_ratio: Number(document.getElementById("am-area").value),
        branch: document.getElementById("am-branch").value,
      };
      const { payload } = await postJson("/api/physics/compressible/area-mach", body);
      show(payload);
    });
  };
})();
