"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const M = require("./model.js");
const ready = () => { const s = M.createState(); M.edit(s, "ambientPa", 0); return s; };
test("blank ambient is missing, explicit vacuum zero is valid", () => {
  const s = M.createState(); assert.equal(M.preflight(s)[0].field, "ambientPa");
  M.edit(s, "ambientPa", 0); assert.deepEqual(M.preflight(s), []);
});
test("finite and positive input guards reject NaN and negative pressure", () => {
  const s = ready(); M.edit(s, "pressurePa", NaN); assert.equal(M.preflight(s)[0].code, "InvalidParameter");
  M.edit(s, "pressurePa", -1); assert.ok(M.preflight(s).length);
});
test("mode changes never modify model or numeric inputs", () => {
  const s = ready(); const before = JSON.stringify(s.draft);
  M.MODES.forEach(mode => { M.setMode(s, mode); assert.equal(JSON.stringify(s.draft), before); });
});
test("navigation retains draft and active snapshot", () => {
  const s = ready(); M.edit(s, "pressurePa", 600000); const before = JSON.stringify(s.draft);
  ["rocket", "ngg", "simulation", "vv", "knowledge", "reports", "projects"].forEach(route => M.navigate(s, route));
  assert.equal(JSON.stringify(s.draft), before); assert.equal(s.baseSnapshotId, "demo-r1");
});
test("published example snapshots are deeply immutable", () => {
  const s = ready(); assert.throws(() => { s.snapshots[0].parametersSI.pressurePa = 1; }, TypeError);
});
test("new example revision preserves old values and does not relabel old result current", () => {
  const s = ready(); const r = M.recordFixtureResult(s, "CURRENT");
  M.edit(s, "pressurePa", 600000); M.commit(s);
  assert.equal(s.snapshots[0].parametersSI.pressurePa, 500000);
  assert.equal(M.visibleStatus(s, r), "STALE"); assert.equal(r.status, "CURRENT");
});
test("inspection of old revision does not overwrite active draft", () => {
  const s = ready(); M.edit(s, "pressurePa", 600000); M.commit(s); M.edit(s, "thrustN", 2000);
  const before = JSON.stringify(s.draft); M.inspect(s, "demo-r1");
  assert.equal(JSON.stringify(s.draft), before); assert.equal(s.baseSnapshotId, "demo-r2");
});
test("stale commit base is rejected without creating a revision", () => {
  const s = ready(); M.edit(s, "pressurePa", 600000);
  assert.throws(() => M.commit(s, "obsolete"), /RevisionConflict/); assert.equal(s.snapshots.length, 1);
});
test("missing input blocks publication", () => {
  const s = M.createState(); assert.throws(() => M.commit(s), /PreflightRejected/);
});
test("undo is reversible without scientific run", () => {
  const s = ready(); M.edit(s, "pressurePa", 600000); M.undo(s);
  assert.equal(s.draft.pressurePa, 500000); assert.equal(s.results.length, 0);
});
test("fixture result refuses unsaved or invalid inputs", () => {
  const s = ready(); M.edit(s, "pressurePa", 600000);
  assert.throws(() => M.recordFixtureResult(s, "CURRENT"), /SaveExplicitInputsFirst/);
});
test("failure remains a failure and validation is never claimed", () => {
  const s = ready(); const r = M.recordFixtureResult(s, "OUT_OF_RANGE");
  assert.equal(M.visibleStatus(s, r), "OUT_OF_RANGE"); assert.equal(r.validation, "Not claimed");
});
test("queued cancellation publishes no artifact", () => {
  const s = ready(); M.startFixtureJob(s); M.transition(s, "Cancelled"); assert.equal(s.job.published, false);
});
test("running cancellation is requested before acknowledgement", () => {
  const s = ready(); M.startFixtureJob(s); M.transition(s, "Running");
  M.transition(s, "CancelRequested"); M.transition(s, "Cancelled"); assert.equal(s.job.published, false);
});
test("QA rejection cannot publish a partially built fixture", () => {
  const s = ready(); M.startFixtureJob(s); M.transition(s, "Running"); M.transition(s, "QA"); M.transition(s, "Rejected");
  assert.throws(() => M.transition(s, "Published"), /InvalidJobTransition/); assert.equal(s.job.published, false);
});
test("scripted job sequence increases and real export is always disabled", () => {
  const s = ready(); M.startFixtureJob(s); ["Running", "QA", "Accepted", "Published"].forEach(next => M.transition(s, next));
  assert.deepEqual(s.job.events.map(e => e.seq), [1, 2, 3, 4, 5]); assert.equal(M.canExport(s), false);
});
test("unknown modes routes inputs and states reject explicitly", () => {
  const s = ready(); assert.throws(() => M.setMode(s, "Fast"), /UnknownMode/);
  assert.throws(() => M.navigate(s, "secret"), /UnknownDestination/);
  assert.throws(() => M.edit(s, "secret", 1), /UnknownParameter/);
});
