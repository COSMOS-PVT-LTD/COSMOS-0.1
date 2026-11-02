/* Isolated P01 wireframe controller: only navigation.json is fetched. */
"use strict";
(async function () {
  const M = window.CosmosP01Model;
  const $ = id => document.getElementById(id);
  let state = M.createState();
  const config = await fetch("../navigation.json").then(response => {
    if (!response.ok) throw new Error("PrototypeNavigationUnavailable");
    return response.json();
  });
  const layoutKey = "cosmos-p01-layout-v1";
  const defaults = {inspector: true, dock: true, width: 260, height: 130};
  let layout = {...defaults};
  try {
    const saved = JSON.parse(localStorage.getItem(layoutKey) || "null");
    if (saved) layout = {inspector: saved.inspector !== false, dock: saved.dock !== false,
      width: [260, 320].includes(saved.width) ? saved.width : 260,
      height: [130, 200].includes(saved.height) ? saved.height : 130};
  } catch { /* UI preferences unavailable: scientific state is unaffected. */ }
  let error = null;
  let showPreflight = false;
  let priorFocus = null;
  const escape = value => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const button = (id, text, disabled = false) => `<button id="${id}" ${disabled ? "disabled" : ""}>${text}</button>`;
  const announce = text => { $("announcement").textContent = text; };
  const act = (id, callback) => { const el = $(id); if (el) el.onclick = () => {
    try { error = null; callback(); } catch (e) { error = {code: e.message, recovery: "Review the preflight or current revision. This is a synthetic scenario."}; }
    renderContext(); renderInspector(); renderActivity();
    if (document.activeElement === document.body) {
      const replacement = $(id);
      (replacement && !replacement.disabled ? replacement : $("editor")).focus({preventScroll:true});
    }
  }; };

  function applyLayout() {
    const workspace = document.querySelector(".workspace");
    workspace.classList.toggle("inspector-hidden", !layout.inspector);
    workspace.classList.toggle("dock-collapsed", !layout.dock);
    $("inspector").hidden = !layout.inspector; $("activity").hidden = !layout.dock;
    $("toggle-inspector").textContent = layout.inspector ? "Hide inspector" : "Show inspector";
    $("toggle-inspector").setAttribute("aria-expanded", String(layout.inspector));
    $("toggle-dock").textContent = layout.dock ? "Collapse diagnostics" : "Expand diagnostics";
    $("toggle-dock").setAttribute("aria-expanded", String(layout.dock));
    $("inspector-width").value = String(layout.width); $("dock-height").value = String(layout.height);
    document.documentElement.style.setProperty("--inspector", `${layout.width}px`);
    document.documentElement.style.setProperty("--dock", `${layout.height}px`);
    try { localStorage.setItem(layoutKey, JSON.stringify(layout)); } catch { announce("Layout remains available for this session only."); }
  }
  function go(route) {
    M.navigate(state, route); error = null; render();
    $("editor").focus({preventScroll:true}); $("editor").scrollTop = 0;
    announce(`${config.primary.find(item => item.id === route).label}. Draft retained.`);
  }
  function renderContext() {
    document.body.dataset.mode = state.mode;
    $("mode").value = state.mode;
    $("project-label").textContent = state.opened ? "Demo mission / Methalox example" : "No project open";
    $("revision-label").textContent = `Active ${state.baseSnapshotId} · inspect ${state.inspectedSnapshotId}`;
    $("draft-label").textContent = M.dirty(state) ? "DRAFT · unsaved example" : "SAVED EXAMPLE · not production";
  }
  function renderInspector() {
    const snap = M.snapshot(state, state.inspectedSnapshotId);
    $("inspector-content").innerHTML = `<dl><dt>Authoritative context (proposed)</dt><dd>Project ID → design ID → snapshot ID. These IDs are synthetic.</dd><dt>Inspected input</dt><dd>${escape(snap.id)} · read-only example</dd><dt>Chamber pressure</dt><dd>${snap.parametersSI.pressurePa} Pa</dd><dt>Ambient pressure</dt><dd>${snap.parametersSI.ambientPa} Pa</dd><dt>Method</dt><dd>${escape(snap.parametersSI.model)} · not executed</dd><dt>Physical validation</dt><dd>NOT CLAIMED</dd><dt>Geometry / solver backend</dt><dd>Unavailable · planned</dd></dl><p class="note warning">Inspection never replaces the active draft. Real immutable revision storage is a P06 dependency.</p><a href="../../P00_2026-10-08/P00_AUDIT_REPORT.md">Source, assumptions & capability limits</a><details class="expert-details"><summary>Example SI snapshot</summary><pre>${escape(JSON.stringify(snap, null, 2))}</pre></details>`;
  }
  function renderActivity() {
    const latest = state.results.at(-1);
    $("activity").innerHTML = `<p>Execution: ${latest ? escape(latest.execution) : "Not run"} · Numerical termination: ${latest ? escape(latest.termination) : "Not available"}</p><p>Physical checks: not executed · Verification: not assessed · Experimental validation: not claimed</p><p>Geometry scenario: ${escape(state.job.state)} · events ${state.job.events.length} · real artifact: none</p>${error ? `<p class="error" role="alert">${escape(error.code)} — ${escape(error.recovery)}</p>` : ""}${state.job.events.map(event => `<p>Scripted event ${event.seq}: ${escape(event.state)} · snapshot ${escape(state.job.snapshotId)}</p>`).join("")}`;
  }
  function revisionRows() {
    return state.snapshots.map(snap => `<tr><td>${escape(snap.id)}</td><td>${snap.parametersSI.pressurePa} Pa</td><td>Read-only fixture</td><td><button data-inspect="${snap.id}">Inspect ${snap.id}</button></td></tr>`).join("");
  }
  function header(title, maturity, description) {
    return `<p class="eyebrow">${maturity} · P01 prototype</p><h1>${title}</h1><p class="lead">${description}</p>`;
  }
  function projects() {
    return header("Projects & Mission", "PROPOSED · P04", "One persistent context across every engineering task.") +
      `<p class="note">This example is held in memory. Production currently has a design store and a browser project preference, not this project/revision service.</p><h2>Demo mission · methalox fixture</h2><p>Requirements → physics sizing → input snapshot → geometry QA → study → V&V → report.</p><div class="actions">${button("open-project", "Open example project")}${button("to-history", "Inspect example revisions")}</div><p class="guided-help">Start with requirements. The prototype keeps your draft while you switch workbenches. It never runs scientific software.</p><div class="section"><h2>Revision overview</h2><div class="table-wrap"><table><caption>In-memory example history</caption><thead><tr><th>Snapshot</th><th>Pressure [Pa]</th><th>State</th><th>Action</th></tr></thead><tbody>${revisionRows()}</tbody></table></div></div>`;
  }
  const fields = [["pressurePa","Chamber pressure","Pa"],["thrustN","Target thrust","N"],["mixtureRatio","O/F mass ratio","1"],["expansionRatio","Expansion ratio Ae/At","1"],["ambientPa","Ambient pressure","Pa"],["throatAreaM2","Throat area","m²"],["fuelTemperatureK","Fuel inlet temperature","K"],["oxidizerTemperatureK","Oxidizer inlet temperature","K"]];
  function rocket() {
    if (!state.opened) return header("Rocket Engine", "ACTIVE / PARTIAL", "Open a project before editing.") + button("open-project", "Open example project");
    const latest = state.results.at(-1);
    return header("Rocket Engine · input preflight", "CURRENT CAPABILITY · PARTIAL SCIENTIFIC MODELS", "Define → Calculate → Size subsystems → Review & export. All 17 legacy stages remain accessible in production.") +
      `<p class="guided-help">Enter every required value, including ambient pressure. Zero Pa is an explicit vacuum condition; a blank is missing data.</p><p>Pair: LOX / LCH4 · Method: NASA CEA 3.3.4 · SI internal and displayed</p><div class="fields">${fields.map(([key,label,unit]) => `<label for="${key}">${label} [${unit}]<input id="${key}" data-parameter="${key}" type="number" step="any" value="${state.draft[key] ?? ""}" aria-describedby="input-help"></label>`).join("")}</div><p id="input-help" class="lead">Basic required/finite-value checks only. Model applicability remains the Physics service's responsibility.</p><div class="actions">${button("preflight", "Check required inputs")}${button("undo", "Undo last edit", !state.undo.length)}${button("commit", "Save new example revision")}${button("native-run", "Run native solver (unavailable)", true)}</div><div id="preflight-output" aria-live="polite"></div><p class="note warning">Cycle power balance is not implemented. Preliminary thermochemistry does not qualify injector, cooling, geometry or hardware.</p><section class="section"><h2>Result inspection · scripted example</h2><div class="actions">${button("fixture-current", "Show completed fixture")}${button("fixture-failed", "Show failed fixture")}${button("fixture-range", "Show range rejection")}</div>${latest ? `<p class="badge">${escape(M.visibleStatus(state, latest))} · ${escape(latest.snapshotId)}</p><div class="status-grid"><p><strong>Execution</strong>${escape(latest.execution)}</p><p><strong>Numerical termination</strong>${escape(latest.termination)}</p><p><strong>Physical checks</strong>Not executed</p><p><strong>Verification</strong>Not assessed</p><p><strong>Experimental validation</strong>Not claimed</p><p><strong>Source</strong>Scripted P01 state, no computed values</p></div>${button("inspect-result", "Inspect this result's input snapshot")}` : "<p>No result fixture selected. Nothing has been calculated.</p>"}<p class="guided-help">Completed execution and current revision are not verification or physical validation.</p></section>`;
  }
  function geometry() {
    return header("Native Geometry", "PLANNED · P06–P08", "Immutable input → representation → build → QA → export/reimport.") +
      `<p class="note warning">No kernel is connected. There is no real geometry, viewer or export. Use the scripted controls only to review failure and cancellation behavior.</p><p>Source example: ${escape(state.baseSnapshotId)}. Backend: unavailable. Representation and source/export tolerances must be explicit in the production contract.</p><div class="actions">${button("real-build", "Build real geometry (unavailable)", true)}${button("real-export", "Export CAD (unavailable)", true)}</div><section class="section"><h2>Scripted job walkthrough</h2><p>State: <strong>${escape(state.job.state)}</strong>. No published real artifact.</p><div class="actions">${button("job-start","Start scripted job")}${button("job-run","Advance to running",state.job.state!=="Queued")}${button("job-qa","Show QA warning",state.job.state!=="Running")}${button("job-reject","Reject QA fixture",state.job.state!=="QA")}${button("job-cancel","Request cancellation",!["Queued","Running"].includes(state.job.state))}${button("job-ack","Acknowledge cancellation",state.job.state!=="CancelRequested")}</div>${state.job.state==="QA" ? "<p class='note warning'>Scripted QA warning: thin-wall topology is not accepted. Recovery: inspect source parameters; create a new revision; rebuild. Do not publish or hand off to simulation.</p>" : ""}<div class="section"><h2>Representation disclosure</h2><p>Analytic B-rep · implicit field · tessellated surface · faceted B-rep. A mesh is not automatically editable parametric STEP.</p></div></section>`;
  }
  function simulation() {
    return header("Simulation", "PLANNED · P09", "Accepted artifact → named selections → mesh → run snapshot → monitor → results.") +
      `<p class="note warning">Study backend unavailable. No mesh or result field exists in this prototype or the current operational workbench.</p><ol><li>Require independently accepted geometry, units, frame and hash.</li><li>Inspect material regions and selection-remap confidence.</li><li>Declare physical model, boundary conditions and numerical settings.</li><li>Review execution, termination, conservation and admissibility separately.</li></ol><div class="actions">${button("to-geometry","Inspect geometry prerequisite")}${button("study-run","Run study (unavailable)",true)}</div><section class="section"><h2>Monitor contract</h2><p>Execution / termination / convergence / conservation / physical admissibility / solution verification / experimental validation.</p><p>No synthetic residual or field plot is shown as a solution.</p></section>`;
  }
  function vv() {
    return header("Comparison & V&V", "PLANNED · P10", "Compare compatible, traceable data before claiming agreement.") +
      `<p class="note warning">No independent dataset loaded. Comparison and validation are unavailable.</p><ol><li>Match variables, units, frames, geometry and mesh revisions.</li><li>Record independent reference provenance and uncertainty.</li><li>Set acceptance tolerance for intended engineering use.</li><li>Separate code/solution verification from experimental validation.</li></ol><div class="actions">${button("compare","Compare datasets (unavailable)",true)}${button("to-knowledge","Inspect missing source evidence")}</div>`;
  }
  function knowledge() {
    return header("Maharshi Bharadwaj Knowledge", "ACTIVE · PROPOSED P11 PRESENTATION", "Inspect source evidence without inventing a claim.") +
      `<p class="note">Prototype has no ingested source or provider connection. The real Knowledge workspace supports governed ingestion and retrieval.</p><label for="knowledge-query">Source or applicability question<input id="knowledge-query" placeholder="Evidence for the selected cooling model"></label><div class="actions">${button("knowledge-search","Check example evidence")}${button("knowledge-upload","Upload to production (unavailable)",true)}</div><div id="knowledge-result" aria-live="polite"></div><p class="guided-help">Sources need provenance and review states. An assistant reply cannot certify a calculated design.</p>`;
  }
  function reports() {
    return header("Reports, History & Governance", "PROPOSED / PARTIAL · P04/P11", "Inspect exact inputs and retained evidence; never overwrite history.") +
      `<p class="note">Current software has design export/change logs. Complete immutable run/artifact history shown here is a proposed contract, not current persistence.</p><div class="table-wrap"><table><caption>Synthetic snapshots; inspection is read-only</caption><thead><tr><th>Snapshot</th><th>Chamber pressure [Pa]</th><th>Publication</th><th>Inspect</th></tr></thead><tbody>${revisionRows()}</tbody></table></div><h2 class="section">Retained result fixtures</h2>${state.results.length ? state.results.map(result => `<p>${escape(result.id)} · input ${escape(result.snapshotId)} · ${escape(M.visibleStatus(state,result))} · validation NOT CLAIMED</p>`).join("") : "<p>No scripted results recorded.</p>"}<div class="actions">${button("report-export","Publish engineering report (unavailable)",true)}</div>`;
  }
  function renderPreflight() {
    const host = $("preflight-output"); if (!host || !showPreflight) return;
    const issues = M.preflight(state);
    host.innerHTML = issues.length ? `<h2>Required input recovery</h2><ul class="preflight-list">${issues.map(issue => `<li><button data-error-field="${issue.field}">${escape(issue.code)}: ${escape(issue.cause)} ${escape(issue.recovery)}</button></li>`).join("")}</ul>` : "<p class='note'>Basic input preflight passed. Native model checks have not run.</p>";
    fields.forEach(([key]) => $(key)?.setAttribute("aria-invalid", String(issues.some(issue => issue.field===key))));
    host.querySelectorAll("[data-error-field]").forEach(el => el.onclick = () => $(el.dataset.errorField)?.focus());
  }
  function render() {
    $("destinations").innerHTML = config.primary.map(item => `<button data-route="${item.id}" ${state.route===item.id ? 'aria-current="page"' : ""}>${escape(item.label)}<small>${escape(item.maturity)}</small></button>`).join("");
    $("destinations").querySelectorAll("button").forEach(el => el.onclick = () => go(el.dataset.route));
    $("editor").innerHTML = ({projects,rocket,ngg:geometry,simulation,vv,knowledge,reports})[state.route]();
    $("editor").querySelectorAll("[data-inspect]").forEach(el => el.onclick = () => {
      M.inspect(state,el.dataset.inspect); layout.inspector=true; applyLayout(); renderContext(); renderInspector();
      announce(`Inspecting ${el.dataset.inspect}. Active draft preserved.`);
    });
    $("editor").querySelectorAll("[data-parameter]").forEach(el => el.oninput = () => {
      M.edit(state,el.dataset.parameter,el.value.trim()==="" ? null : Number(el.value));
      renderContext(); renderActivity(); renderPreflight(); if ($("undo")) $("undo").disabled=false;
      const status = $("editor").querySelector(".section > .badge");
      if (status && state.results.length) {
        const latest = state.results.at(-1);
        status.textContent = `${M.visibleStatus(state, latest)} · ${latest.snapshotId}`;
      }
    });
    act("open-project",()=>{state.opened=true; go("rocket");});
    act("to-history",()=>go("reports")); act("to-geometry",()=>go("ngg")); act("to-knowledge",()=>go("knowledge"));
    act("preflight",()=>{showPreflight=true; renderPreflight(); announce(`${M.preflight(state).length} required input issues.`);});
    act("undo",()=>{M.undo(state); render(); announce("Last draft edit undone.");});
    act("commit",()=>{M.commit(state); render(); announce(`Saved ${state.baseSnapshotId} in memory only.`);});
    [["fixture-current","CURRENT"],["fixture-failed","FAILED"],["fixture-range","OUT_OF_RANGE"]].forEach(([id,outcome])=>act(id,()=>{M.recordFixtureResult(state,outcome);render();announce(`${outcome} scripted result. No calculation executed.`);}));
    act("inspect-result",()=>{M.inspect(state,state.results.at(-1).snapshotId);layout.inspector=true;applyLayout();announce("Result input snapshot opened in inspector.");});
    act("job-start",()=>{M.startFixtureJob(state);render();announce("Scripted job queued, not a real geometry build.");});
    [["job-run","Running"],["job-qa","QA"],["job-reject","Rejected"],["job-ack","Cancelled"]].forEach(([id,next])=>act(id,()=>{M.transition(state,next);render();announce(`${next} scripted event.`);}));
    act("job-cancel",()=>{M.transition(state,state.job.state==="Queued" ? "Cancelled" : "CancelRequested");render();announce("Cancellation scenario recorded; no real artifact published.");});
    act("knowledge-search",()=>{$("knowledge-result").innerHTML="<p class='note warning'>INSUFFICIENT_EVIDENCE — no approved source is loaded in this example. Recovery: import and qualify a source in the production Knowledge workspace.</p>";announce("Insufficient evidence. No citation invented.");});
    renderContext(); renderInspector(); renderActivity(); renderPreflight();
  }
  $("legacy-catalog").innerHTML=config.compatibility_catalog.map(item=>`<p><strong>${escape(item.id)}</strong> · ${escape(item.maturity)}<code>${escape(item.route)}</code></p>`).join("");
  $("mode").onchange=()=>{const focusId=document.activeElement.id; M.setMode(state,$("mode").value);render();$(focusId)?.focus();announce(`${state.mode} presentation. Numeric parameters and model unchanged.`);};
  $("toggle-inspector").onclick=()=>{layout.inspector=!layout.inspector;applyLayout();};
  $("toggle-dock").onclick=()=>{layout.dock=!layout.dock;applyLayout();};
  $("inspector-width").onchange=()=>{layout.width=Number($("inspector-width").value);applyLayout();};
  $("dock-height").onchange=()=>{layout.height=Number($("dock-height").value);applyLayout();};
  $("reset-layout").onclick=()=>{layout={...defaults};applyLayout();announce("Default layout restored. Scientific draft unchanged.");};
  function commandList() {
    const query=$("command-search").value.toLowerCase();
    $("command-list").innerHTML=config.primary.filter(item=>item.label.toLowerCase().includes(query)).map(item=>`<button data-command="${item.id}">${escape(item.label)} · ${escape(item.maturity)}</button>`).join("");
    $("command-list").querySelectorAll("button").forEach(el=>el.onclick=()=>{$("command-dialog").close();go(el.dataset.command);});
  }
  function openCommands() { priorFocus=document.activeElement; $("command-search").value="";commandList();$("command-dialog").showModal();$("command-search").focus(); }
  $("command-open").onclick=openCommands; $("command-search").oninput=commandList;
  $("command-close").onclick=()=>$("command-dialog").close();
  $("command-dialog").addEventListener("close",()=>{(priorFocus?.isConnected && priorFocus!==document.body ? priorFocus : $("command-open")).focus();});
  document.addEventListener("keydown",event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="k"){event.preventDefault();if(!$("command-dialog").open&&!$("reset-dialog").open)openCommands();}});
  $("reset").onclick=()=>{$("reset-dialog").showModal();$("reset-cancel").focus();};
  $("reset-cancel").onclick=()=>$("reset-dialog").close();
  $("reset-confirm").onclick=()=>{state=M.createState();error=null;showPreflight=false;$("reset-dialog").close();render();announce("Synthetic example reset. Production data untouched.");};
  $("reset-dialog").addEventListener("close",()=>$("reset").focus());
  [$("command-dialog"),$("reset-dialog")].forEach(dialog=>dialog.addEventListener("keydown",event=>{
    if (event.key!=="Tab") return;
    const focusable=[...dialog.querySelectorAll("button,input,select,a[href],[tabindex]:not([tabindex='-1'])")]
      .filter(el=>!el.disabled&&el.getClientRects().length);
    const first=focusable[0],last=focusable.at(-1);
    if (!first) { event.preventDefault(); return; }
    if (event.shiftKey&&document.activeElement===first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey&&document.activeElement===last) { event.preventDefault(); first.focus(); }
  }));
  applyLayout();render();
})().catch(error=>{document.getElementById("editor").textContent=`Prototype failed to load: ${error.message}. Serve the evidence directory using the documented local command.`;});
