"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const source = fs.readFileSync(path.join(__dirname, "../../gui/static/propulsion-suite.js"), "utf8");
// Execute the actual workflow DTO functions without duplicating their logic.
const definitions = [...source.matchAll(/^  (?:async )?function (\w+)\(/gm)];
function definition(name) {
  const index = definitions.findIndex((match) => match[1] === name);
  assert.notEqual(index, -1);
  return source.slice(definitions[index].index, definitions[index + 1].index);
}

function harness() {
  const values = {
    "wf-pc": "50", "wf-thrust": "10", "wf-pa": "0", "wf-of": "2.3", "wf-eps": "8",
    "wf-tc": "3000", "wf-gamma": "1.2", "wf-mw": "0.022", "wf-at": "0.01",
    "wf-lstar": "1", "wf-cr": "2.5", "wf-twall": "0.006", "wf-pout": "0",
    "wf-tmaterial": "300", "wf-mu": "0.00008", "wf-k": "0.3", "wf-cp": "2500",
    "wf-tw": "800", "wf-curvature": "", "wf-ox": "LOX", "wf-fuel": "RP1",
    "wf-material": "stainless_304",
    "wf-thermo-mode": "assumed",
  };
  const fields = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, {value}]));
  const calls = [];
  const clearForms = async () => { for (const field of Object.values(fields)) field.value = ""; };
  const context = {
    state: {design: {requirements: {}, operating_point: {}, propellant_configuration: {}}},
    $: (id) => fields[id] || null,
    requireDesign: () => "test-design",
    setResult: () => {},
    quantityInputValue: (value) => value?.magnitude ?? "",
    refreshDesign: clearForms,
    persistWorkflowInputs: async () => { await clearForms(); return {ok: true}; },
    api: () => Object.fromEntries(["saveDesign", "updateRequirements", "updatePropellants", "runPhase3", "runPhase4", "runPhase6", "runDesignWorkflow"].map((name) => [
      name, async (id, payload) => { calls.push({name, id, payload}); return {ok: true}; },
    ])),
    document: {createElement: (tag) => ({tag, children: [], textContent: "", appendChild(child) {this.children.push(child);}})},
  };
  vm.createContext(context);
  vm.runInContext(["defaultThermochemistryMode", "thermochemistryDraftInputs", "withThermochemistryInputs", "subsystemFields", "subsystemDraftInputs", "appendSubsystemVisual", "num", "phase4Inputs", "persistDesignInputs", "missingThermochemistryInputs", "runWorkflow", "runWorkflowFromDesign", "formatScalar", "formatResult", "renderStructuredPhase"].map(definition).join("\n"), context);
  return {context, fields, calls};
}

test("Save maps applied requirements and keeps solver text as drafts, including zero and blank", () => {
  const {context} = harness();
  context.state.design.revision = 7;
  context.state.drafts = {"wf-name": "Renamed", "wf-pc": "55", "wf-thrust": "10",
    "wf-pa": "0", "wf-tc": "3000", "wf-pout": "0", "wf-curvature": "",
    "wf-ox": "LOX", "wf-fuel": "RP1", "wf-of": "2.3"};
  vm.runInContext(definition("saveEdits"), context);
  const edits = context.saveEdits();
  assert.equal(edits.base_revision, 7);
  assert.equal(edits.name, "Renamed");
  assert.equal(edits.requirements.target_chamber_pressure.magnitude, 55);
  assert.equal(edits.requirements.ambient_pressure.magnitude, 0);
  assert.equal(edits.editor_drafts["wf-tc"], "3000");
  assert.equal(edits.editor_drafts["wf-pout"], "0");
  assert.equal(edits.editor_drafts["wf-curvature"], "");
  assert.equal(edits.editor_drafts["wf-pc"], undefined);
  assert.equal(edits.propellants.fuel_id, "RP1");
  assert.equal(context.state.drafts["wf-pc"], "55", "Failed saves must not erase pending edits");
});

test("saved draft inputs remain available for recalculation from another stage", () => {
  const {context, fields} = harness();
  context.state.drafts = {"wf-pout": "0", "wf-lstar": "1", "wf-material": "stainless_304"};
  delete fields["wf-pout"];
  delete fields["wf-lstar"];
  delete fields["wf-material"];
  const payload = context.phase4Inputs("wf");
  assert.equal(payload.external_pressure_pa, 0);
  assert.equal(payload.characteristic_length_m, 1);
  assert.equal(payload.material_id, "stainless_304");
});

