"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const source = fs.readFileSync(path.join(__dirname, "../../gui/static/propulsion-suite.js"), "utf8");
const html = fs.readFileSync(path.join(__dirname, "../../gui/static/workbench/rocket-engine.html"), "utf8");
const definitions = [...source.matchAll(/^  (?:async )?function (\w+)\(/gm)];
function definition(name) {
  const index = definitions.findIndex(match => match[1] === name);
  assert.notEqual(index, -1, `Actual production function ${name} must exist`);
  return source.slice(definitions[index].index, definitions[index + 1]?.index ?? source.length);
}

function harness(design) {
  const ids = ["name", "inputs", "revision", "state", "pc", "of", "thrust", "props"];
  const elements = Object.fromEntries(ids.map(id => [`design-context-${id}`, {textContent: ""}]));
  const state = {design, dirty: false, drafts: {}};
  const context = {state, $: id => elements[id] || null, publishShellContext() {}};
  vm.createContext(context);
  vm.runInContext(["qtyText", "displayEngineQty", "renderContextBar"].map(definition).join("\n"), context);
  return {context, state, elements, render() {context.renderContextBar(); return elements["design-context-thrust"].textContent;}};
}

function quantity(magnitude, symbol = "N") {return {magnitude, unit: {symbol}};}
function design(target, performance) {
  return {design_id: "source-design", name: "Source-backed requirement", revision: 3,
    requirements: {target_thrust: target}, workflow: {results: {performance}}};
}

test("initial HTML and actual context source consistently label a target, not achieved thrust", () => {
  assert.match(html, /id="design-context-thrust">Target thrust —<\/span>/);
  assert.match(definition("renderContextBar"), /Target thrust \$\{displayEngineQty\(req\.target_thrust, "kN"\)\}/);
  assert.doesNotMatch(definition("renderContextBar"), /Calculated thrust|Achieved thrust|workflow\.results|outputs\.thrust/);
});

test("both actual requirement editors label Target thrust and retain their existing IDs/units", () => {
  assert.match(definition("buildWorkflowCard"), /field\("Target thrust \[kN\]", \{[^}]*id: "wf-thrust"/);
  assert.match(definition("buildEngineDefinitionCard"), /field\("Target thrust \[kN\]", \{[^}]*id: "ed-thrust"/);
  assert.match(definition("buildEngineDefinitionCard"), /quantityInputValue\(req\.target_thrust, "kN"\)/);
  assert.doesNotMatch(source, /field\("Thrust \[kN\]"/);
});

test("empty active design remains explicitly a missing target", () => {
  assert.equal(harness(null).render(), "Target thrust —");
});

test("zero target remains zero with supplied unit rather than a missing value", () => {
  assert.equal(harness(design(quantity(0))).render(), "Target thrust 0.00 kN");
  assert.equal(harness(design(quantity(0, "kN"))).render(), "Target thrust 0.00 kN");
});

test("finite target retains existing display conversion and precision without source mutation", () => {
  const value = design(quantity(12345.6789));
  const before = JSON.stringify(value);
  Object.freeze(value.requirements.target_thrust.unit);
  Object.freeze(value.requirements.target_thrust);
  Object.freeze(value.requirements);
  Object.freeze(value);
  assert.equal(harness(value).render(), "Target thrust 12.35 kN");
  assert.equal(JSON.stringify(value), before);
  assert.equal(harness(design(quantity(12.3456789, "kN"))).render(), "Target thrust 12.35 kN");
});

test("supplied nonconverted units remain source text, not invented compatible units", () => {
  assert.equal(harness(design(quantity(8, "lbf"))).render(), "Target thrust 8 lbf");
});

for (const [label, target] of [
  ["undefined", undefined], ["null", null], ["empty object", {}], ["missing magnitude", {unit: {symbol: "N"}}],
  ["NaN", quantity(NaN)], ["positive infinity", quantity(Infinity)], ["negative infinity", quantity(-Infinity)],
  ["overflow text", quantity("1e999")],
]) {
  test(`missing or nonfinite ${label} target is unavailable, not an achieved number`, () => {
    assert.equal(harness(design(target)).render(), "Target thrust —");
  });
}

test("current calculated result cannot be substituted for an absent requirement target", () => {
  const calculated = {stage_id: "performance", status: "CURRENT", outputs: {thrust: quantity(21000)}};
  assert.equal(harness(design(null, calculated)).render(), "Target thrust —");
});

test("stale, failed and missing performance results do not change target identity or imply achievement", () => {
  for (const status of ["CURRENT", "STALE", "FAILED", "OUT_OF_RANGE", "NOT_CALCULATED", "NOT_RUN", undefined]) {
    const performance = status ? {stage_id: "performance", status, outputs: {thrust: quantity(42000)}} : undefined;
    const value = design(quantity(10000), performance);
    const before = JSON.stringify(value);
    const h = harness(value);
    assert.equal(h.render(), "Target thrust 10.00 kN");
    assert.equal(JSON.stringify(value), before);
    h.state.design.requirements.target_thrust = null;
    assert.equal(h.render(), "Target thrust —");
  }
});

test("rendering dirty/saved drafts does not promote an unsaved number into the target summary", () => {
  const h = harness(design(quantity(10000)));
  h.state.dirty = true;
  h.state.drafts["wf-thrust"] = "999";
  assert.equal(h.render(), "Target thrust 10.00 kN");
  assert.match(h.elements["design-context-inputs"].textContent, /Unsaved edits/);
  h.state.dirty = false;
  assert.equal(h.render(), "Target thrust 10.00 kN");
  assert.match(h.elements["design-context-inputs"].textContent, /Saved editor drafts/);
});

test("target summary source has no API, solver, persistence or input write side effect", () => {
  assert.doesNotMatch(definition("renderContextBar"), /api\(\)|runPhase|saveDesign|updateRequirements|localStorage|setFieldValue|\.value\s*=/);
});
