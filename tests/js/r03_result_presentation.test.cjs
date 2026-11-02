"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const source = fs.readFileSync(path.join(__dirname, "../../gui/static/propulsion-suite.js"), "utf8");
const definitions = [...source.matchAll(/^  (?:async )?function (\w+)\(/gm)];
function definition(name) {
  const index = definitions.findIndex(match => match[1] === name);
  assert.notEqual(index, -1);
  return source.slice(definitions[index].index, definitions[index + 1]?.index ?? source.length);
}

function element(tag) {
  let ownText = "";
  const node = {tag, children: [], className: "", classList: {toggle() {}},
    appendChild(child) {this.children.push(child); return child;},
    get textContent() {return ownText + this.children.map(child => child.textContent).join(" ");},
    set textContent(value) {ownText = String(value); this.children.length = 0;},
    set innerHTML(value) {assert.equal(value, "", "Source text must never enter innerHTML"); this.children.length = 0; ownText = "";},
  };
  return node;
}
function all(root, predicate) {
  return [root, ...root.children.flatMap(child => all(child, () => true))].filter(predicate);
}
function rows(root, caption) {
  const table = all(root, node => node.tag === "table").find(table => table.children[0].textContent.startsWith(caption));
  assert.ok(table, `Table ${caption} exists`);
  return all(table, node => node.tag === "tr" && node.children[0]?.scope === "row");
}
function raw(root) {
  const details = all(root, node => node.tag === "details" && node.className === "suite-source-inspection");
  return details.map(details => details.children.find(child => child.tag === "pre").textContent);
}
function harness() {
  const resultHost = element("div");
  const visualCalls = [];
  const context = {document: {createElement: element}, state: {resultGeneration: 0,
    design: {requirements: {target_thrust: {magnitude: 99999, unit: {symbol: "N"}}}}},
    $: id => id === "suite-result" ? resultHost : null, publishPresentation() {},
    appendCeaVisual(_host, payload) {visualCalls.push(payload);}, appendSubsystemVisual(_host, payload) {visualCalls.push(payload);},
  };
  vm.createContext(context);
  vm.runInContext(["qtyText", "formatScalar", "formatResult", "renderStructuredPhase", "setResult", "showStoredStageResult"].map(definition).join("\n"), context);
  vm.runInContext("this.renderResultPresentation = renderResultPresentation; this.rawResultInspection = rawResultInspection;", context);
  return {...context, context, resultHost, visualCalls};
}
const quantity = (magnitude, symbol) => ({magnitude, unit: {symbol}});
function performance(status = "CURRENT") {
  return {ok: true, stage_id: "performance", calculation_type: "performance.choked_nozzle_thrust", status,
    result_id: "actual-result", design_revision: 7, model_id: "actual-thrust-model", model_version: "1.0",
    provenance: {source: "Existing model source", reference: "actual-reference", calculation_revision: 7},
    validity: {status: "VALID", checks: ["actual-check"]}, verification: {status: "UNKNOWN"}, validation: {status: "NOT_CLAIMED"},
    inputs: {ambient_pressure: quantity(0, "Pa"), chamber_pressure: quantity(5000000, "Pa"),
      chamber_temperature: quantity(3000, "K"), gamma: {value: 1.2, unit: "1"}},
    outputs: {thrust: quantity(12345.6789012345, "N"), unknown_output: {value: 3.4, unit: "1"}},
    warnings: ["actual warning"], assumptions: ["actual assumption"]};
}

test("CURRENT performance names calculated thrust with exact source magnitude/unit and identity", () => {
  const h = harness(), dto = performance(), view = h.renderResultPresentation(dto);
  const thrust = rows(view, "Calculated outputs").find(row => row.children[0].textContent === "Calculated thrust");
  assert.deepEqual(thrust.children.map(child => child.textContent), ["Calculated thrust", "12345.6789012345", "N", "thrust"]);
  for (const text of ["actual-result", "actual-thrust-model", "Existing model source", "actual-reference", "Design revision", "7"])
    assert.ok(view.textContent.includes(text));
  assert.match(view.textContent, /CURRENT.*not experimental validation/);
});

test("zero calculated thrust and zero ambient pressure remain zero, not unavailable", () => {
  const dto = performance(); dto.outputs.thrust.magnitude = 0;
  const view = harness().renderResultPresentation(dto);
  assert.equal(rows(view, "Calculated outputs")[0].children[1].textContent, "0");
  const ambient = rows(view, "Supplied operating").find(row => row.children[0].textContent === "Ambient pressure");
  assert.equal(ambient.children[1].textContent, "0");
  assert.equal(ambient.children[2].textContent, "Pa");
});
test('backend target comparison preserves exact supplied signed difference without browser math',()=>{
  const dto=performance(),comparison={status:'AVAILABLE',result_id:dto.result_id,design_revision:dto.design_revision,quantities:{requested_thrust:quantity(10000,'N'),calculated_thrust:quantity(12345.6789012345,'N'),signed_difference:quantity(2345.6789012345,'N')},scope:'Backend signed difference; no sizing',tolerance_assessment:'NOT_DECLARED'};
  const view=harness().renderResultPresentation(dto,{targetComparison:comparison});
  const values=rows(view,'Requested versus calculated thrust');assert.equal(values[2].children[1].textContent,'2345.6789012345');assert.match(view.textContent,/NOT_DECLARED/);assert.deepEqual(JSON.parse(raw(view)[0]),dto);
});
test('comparison from another result or revision cannot become a current mismatch',()=>{
  for(const override of [{result_id:'other'},{design_revision:6}]){
    const dto=performance(),comparison={status:'AVAILABLE',result_id:dto.result_id,design_revision:dto.design_revision,...override,quantities:{signed_difference:quantity(456789,'N')}};
    const view=harness().renderResultPresentation(dto,{targetComparison:comparison});assert.match(view.textContent,/Target mismatch unavailable/);assert.ok(!view.textContent.includes('456789'));
  }
});

test("only supplied operating conditions render; missing inputs are not defaulted from current design", () => {
  const dto = performance(); delete dto.inputs.chamber_temperature;
  const view = harness().renderResultPresentation(dto);
  const inputRows = rows(view, "Supplied operating");
  assert.equal(inputRows.length, 3);
  assert.ok(!inputRows.some(row => row.children[0].textContent === "Chamber temperature"));
  assert.ok(!view.textContent.includes("99999"));
});

test("freshness, validity, verification and validation remain distinct source claims", () => {
  const dto = performance(); dto.validity.status = "UNKNOWN"; dto.verification = {};
  const view = harness().renderResultPresentation(dto);
  const metadata = all(view, node => node.tag === "dl")[0].children;
  const values = Object.fromEntries(metadata.filter((_node, index) => index % 2 === 0).map((node, index) => [node.textContent, metadata[index * 2 + 1].textContent]));
  assert.equal(values.Freshness, "CURRENT"); assert.equal(values.Validity, "UNKNOWN");
  assert.equal(values.Verification, "UNKNOWN"); assert.equal(values.Validation, "NOT_CLAIMED");
  assert.ok(!view.textContent.includes("VERIFIED") && !view.textContent.includes("VALIDATED"));
});

for (const status of ["STALE", "FAILED", "OUT_OF_RANGE", "NOT_CALCULATED", "NOT_RUN", "RUNNING", undefined]) {
  test(`${status || "missing status"} output cannot be shown as a current calculated thrust`, () => {
    const dto = performance(status); if (status === undefined) delete dto.status;
    const view = harness().renderResultPresentation(dto);
    const thrust = rows(view, "Outputs unavailable")[0];
    assert.equal(thrust.children[0].textContent, "Calculated thrust");
    assert.match(thrust.children[1].textContent, /Unavailable.*not a current answer/);
    assert.match(view.textContent, /Stored operating conditions/);
    assert.deepEqual(JSON.parse(raw(view)[0]), dto, "Original stored output remains inspectable, not promoted");
  });
}

for (const [label, value] of [["null", null], ["missing", undefined], ["scalar lacking unit", 123],
  ["missing unit", {magnitude: 12}], ["NaN", quantity(NaN, "N")], ["Infinity", quantity(Infinity, "N")]]) {
  test(`${label} thrust is unavailable and cannot fall back to target`, () => {
    const dto = performance(); dto.outputs.thrust = value;
    const view = harness().renderResultPresentation(dto);
    const thrust = rows(view, "Calculated outputs")[0];
    assert.match(thrust.children[1].textContent, /Unavailable/);
    assert.ok(!thrust.textContent.includes("99999"));
  });
}

test("failed ok flag defeats CURRENT status and retains actionable errors", () => {
  const dto = performance(); dto.ok = false; dto.errors = [{code: "ActualFailure", message: "actual cause", action: "actual recovery"}];
  const view = harness().renderResultPresentation(dto);
  assert.match(rows(view, "Outputs unavailable")[0].children[1].textContent, /Unavailable/);
  assert.match(view.textContent, /ActualFailure/); assert.match(view.textContent, /actual cause/); assert.match(view.textContent, /actual recovery/);
});

test("nested canonical/value quantities retain exact supplied units and raw keys", () => {
  const dto = performance(); dto.outputs.nested = {station: {pressure: quantity(10.123456789, "Pa"), speed: {value: 2.345678901, unit: "m/s"}}};
  const view = harness().renderResultPresentation(dto);
  const nested = rows(view, "Calculated outputs").find(row => row.children[0].textContent === "nested.station.pressure");
  assert.deepEqual(nested.children.map(child => child.textContent), ["nested.station.pressure", "10.123456789", "Pa", "nested.station.pressure"]);
  assert.deepEqual(JSON.parse(raw(view)[0]), dto);
});

test("unknown stage thrust remains raw field name rather than a fabricated performance claim", () => {
  const dto = performance(); dto.stage_id = "other-model"; dto.calculation_type = "other_model";
  const view = harness().renderResultPresentation(dto);
  assert.ok(!view.textContent.includes("Calculated thrust"));
  assert.equal(rows(view, "Calculated outputs")[0].children[0].textContent, "thrust");
});

test("prototype-like unknown source keys remain literal fields, not inherited label methods", () => {
  const dto = performance();
  dto.outputs = JSON.parse('{"constructor":{"value":1,"unit":"1"},"toString":{"value":2,"unit":"1"},"__proto__":{"value":3,"unit":"1"}}');
  const view = harness().renderResultPresentation(dto);
  const labels = rows(view, "Calculated outputs").map(row => row.children[0].textContent);
  for (const name of ["constructor", "toString", "__proto__"]) assert.ok(labels.includes(name));
  assert.deepEqual(JSON.parse(raw(view)[0]), dto);
});

test("source HTML is plain DOM text in metadata, tables, notes, errors and raw inspection", () => {
  const unsafe = '<img src=x onerror="throw 1"><script>danger()</script>';
  const dto = performance(); dto.model_id = unsafe; dto.provenance.source = unsafe;
  dto.outputs[unsafe] = {value: 1, unit: unsafe}; dto.warnings = [unsafe]; dto.assumptions = [unsafe];
  const view = harness().renderResultPresentation(dto);
  assert.ok(view.textContent.includes(unsafe));
  assert.ok(!all(view, node => ["img", "script"].includes(node.tag)).length);
  assert.deepEqual(JSON.parse(raw(view)[0]), dto);
});

test("bounded rows/depth/array summaries disclose limits and preserve the complete received DTO", () => {
  const dto = performance(); dto.outputs.array = Array.from({length: 50}, (_, index) => quantity(index, "N"));
  dto.outputs.deep = {a: {b: {c: {d: quantity(9, "Pa")}}}};
  for (let index = 0; index < 100; index++) dto.outputs[`unknown_${index}`] = index;
  const view = harness().renderResultPresentation(dto);
  assert.ok(rows(view, "Calculated outputs").length <= 64);
  assert.match(view.textContent, /Summary limited to 64 rows/);
  assert.deepEqual(JSON.parse(raw(view)[0]), dto);
});

test("nonfinite raw values use explicit noncanonical placeholders rather than silent JSON null", () => {
  const dto = performance(); dto.outputs.thrust.magnitude = Infinity;
  const view = harness().renderResultPresentation(dto);
  assert.match(view.textContent, /nonfinite placeholders, not canonical finite data/);
  assert.equal(JSON.parse(raw(view)[0]).outputs.thrust.magnitude, "[nonfinite: Infinity]");
});

test("real standalone setResult uses the additive summary and preserves input/result DTOs", () => {
  const h = harness(), dto = performance(), before = JSON.stringify(dto), inputBefore = JSON.stringify(h.state.design);
  h.context.setResult(dto);
  assert.match(h.resultHost.textContent, /Calculated thrust/);
  assert.deepEqual(JSON.parse(raw(h.resultHost)[0]), dto);
  assert.equal(JSON.stringify(dto), before); assert.equal(JSON.stringify(h.state.design), inputBefore);
  assert.equal(h.state.resultGeneration, 1);
});

test("real phase stage performance summary keeps stage key context and entire phase DTO", () => {
  const dto = performance(); delete dto.stage_id; delete dto.calculation_type;
  const payload = {ok: true, execution_ok: true, workflow_complete: false, engineering_readiness: "PRELIMINARY",
    validation_level: "NOT_CLAIMED", stages: {performance: dto}, extra_source_metadata: {literal: "retained"}};
  const view = harness().renderStructuredPhase(payload);
  assert.match(view.textContent, /Calculated thrust/); assert.match(view.textContent, /workflow_complete=false/);
  assert.deepEqual(JSON.parse(raw(view).at(-1)), payload);
});

test("failed phase stage preserves urgent diagnostics once without a duplicate expanded summary", () => {
  const dto = performance("FAILED"); dto.ok = false;
  dto.errors = [{code: "ActualFailure", message: "actual cause", action: "actual recovery"}];
  const view = harness().renderStructuredPhase({ok: false, stages: {performance: dto}});
  const urgent = all(view, node => node.tag === "pre" && !node.className);
  const sourcePre = raw(view);
  assert.equal(urgent.filter(node => node.textContent.startsWith("CALCULATION FAILED")).length, 1);
  assert.ok(!all(view, node => node.className === "suite-result-diagnostics").length);
  assert.equal(sourcePre.length, 2);
  assert.match(view.textContent, /actual recovery/);
});

test("existing CEA and subsystem visuals retain full array/source data in additive inspection", () => {
  const h = harness();
  const dto = {stage_id: "nozzle", status: "CURRENT", outputs: {stations: [{x_m: 0, radius_m: 0.02}]}};
  h.context.setResult(dto);
  assert.equal(h.visualCalls[0], dto);
  assert.deepEqual(JSON.parse(raw(h.resultHost)[0]), dto);
  const cea = {stage_id: "thermochemistry", status: "CURRENT", outputs: {rocket_stations: {chamber: {pressure_pa: 1}}, mole_fractions: {H2O: 0.5}}};
  h.context.setResult(cea);
  assert.equal(h.visualCalls[1], cea); assert.deepEqual(JSON.parse(raw(h.resultHost)[0]), cea);
});

test("legacy string formatter and receipts remain stable without scientific side effects", () => {
  const h = harness();
  assert.equal(h.context.formatResult({ok: true, status: "RUNNING", message: "Calculating…"}), "RUNNING\nCalculating…");
  h.context.setResult({ok: true, status: "SAVED", message: "Saved"});
  assert.equal(h.resultHost.textContent, "SAVED\nSaved");
  const presentationSource = definition("formatResult").slice(definition("formatResult").indexOf("const rawResultInspection"));
  assert.doesNotMatch(presentationSource, /api\(\)|runPhase|updateRequirements|target_thrust|localStorage|innerHTML|toFixed|\/\s*1000/);
});

for (const status of ["NOT_CALCULATED", "NOT_IMPLEMENTED", "STALE", "FAILED", "OUT_OF_RANGE", "CURRENT"]) {
  test(`actual stored-result loader retains ${status} source DTO and separate denied envelope`, async () => {
    const h = harness(), dto = performance(status);
    delete dto.ok;
    dto.warnings = ["only actual source warning"];
    const before = JSON.stringify(dto);
    Object.freeze(dto.warnings); Object.freeze(dto);
    h.state.design.design_id = "owned-design"; h.state.activeKind = "stage"; h.state.activeId = "performance";
    h.context.api = () => ({getStageResult: async () => ({ok: true, displayable_as_current: false, result: dto})});
    await h.context.showStoredStageResult("performance");
    assert.equal(JSON.stringify(dto), before);
    assert.equal(JSON.stringify(h.state.presentationResult), before);
    assert.equal(h.state.presentationResult.status, status);
    assert.equal(h.state.presentationDisplayableAsCurrent, false);
    assert.deepEqual(JSON.parse(raw(h.resultHost)[0]), dto);
    assert.match(rows(h.resultHost, "Outputs unavailable")[0].children[1].textContent, /Unavailable.*API envelope/);
    assert.match(h.resultHost.textContent, /Display eligibility/);
  });
}

test("actual stored loader requires an affirmative envelope, while direct phase behavior stays compatible", async () => {
  const h = harness(), dto = performance();
  h.state.design.design_id = "owned-design"; h.state.activeKind = "stage"; h.state.activeId = "performance";
  h.context.api = () => ({getStageResult: async () => ({ok: true, result: dto})});
  await h.context.showStoredStageResult("performance");
  assert.equal(h.state.presentationDisplayableAsCurrent, false);
  assert.match(rows(h.resultHost, "Outputs unavailable")[0].children[1].textContent, /Unavailable/);
  h.context.api = () => ({getStageResult: async () => ({ok: true, displayable_as_current: true, result: dto})});
  await h.context.showStoredStageResult("performance");
  assert.equal(rows(h.resultHost, "Calculated outputs")[0].children[1].textContent, "12345.6789012345");
  h.context.setResult(dto);
  assert.equal(h.state.presentationDisplayableAsCurrent, undefined);
  assert.equal(rows(h.resultHost, "Calculated outputs")[0].children[1].textContent, "12345.6789012345");
});

test("denied envelope prevents source-CURRENT CEA and subsystem active visuals without source relabeling", () => {
  const h = harness();
  for (const dto of [
    {stage_id: "nozzle", status: "CURRENT", outputs: {stations: [{x_m: 0, radius_m: 0.02}]}},
    {stage_id: "thermochemistry", status: "CURRENT", outputs: {rocket_stations: {chamber: {pressure_pa: 1}}}},
  ]) {
    h.context.setResult(dto, {displayableAsCurrent: false});
    assert.equal(h.visualCalls.length, 0);
    assert.equal(h.state.presentationResult.status, "CURRENT");
    assert.deepEqual(JSON.parse(raw(h.resultHost)[0]), dto);
  }
});

test("raw scrollable source region is keyboard-focusable and named for result and phase inspection", () => {
  const h = harness();
  const phase = {stages: {performance: performance()}};
  const views = [h.renderResultPresentation(performance()), h.renderStructuredPhase(phase)];
  for (const view of views) {
    const regions = all(view, node => node.tag === "details" && node.className === "suite-source-inspection")
      .map(details => details.children.find(child => child.tag === "pre"));
    assert.ok(regions.length);
    for (const region of regions) {
      assert.equal(region.tabIndex, 0); assert.equal(region.role, "region");
      assert.match(region.ariaLabel, /Raw received.*scrollable source content/);
    }
  }
});

test("quantity tables have named focusable bounded scroll regions and unbroken exact numeric cells", () => {
  const dto = performance(), view = harness().renderResultPresentation(dto);
  const scrolls = all(view, node => node.className === "suite-table-scroll");
  assert.equal(scrolls.length, 2);
  for (const scroll of scrolls) {
    assert.equal(scroll.tabIndex, 0); assert.equal(scroll.role, "region");
    assert.match(scroll.ariaLabel, /quantity table; scroll horizontally when needed/);
    assert.ok(scroll.children.some(node => node.tag === "table"));
  }
  const numeric = rows(view, "Calculated outputs")[0].children[1];
  assert.equal(numeric.className, "suite-quantity-value");
  assert.equal(numeric.textContent, "12345.6789012345");
  assert.deepEqual(JSON.parse(raw(view)[0]), dto);
  const css = fs.readFileSync(path.join(__dirname, "../../gui/static/propulsion-suite.css"), "utf8");
  assert.match(css, /\.suite-quantity-table \{[^}]*min-width: 42rem/);
  assert.match(css, /\.suite-quantity-value[^}]*td:nth-child\(3\)[^{]*\{[^}]*white-space: nowrap;[^}]*overflow-wrap: normal/);
  assert.match(css, /suite-table-scroll:focus-visible/);
});