test("optional presentation DTO absent before first calculation is null, not a JSON exception", () => {
  const {context} = harness();
  vm.runInContext(definition("immutableCopy"), context);
  assert.equal(context.immutableCopy(undefined), null);
  assert.equal(context.immutableCopy(null), null);
  const source = {status:"CURRENT", outputs:{actual:1}};
  const copy = context.immutableCopy(source);
  assert.ok(Object.isFrozen(copy.outputs));
  assert.equal(source.outputs.actual, 1);
  assert.notEqual(copy, source);
});

test("explicit pressure model is retained across workspace changes and sent with analysis", () => {
  const {context, fields} = harness();
  context.state.drafts = {"wf-pressure-model":"LAME_CLOSED_ENDS"};
  assert.equal(context.phase4Inputs("wf").pressure_model, "LAME_CLOSED_ENDS");
  fields["wf-pressure-model"] = {value:"THIN_WALL"};
  assert.equal(context.phase4Inputs("wf").pressure_model, "THIN_WALL");
});

test("baseline Save and Recalculate cannot erase embedded cycle/operating drafts", async () => {
  const {context, calls} = harness();
  context.state.supplementalDirty = () => true;
  const messages = [];
  context.setResult = value => messages.push(value);
  context.window = {confirm:()=>{throw new Error('Embedded draft must have an explicit retain/discard action');}};
  vm.runInContext(["canLeaveDesign", "saveActive", "recalculateActive"].map(definition).join('\n'),context);
  await context.saveActive();
  await context.recalculateActive();
  await context.runWorkflow();
  assert.equal(calls.length, 0);
  assert.equal(messages.length, 3);
  assert.ok(messages.every(value=>value.error.code==='UnsavedCycleInputs'));
});

test("CEA sends explicit reactant temperatures, never computed/manual chamber inputs", () => {
  const {context, fields} = harness();
  fields["wf-thermo-mode"].value = "nasa_cea";
  context.state.drafts = {"wf-fuel-temp": "111.67", "wf-ox-temp": "90.17"};
  const inputs = context.withThermochemistryInputs({gamma: 1.2, chamber_temperature_k: 3000, molecular_weight_kg_per_mol: 0.022});
  assert.equal(inputs.gamma, undefined);
  assert.equal(inputs.chamber_temperature_k, undefined);
  assert.equal(inputs.molecular_weight_kg_per_mol, undefined);
  assert.equal(inputs.thermochemistry_configuration.fuel_temperature_k, 111.67);
  assert.equal(context.missingThermochemistryInputs(inputs), null);
  context.state.drafts["wf-ox-temp"] = "";
  assert.equal(context.missingThermochemistryInputs(context.withThermochemistryInputs({})).status, "NOT_RUN");
});

test("Save applies CEA mode and temperatures and removes stale text overrides", () => {
  const {context} = harness();
  context.state.design.revision = 1;
  context.state.drafts = {"wf-thermo-mode": "nasa_cea", "wf-fuel-temp": "111.67", "wf-ox-temp": "90.17"};
  vm.runInContext(definition("saveEdits"), context);
  const edits = context.saveEdits();
  assert.equal(edits.thermochemistry_configuration.mode, "nasa_cea");
  assert.equal(edits.thermochemistry_configuration.oxidizer_temperature_k, 90.17);
  assert.equal(edits.editor_drafts["wf-fuel-temp"], undefined);
});

test("subsystem Save applies explicit configuration, clears blanks and retains omitted stages", () => {
  const {context} = harness();
  context.state.design.subsystem_inputs = {nozzle: {start_angle_deg: 30, exit_angle_deg: 8, point_count: 81}};
  const drafts = {"sub-nozzle-point_count": "161", "sub-nozzle-exit_angle_deg": "",
    "sub-cooling-film_slot_x_m": "0", "sub-cooling-film_mode": "gaseous_slot", "wf-tc": "3000"};
  const updates = context.subsystemDraftInputs(drafts);
  assert.equal(updates.nozzle.point_count, 161);
  assert.equal(updates.nozzle.exit_angle_deg, null);
  assert.equal(updates.nozzle.start_angle_deg, 30);
  assert.equal(updates.cooling.film_slot_x_m, 0);
  assert.equal(updates.cooling.film_mode, "gaseous_slot");
  assert.equal(updates.injector, undefined);
  assert.deepEqual(drafts, {"wf-tc": "3000"});
});

