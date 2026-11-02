"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const source = fs.readFileSync(path.join(__dirname, "../../gui/static/app.js"), "utf8");
// Run the real shared dialog methods, without booting the application shell.
const dialogMethods = source.slice(0, source.indexOf("  NAV_ICONS:")) + "}; this.shell = COSMOS;";

function harness() {
  const listeners = new Map();
  const document = {activeElement: null, addEventListener: (key, fn) => listeners.set(key, fn),
    removeEventListener: (key) => listeners.delete(key)};
  function element(id, children = []) {
    const attrs = new Map();
    const classes = new Set();
    const el = {id, children, inert: false, tagName: "DIV", tabIndex: 0, isConnected: true,
      classList: {add: (value) => classes.add(value), remove: (value) => classes.delete(value)},
      setAttribute: (key, value) => attrs.set(key, value), getAttribute: (key) => attrs.get(key),
      getClientRects: () => [{}], focus: () => {document.activeElement = el;},
      querySelector: () => children[0], querySelectorAll: () => children,
    };
    children.forEach(child => {child.parentElement = el; child.tagName = "BUTTON";});
    return el;
  }
  const first = element("first"), last = element("last");
  const modal = element("dialog", [first, last]);
  const sibling = element("other-dialog");
  const overlayRoot = element("overlays", [modal, sibling]);
  const frame = element("frame");
  const body = element("body", [frame, overlayRoot]);
  document.body = body;
  const trigger = element("trigger");
  document.activeElement = trigger;
  const context = {document};
  vm.createContext(context);
  vm.runInContext(dialogMethods, context);
  const key = (key, shiftKey = false) => {
    const event = {key, shiftKey, prevented: false,
      preventDefault() {this.prevented = true;}, stopImmediatePropagation() {this.stopped = true;}};
    listeners.get("keydown")(event);
    return event;
  };
  return {shell: context.shell, document, modal, sibling, frame, trigger, first, last, listeners, key};
}

test("dialog gets focus and inerts background without inerting its ancestor", () => {
  const h = harness();
  h.shell.openDialog(h.modal, h.first);
  assert.equal(h.document.activeElement, h.first);
  assert.equal(h.modal.getAttribute("aria-hidden"), "false");
  assert.equal(h.frame.inert, true);
  assert.equal(h.sibling.inert, true);
  assert.equal(h.modal.parentElement.inert, false);
});

test("Tab and Shift+Tab wrap at both dialog boundaries", () => {
  const h = harness();
  h.shell.openDialog(h.modal, h.first);
  assert.equal(h.key("Tab", true).prevented, true);
  assert.equal(h.document.activeElement, h.last);
  assert.equal(h.key("Tab").prevented, true);
  assert.equal(h.document.activeElement, h.first);
});

test("Escape closes the dialog, restores focus and original inert states", () => {
  const h = harness();
  h.sibling.inert = true;
  let closed = 0;
  h.shell.openDialog(h.modal, h.first, () => {closed++;});
  const event = h.key("Escape");
  assert.equal(event.stopped, true);
  assert.equal(h.modal.getAttribute("aria-hidden"), "true");
  assert.equal(h.document.activeElement, h.trigger);
  assert.equal(h.frame.inert, false);
  assert.equal(h.sibling.inert, true);
  assert.equal(h.listeners.size, 0);
  assert.equal(closed, 1);
});

test("opening a second modal cleans up the first focus trap", () => {
  const h = harness();
  h.shell.openDialog(h.modal, h.first);
  h.shell.openDialog(h.sibling);
  assert.equal(h.modal.getAttribute("aria-hidden"), "true");
  assert.equal(h.shell.activeDialog.modal, h.sibling);
  h.shell.closeDialog(h.sibling);
  assert.equal(h.document.activeElement, h.trigger);
  assert.equal(h.frame.inert, false);
});
