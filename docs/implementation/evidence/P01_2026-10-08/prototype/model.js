/* P01 synthetic workflow state only. No Physics, CEA, CAD or persistence API. */
(function (root) {
  "use strict";
  const freeze = value => {
    if (value && typeof value === "object") {
      Object.values(value).forEach(freeze);
      Object.freeze(value);
    }
    return value;
  };
  const copy = value => JSON.parse(JSON.stringify(value));
  const PARAMETERS = freeze({pressurePa: 500000, thrustN: 1000, mixtureRatio: 2.7239,
    expansionRatio: 10, ambientPa: 0, throatAreaM2: 0.001, fuelTemperatureK: 111.67,
    oxidizerTemperatureK: 90.17, fuel: "LCH4", oxidizer: "LOX", model: "NASA CEA 3.3.4"});
  const DIMENSIONS = freeze({pressurePa: "Pa", thrustN: "N", mixtureRatio: "1",
    expansionRatio: "1", ambientPa: "Pa", throatAreaM2: "m²", fuelTemperatureK: "K",
    oxidizerTemperatureK: "K"});
  const TRANSITIONS = freeze({Idle: ["Queued"], Queued: ["Running", "Cancelled"],
    Running: ["QA", "Failed", "CancelRequested"], CancelRequested: ["Cancelled"],
    QA: ["Accepted", "Rejected"], Accepted: ["Published"], Published: [], Failed: [],
    Rejected: [], Cancelled: []});
  const MODES = freeze(["Guided", "Standard", "Expert"]);

  function createState() {
    const snapshot = freeze({id: "demo-r1", revision: 1, parametersSI: copy(PARAMETERS), prototypeOnly: true});
    return {route: "projects", mode: "Standard", opened: false, draft: {...copy(PARAMETERS), ambientPa: null},
      baseSnapshotId: snapshot.id, inspectedSnapshotId: snapshot.id, snapshots: [snapshot],
      results: [], job: {state: "Idle", events: [], snapshotId: null, published: false}, undo: []};
  }
  function snapshot(state, id = state.baseSnapshotId) {
    const found = state.snapshots.find(item => item.id === id);
    if (!found) throw new Error("SnapshotNotFound");
    return found;
  }
  function preflight(state) {
    const errors = [];
    const limits = {pressurePa: "positive", thrustN: "positive", mixtureRatio: "positive",
      expansionRatio: "greaterThanOne", ambientPa: "nonNegative", throatAreaM2: "positive",
      fuelTemperatureK: "positive", oxidizerTemperatureK: "positive"};
    for (const [key, limit] of Object.entries(limits)) {
      const value = state.draft[key];
      if (value === null || value === undefined || value === "") {
        errors.push({code: "RequiredInputMissing", field: key, cause: `${key} requires an explicit value.`, recovery: `Enter ${DIMENSIONS[key]}; blank is not zero.`});
      } else if (!Number.isFinite(value) || (limit === "positive" && value <= 0) ||
        (limit === "nonNegative" && value < 0) || (limit === "greaterThanOne" && value <= 1)) {
        errors.push({code: "InvalidParameter", field: key, cause: `${key} is outside the basic input constraint.`, recovery: "Correct this value; native model applicability checks are not executed in P01."});
      }
    }
    if (!state.draft.fuel || !state.draft.oxidizer || !state.draft.model) {
      errors.push({code: "ModelSelectionMissing", field: "model", cause: "An explicit model and propellant pair are required.", recovery: "Select a supported pair in the production workbench."});
    }
    return errors;
  }
  function dirty(state) {
    return JSON.stringify(state.draft) !== JSON.stringify(snapshot(state).parametersSI);
  }
  function edit(state, field, value) {
    if (!(field in PARAMETERS)) throw new Error("UnknownParameter");
    state.undo.push(copy(state.draft));
    state.draft[field] = value;
  }
  function undo(state) {
    if (state.undo.length) state.draft = state.undo.pop();
  }
  function setMode(state, mode) {
    if (!MODES.includes(mode)) throw new Error("UnknownMode");
    state.mode = mode;
  }
  function navigate(state, route) {
    const routes = ["projects", "rocket", "ngg", "simulation", "vv", "knowledge", "reports"];
    if (!routes.includes(route)) throw new Error("UnknownDestination");
    state.route = route;
  }
  function commit(state, expectedId = state.baseSnapshotId) {
    if (expectedId !== state.baseSnapshotId) throw new Error("RevisionConflict");
    if (preflight(state).length) throw new Error("PreflightRejected");
    if (!dirty(state)) return snapshot(state);
    const next = freeze({id: `demo-r${state.snapshots.length + 1}`, revision: state.snapshots.length + 1,
      parametersSI: copy(state.draft), prototypeOnly: true});
    state.snapshots.push(next);
    state.baseSnapshotId = next.id;
    state.inspectedSnapshotId = next.id;
    state.undo = [];
    return next;
  }
  function inspect(state, id) {
    snapshot(state, id);
    state.inspectedSnapshotId = id; // Never replaces the active draft or its base.
  }
  function recordFixtureResult(state, outcome) {
    if (dirty(state) || preflight(state).length) throw new Error("SaveExplicitInputsFirst");
    if (!["CURRENT", "FAILED", "OUT_OF_RANGE"].includes(outcome)) throw new Error("UnknownFixture");
    const result = freeze({id: `demo-result-${state.results.length + 1}`, snapshotId: state.baseSnapshotId,
      status: outcome, execution: outcome === "CURRENT" ? "Completed fixture" : "Failed fixture",
      termination: "Scripted; no native calculation", physicalChecks: "Not executed",
      verification: "Not assessed", validation: "Not claimed", prototypeOnly: true});
    state.results.push(result);
    return result;
  }
  function visibleStatus(state, result) {
    if (["FAILED", "OUT_OF_RANGE"].includes(result.status)) return result.status;
    return dirty(state) || result.snapshotId !== state.baseSnapshotId ? "STALE" : result.status;
  }
  function canExport() { return false; } // No real artifact or qualified backend exists.
  function startFixtureJob(state) {
    if (dirty(state) || preflight(state).length) throw new Error("SnapshotRequired");
    if (["Queued", "Running", "QA", "CancelRequested", "Accepted"].includes(state.job.state)) throw new Error("JobAlreadyActive");
    state.job = {state: "Idle", events: [], snapshotId: state.baseSnapshotId, published: false};
    transition(state, "Queued");
  }
  function transition(state, next) {
    if (!(TRANSITIONS[state.job.state] || []).includes(next)) throw new Error("InvalidJobTransition");
    state.job.state = next;
    state.job.events.push({seq: state.job.events.length + 1, state: next, prototypeOnly: true});
    state.job.published = next === "Published"; // Scripted manifest marker, never a real artifact.
  }
  const api = {createState, snapshot, preflight, dirty, edit, undo, setMode, navigate, commit, inspect,
    recordFixtureResult, visibleStatus, canExport, startFixtureJob, transition, PARAMETERS, DIMENSIONS, MODES};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.CosmosP01Model = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