test("stale or failed subsystem results cannot render active plots or CSV exports", () => {
  const {context} = harness();
  const host = {appendChild() {throw new Error("An active plot/export was rendered");}};
  for (const status of ["STALE", "FAILED", "OUT_OF_RANGE", "NOT_CALCULATED"]) {
    context.appendSubsystemVisual(host, {status, stage_id: "nozzle", outputs: {stations: [{x_m: 1, radius_m: 1}]}});
  }
});

test("current subsystem CSV contains exact SI rows and rejects dirty or superseded results", () => {
  const {context} = harness();
  const downloads = [], failures = [], elements = [];
  context.document = {
    createElement(tag) {
      const element = {tag, children: [], classList: {add() {}}, setAttribute() {}, appendChild(child) {this.children.push(child);},
        addEventListener(event, action) {this[event] = action;}, click() {downloads.push(this.download);}, remove() {}};
      elements.push(element);
      return element;
    },
    body: {appendChild() {}},
  };
  context.document.createElementNS = (_, tag) => context.document.createElement(tag);
  let csv;
  context.Blob = class {constructor(parts) {csv = parts.join("");}};
  context.URL = {createObjectURL: () => "blob:test", revokeObjectURL() {}};
  context.setResult = (result) => failures.push(result);
  const result = {stage_id: "nozzle", result_id: "n1", status: "CURRENT", outputs: {stations: [{x_m: 0, radius_m: 0.02}, {x_m: 0.1, radius_m: 0.05}]}};
  context.state.design.workflow = {results: {nozzle: result}};
  context.appendSubsystemVisual({appendChild() {}}, result);
  const button = elements.find(element => element.tag === "button");
  button.click();
  assert.equal(csv, "x_m,radius_m\n0,0.02\n0.1,0.05");
  assert.deepEqual(downloads, ["cosmos_nozzle_n1.csv"]);
  context.state.dirty = true;
  button.click();
  context.state.dirty = false;
  context.state.design.workflow.results.nozzle = {...result, result_id: "n2"};
  button.click();
  assert.equal(downloads.length, 1);
  assert.equal(failures.length, 2);
  assert.equal(failures[0].error.code, "ExportNotCurrent");
});

test("rocket workbench defines COSMOS before loading centralized permissions", () => {
  const html = fs.readFileSync(path.join(__dirname, "../../gui/static/workbench/rocket-engine.html"), "utf8");
  assert.ok(html.indexOf('/assets/app.js') < html.indexOf('/assets/rbac.js'));
});

test("stale stored results and running/saved receipts are not unknown failures", () => {
  const {context} = harness();
  const text = context.formatResult({ok: true, status: "STALE", outputs: {mach: 2}});
  assert.ok(text.startsWith("STALE —"));
  assert.ok(text.includes("mach: 2"));
  assert.ok(!text.includes("CALCULATION FAILED"));
  assert.equal(context.formatResult({ok: true, status: "RUNNING", message: "Calculating…"}), "RUNNING\nCalculating…");
});

test("a late stored-result response cannot overwrite a receipt or another stage", async () => {
  const {context} = harness();
  let deliver;
  const displayed = [];
  context.state.design.design_id = "test-design";
  context.state.activeKind = "stage";
  context.state.activeId = "nozzle";
  context.state.resultGeneration = 5;
  context.api = () => ({getStageResult: () => new Promise(resolve => {deliver = resolve;})});
  context.setResult = (payload) => displayed.push(payload);
  vm.runInContext(definition("showStoredStageResult"), context);
  const pending = context.showStoredStageResult("nozzle");
  context.state.resultGeneration++;
  deliver({ok: true, result: {status: "CURRENT"}, displayable_as_current: true});
  await pending;
  assert.equal(displayed.length, 0);
  const moved = context.showStoredStageResult("nozzle");
  context.state.activeId = "requirements";
  deliver({ok: true, result: {status: "CURRENT"}, displayable_as_current: true});
  await moved;
  assert.equal(displayed.length, 0);
});

