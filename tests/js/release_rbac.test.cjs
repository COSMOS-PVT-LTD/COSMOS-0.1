"use strict";
const test = require("node:test"), assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path"), vm = require("node:vm");
const app = fs.readFileSync(path.join(__dirname, "../../gui/static/app.js"), "utf8");
const rbac = fs.readFileSync(path.join(__dirname, "../../gui/static/rbac.js"), "utf8");
for (const order of ["rbac-first", "app-first"]) test("actual permissions initialize safely: " + order, () => {
  const window = {}, context = vm.createContext({window});
  for (const source of order === "rbac-first" ? [rbac, app] : [app, rbac]) vm.runInContext(source, context);
  assert.equal(window.CosmosInstallRBAC, undefined);
  assert.equal(window.COSMOS.canAdmin({role: "ADMIN"}), true);
  for (const role of ["ENGINEER", "REVIEWER", "APPROVER", "VIEWER", "", "NOT_A_ROLE"]) assert.equal(window.COSMOS.canAdmin({role}), false);
  assert.equal(window.COSMOS.permissions.canKnowledgeChat({role: "VIEWER"}), true);
  assert.equal(window.COSMOS.permissions.canKnowledgeChat({role: "NOT_A_ROLE"}), false);
  assert.equal(window.COSMOS.canAudit({role: "ENGINEER"}), false);
});
