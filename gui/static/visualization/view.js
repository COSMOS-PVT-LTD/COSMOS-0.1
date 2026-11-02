/* Presentation only: all equations, source state and validation stay in services. */
const $ = id => document.getElementById(id);
const chart = new window.ScientificChart($("viz-chart"));
const exports = new window.CosmosPlotExports.ExportChooser($("viz-export-dialog"), $("viz-export-files"), $("viz-export-source"));
let payload = null, selected = null, page = 0, requestSequence = 0, activeSourcePath = null;
const size = 50;
window.COSMOS.initShell({activeNav: "workbenches"});
const status = (message, error = false) => { $("viz-status").textContent = message; $("viz-status").dataset.error = String(error); };
const text = value => typeof value === "object" ? JSON.stringify(value) : String(value ?? "not available");
async function read(path) {
  const response = await fetch(path, {credentials: "same-origin", cache: "no-store"});
  const value = await response.json();
  if (!response.ok) throw new Error(text(value.error?.message ?? value.error));
  return value;
}
function disableExports(disabled) { ["viz-svg", "viz-csv", "viz-json"].forEach(id => $(id).disabled = disabled); }
function clear() { exports.clear(); selected = null; disableExports(true); $("viz-title").textContent = "No current supported result"; $("viz-lineage").replaceChildren(); $("viz-data").replaceChildren(); $("viz-notes").replaceChildren(); $("viz-render-info").textContent = ""; $("viz-assumptions").textContent = ""; chart.dispose(); }
function sourceTable() {
  $("viz-data").replaceChildren();
  const rows = selected?.rows ?? [];
  const keys = [...new Set(rows.flatMap(row => Object.keys(row)))];
  const table = document.createElement("table"), caption = document.createElement("caption");
  caption.textContent = "Exact source rows; column unit suffixes are SI. No display decimation."; table.append(caption);
  const head = table.createTHead().insertRow();
  keys.forEach(key => { const th = document.createElement("th"); th.scope = "col"; th.textContent = key; head.append(th); });
  const body = table.createTBody();
  rows.slice(page * size, (page + 1) * size).forEach(row => { const tr = body.insertRow(); keys.forEach(key => { tr.insertCell().textContent = text(row[key]); }); });
  $("viz-data").append(table); $("viz-page").textContent = rows.length ? `${page * size + 1}–${Math.min((page + 1) * size, rows.length)} / ${rows.length}` : "No samples";
  $("viz-prev").disabled = page === 0; $("viz-next").disabled = (page + 1) * size >= rows.length;
}
function draw() {
  disableExports(true);
  if (!selected) return;
  try {
    const result = chart.setData(selected, {xScale: $("viz-x").value, yScale: $("viz-y").value});
    $("viz-render-info").textContent = `Source samples: ${selected.sample_count}. Source clipping: none; zoom affects the view only. Uncertainty: ${selected.uncertainty}. ` +
      result.series.map(series => `${series.name}: ${series.displayed_points}/${series.source_points} points displayed (${series.reduction}).`).join(" ");
    disableExports(false); status("Current source loaded. Zoom with the chart controls; exports include source metadata.");
  } catch (error) { status(`Plot unavailable: ${error.message}${error.code==='LOG_DOMAIN'?'. Choose a linear axis for zero or signed values.':''}`, true); }
}
function selectPlot() {
  selected = payload?.plots.find(plot => plot.id === $("viz-plot").value) ?? null; page = 0;
  if (!selected) { clear(); return; }
  $("viz-title").textContent = selected.title;
  $("viz-lineage").replaceChildren();
  Object.entries(selected.source).filter(([key]) => !["assumptions", "warnings", "source_record", "source_canonical_json"].includes(key)).forEach(([key, value]) => {
    const dt = document.createElement("dt"), dd = document.createElement("dd"); dt.textContent = key.replaceAll("_", " "); dd.textContent = text(value); $("viz-lineage").append(dt, dd);
  });
  $("viz-notes").replaceChildren(); selected.notes.forEach(note => { const p = document.createElement("p"); p.textContent = note; $("viz-notes").append(p); });
  $("viz-assumptions").textContent = JSON.stringify({assumptions: selected.source.assumptions, warnings: selected.source.warnings}, null, 2);
  sourceTable(); draw();
}
async function load(path) {
  activeSourcePath = path;
  const sequence = ++requestSequence; clear(); status("Reading exact current source…"); disableExports(true);
  try {
    const candidate = await read(path); if (sequence !== requestSequence) return;
    payload = candidate; $("viz-plot").replaceChildren();
    payload.plots.forEach(plot => { const option = document.createElement("option"); option.value = plot.id; option.textContent = plot.title; $("viz-plot").append(option); });
    $("viz-unavailable").textContent = JSON.stringify(payload.unavailable, null, 2);
    selectPlot(); if (!payload.plots.length) status(path.includes('/sensitivity/')?'No continuous valid sensitivity segment with at least two samples. Inspect retained invalid/isolated samples; gaps are never interpolated.':"No current profiles. Calculate the implemented nozzle/cooling stages in Rocket Engine, then reload.");
  } catch (error) { if (sequence !== requestSequence) return; payload = null; clear(); status(error.message, true); }
}
function prepareExport(kind, trigger) {
  try {
    const files = window.CosmosPlotExports.buildFiles(chart, kind);
    exports.show(files, chart.plot.source, trigger);
    status("Export snapshot prepared. Choose each file in the dialog; retain its provenance. Download completion is reported by your runtime, not inferred by COSMOS.");
  } catch (error) { status(`${error.code || "EXPORT_UNAVAILABLE"}: ${error.message}. Reload the exact current source or retry.`, true); }
}
const managedProject = window.CosmosManagedEvidence?.projectFromSearch(location.search) || null;
const designPath = value => value.startsWith('managed:') ? `/api/projects/${encodeURIComponent(managedProject)}/records/${encodeURIComponent(value.slice(8))}/plots` : `/api/visualization/designs/${encodeURIComponent(value)}`;
$("viz-design").addEventListener("change", () => { if ($("viz-design").value) load(designPath($("viz-design").value)); else { ++requestSequence; activeSourcePath=null;payload = null; $("viz-plot").replaceChildren(); clear(); } });
$("viz-reload").addEventListener("click", () => { if (activeSourcePath) load(activeSourcePath);else if ($("viz-design").value) load(designPath($("viz-design").value)); });
$("viz-run-load").addEventListener("click", () => { const id = $("viz-run").value.trim(); if (id) load(managedProject ? `/api/projects/${encodeURIComponent(managedProject)}/jobs/${encodeURIComponent(id)}/plots` : `/api/visualization/simulation/${encodeURIComponent(id)}`); });
$("viz-plot").addEventListener("change", selectPlot); ["viz-x", "viz-y"].forEach(id => $(id).addEventListener("change", draw));
$("viz-reset").addEventListener("click", () => chart.resetZoom());
function focusView(enabled) {
  if (typeof window.COSMOS.setWorkbenchFocus === "function") {window.COSMOS.setWorkbenchFocus(enabled); return;}
  updateFocus(enabled);
}
function updateFocus(enabled) {
  document.body.classList.toggle("viz-focused", enabled);
  $("viz-focus").setAttribute("aria-pressed", String(enabled));
  $("viz-focus").textContent = enabled ? "Restore workspace (Escape)" : "Focus visualization";
  requestAnimationFrame(() => chart.resize());
}
const focusListener = event => updateFocus(event.detail.enabled === true);
window.addEventListener("cosmos:focus-workspace", focusListener);
$("viz-focus").addEventListener("click", () => focusView(!document.body.classList.contains("viz-focused")));
document.addEventListener("keydown", event => { if (event.key === "Escape" && document.body.classList.contains("viz-focused")) focusView(false); });
$("viz-prev").addEventListener("click", () => { page--; sourceTable(); }); $("viz-next").addEventListener("click", () => { page++; sourceTable(); });
for (const kind of ["json", "csv", "svg"]) $("viz-" + kind).addEventListener("click", event => prepareExport(kind, event.currentTarget));
$("viz-export-close").addEventListener("click", () => exports.dialog.close());
const observer = new ResizeObserver(() => chart.resize()); observer.observe($("viz-chart"));
const shellTheme = document.querySelector(".viz-workbench");
const themeObserver = new MutationObserver(() => { if (selected) draw(); });
if (shellTheme) themeObserver.observe(shellTheme, {attributes:true,attributeFilter:["data-theme"]});
window.addEventListener("pagehide", () => { observer.disconnect(); themeObserver.disconnect(); exports.dispose(); window.removeEventListener("cosmos:focus-workspace",focusListener); chart.dispose(); }, {once: true});
try {
  const context = await read("/api/visualization/context"); $("viz-design").replaceChildren();
  const placeholder = document.createElement("option"); placeholder.value = ""; placeholder.textContent = "Select an engineering design"; $("viz-design").append(placeholder);
  context.designs.forEach(design => { const option = document.createElement("option"); option.value = design.design_id; option.textContent = `${design.name} · r${design.revision}`; $("viz-design").append(option); });
  if(managedProject){const managed=await read(`/api/projects/${encodeURIComponent(managedProject)}/context?domain=propulsion&limit=20`);managed.objects.forEach(item=>{const option=document.createElement('option');option.value='managed:'+item.commit_id;option.textContent=`Managed ${item.object_id} · saved v${item.head.version}`;$("viz-design").append(option);});status('Managed project: select an exact saved design or enter an owning-project run attempt ID. Historical sources are not promoted to current curves.');}
  else status(context.designs.length ? "Select a design to inspect its current implemented profiles." : "No saved designs. Create and calculate an engineering design in Rocket Engine first.");
  const studies=new URLSearchParams(location.search).getAll('sensitivity');if(managedProject&&studies.length===1&&/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(studies[0]))await load(`/api/projects/${encodeURIComponent(managedProject)}/sensitivity/${encodeURIComponent(studies[0])}/plots`);
} catch (error) { status(error.message, true); }