for (const failedPhase of ["runDesignWorkflow"]) {
  test(`${failedPhase} failure feedback survives the form refresh`, async () => {
    const {context} = harness();
    let feedback;
    context.setResult = (payload) => {feedback = payload;};
    context.refreshDesign = async () => {feedback = "No calculation yet.";};
    context.api = () => Object.fromEntries(["runDesignWorkflow"].map(name => [name,
      async () => name === failedPhase ? {ok: false, error: {message: "Explicit boundary is missing"}} : {ok: true},
    ]));
    await context.runWorkflow();
    assert.equal(feedback.error.message, "Explicit boundary is missing");
  });
}

test("blank/non-finite inputs remain missing; explicit zero remains zero", () => {
  const {context, fields} = harness();
  for (const value of ["", " ", "NaN", "Infinity", "not-a-number"]) {
    fields["wf-pa"].value = value;
    assert.equal(context.num("wf-pa"), null);
  }
  fields["wf-pa"].value = "0";
  assert.equal(context.num("wf-pa"), 0);
});

for (const entrypoint of ["runWorkflow", "runWorkflowFromDesign"]) {
  test(`${entrypoint} preserves explicit solver inputs across form refresh`, async () => {
    const {context, fields, calls} = harness();
    await context[entrypoint]("test-design");
    assert.equal(fields["wf-tc"].value, "");
    const analysisCalls=calls.filter(call=>call.name==='runDesignWorkflow');
    assert.equal(analysisCalls.length,1,'One captured analysis, not three stop-on-first-error calls');
    const p3 = analysisCalls[0].payload.phase3_inputs;
    const p4 = analysisCalls[0].payload.phase4_inputs;
    assert.equal(p3.chamber_temperature_k, 3000);
    assert.equal(p3.gamma, 1.2);
    assert.equal(p3.throat_area_m2, 0.01);
    assert.equal(p4.characteristic_length_m, 1);
    assert.equal(p4.external_pressure_pa, 0);
    assert.equal(p4.material_id, "stainless_304");
    assert.equal(p4.viscosity_pa_s, 0.00008);
    assert.equal(p4.throat_curvature_radius_m, null);
  });
}

test('thermal CEA selection never sends prefilled manual transport as a mixed source',()=>{
  const {context,fields}=harness();
  fields['wf-gas-property-mode']={value:'CEA_CHAMBER_FROZEN_TRANSPORT'};
  const payload=context.phase4Inputs('wf');
  assert.equal(payload.gas_property_mode,'CEA_CHAMBER_FROZEN_TRANSPORT');
  assert.equal(payload.viscosity_pa_s,null);
  assert.equal(payload.conductivity_w_m_k,null);
  assert.equal(payload.cp_j_kg_k,null);
  assert.equal(payload.wall_temperature_k,800);
});

test("blank thermochemistry fields block full-form recalculation rather than reuse saved values", async () => {
  const {context, fields, calls} = harness();
  context.state.design.operating_point.gamma = 1.2;
  fields["wf-gamma"].value = "";
  const result = await context.runWorkflowFromDesign("test-design");
  assert.equal(result.ok, false);
  assert.equal(result.error.code, "MissingExplicitInputs");
  assert.ok(result.error.message.includes("gamma"));
  assert.equal(calls.length, 0);
});

test("UI distinguishes execution success from completeness and validation", () => {
  const {context} = harness();
  const rendered = context.renderStructuredPhase({ok: true, execution_ok: true,
    workflow_complete: false, engineering_readiness: "PRELIMINARY", validation_level: "NOT_CLAIMED", stages: {}});
  const text = rendered.children[0].textContent;
  for (const truth of ["EXECUTION SUCCEEDED", "workflow_complete=false", "readiness=PRELIMINARY", "validation=NOT_CLAIMED"]) {
    assert.ok(text.includes(truth));
  }
});

for (const status of ["FAILED", "OUT_OF_RANGE"]) {
  test(`UI preserves structured ${status} stage diagnostics`, () => {
    const {context} = harness();
    const rendered = context.renderStructuredPhase({ok: false, stages: {structure: {
      status, errors: [{code: "OutOfRangeError", message: "External pressure exceeds internal pressure"}],
    }}});
    const text = rendered.children[1].children[1].textContent;
    assert.ok(text.includes("External pressure exceeds internal pressure"));
    assert.ok(text.includes("OutOfRangeError"));
  });
}
