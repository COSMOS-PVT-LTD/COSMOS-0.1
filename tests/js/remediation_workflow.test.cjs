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
    api: () => Object.fromEntries(["updateRequirements", "updatePropellants", "runPhase3", "runPhase4", "runPhase6"].map((name) => [
      name, async (id, payload) => { calls.push({name, id, payload}); return {ok: true}; },
    ])),
    document: {createElement: (tag) => ({tag, children: [], textContent: "", appendChild(child) {this.children.push(child);}})},
  };
  vm.createContext(context);
  vm.runInContext(["num", "phase4Inputs", "runWorkflow", "runWorkflowFromDesign", "formatScalar", "formatResult", "renderStructuredPhase"].map(definition).join("\n"), context);
  return {context, fields, calls};
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
    const p3 = calls.find((call) => call.name === "runPhase3").payload;
    const p4 = calls.find((call) => call.name === "runPhase4").payload;
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

test("blank engineering fields send missing values, never invented fallbacks", async () => {
  const {context, fields, calls} = harness();
  context.state.design.operating_point.gamma = 1.2;
  fields["wf-gamma"].value = "";
  await context.runWorkflowFromDesign("test-design");
  assert.equal(calls.find((call) => call.name === "runPhase3").payload.gamma, null);
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
