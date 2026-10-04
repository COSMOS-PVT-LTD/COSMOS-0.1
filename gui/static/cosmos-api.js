/**
 * COSMOS application HTTP client — timeouts, credentials, JSON error mapping.
 * Presentation layer only. No engineering equations.
 */
(function (global) {
  "use strict";

  const DEFAULT_TIMEOUT_MS = 20000;

  function errorFromBody(status, body) {
    if (!body || typeof body !== "object") {
      return { code: "HttpError", message: `HTTP ${status}`, action: "Retry the request." };
    }
    if (body.error && typeof body.error === "object") return body.error;
    if (typeof body.error === "string") {
      return {
        code: body.error_code || "HttpError",
        message: body.error,
        action: "Correct the input and retry.",
      };
    }
    return { code: "HttpError", message: `HTTP ${status}`, action: "Retry the request." };
  }

  async function request(method, url, body, timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs || DEFAULT_TIMEOUT_MS);
    try {
      const headers = { Accept: "application/json" };
      let payload;
      if (body instanceof FormData) {
        payload = body;
      } else if (body !== undefined) {
        headers["Content-Type"] = "application/json";
        payload = JSON.stringify(body);
      }
      const response = await fetch(url, {
        method,
        credentials: "same-origin",
        headers,
        body: payload,
        signal: controller.signal,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const error = errorFromBody(response.status, data);
        const failure = {
          ok: false,
          status: response.status,
          error,
        };
        return failure;
      }
      if (data && typeof data === "object" && data.ok === false) return data;
      return data;
    } catch (err) {
      const aborted = err && err.name === "AbortError";
      return {
        ok: false,
        error: {
          code: aborted ? "Timeout" : "NetworkError",
          message: aborted
            ? `Request timed out after ${(timeoutMs || DEFAULT_TIMEOUT_MS) / 1000}s.`
            : String(err.message || err),
          action: aborted ? "Check the COSMOS server and retry." : "Check that COSMOS is running.",
        },
      };
    } finally {
      clearTimeout(timer);
    }
  }

  const CosmosAPI = {
    timeoutMs: DEFAULT_TIMEOUT_MS,
    get(url) {
      return request("GET", url, undefined, this.timeoutMs);
    },
    post(url, body) {
      return request("POST", url, body === undefined ? {} : body, this.timeoutMs);
    },
    listDesigns() {
      return this.get("/api/propulsion/designs");
    },
    createDesign(payload) {
      return this.post("/api/propulsion/designs", payload);
    },
    getDesign(id) {
      return this.get(`/api/propulsion/designs/${id}`);
    },
    saveDesign(id) {
      return this.post(`/api/propulsion/designs/${id}/save`, {});
    },
    cloneDesign(id, name) {
      return this.post(`/api/propulsion/designs/${id}/clone`, name ? { name } : {});
    },
    updateRequirements(id, updates) {
      return this.post(`/api/propulsion/designs/${id}/requirements`, { updates });
    },
    updatePropellants(id, payload) {
      return this.post(`/api/propulsion/designs/${id}/propellants`, payload);
    },
    updateCycle(id, cycleType) {
      return this.post(`/api/propulsion/designs/${id}/cycle`, { cycle_type: cycleType });
    },
    runPhase3(id, payload) {
      return this.post(`/api/propulsion/designs/${id}/run/phase3`, payload);
    },
    runPhase4(id, payload) {
      return this.post(`/api/propulsion/designs/${id}/run/phase4`, payload);
    },
    runPhase6(id) {
      return this.post(`/api/propulsion/designs/${id}/run/phase6`, {});
    },
    getWorkflow(id) {
      return this.get(`/api/propulsion/designs/${id}/workflow`);
    },
    exportDesign(id) {
      return this.get(`/api/propulsion/designs/${id}/export`);
    },
    getSuiteCatalog() {
      return this.get("/api/workbenches/rocket-engine/suite");
    },
    getPropellantCatalog() {
      return this.get("/api/catalogs/propellants");
    },
    getMaterialCatalog() {
      return this.get("/api/catalogs/materials");
    },
    getWorkflowCatalog() {
      return this.get("/api/propulsion/workflow-catalog");
    },
    getStageResult(id, stageId, allowStale) {
      const query = allowStale ? "?allow_stale=1" : "";
      return this.get(`/api/propulsion/designs/${id}/stages/${stageId}${query}`);
    },
  };

  global.CosmosAPI = CosmosAPI;
})(window);
