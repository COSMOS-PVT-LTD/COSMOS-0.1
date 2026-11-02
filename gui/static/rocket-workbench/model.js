/* P05 immutable presentation/trace contracts. No scientific model or writes. */
(function (host) {
  'use strict';
  const groups = Object.freeze([
    ['Define', ['design_project', 'requirements', 'propellants', 'cycle']],
    ['Analyze', ['operating_point', 'thermochemistry', 'performance', 'chamber']],
    ['Subsystems', ['injector', 'thermal', 'cooling', 'nozzle', 'structure', 'materials']],
    ['Review', ['performance_summary', 'consistency', 'design_review']],
    ['Physics tools', ['nozzle-flow', 'heat-transfer', 'structures']],
  ].map(([name, ids]) => Object.freeze({name, ids: Object.freeze(ids)})));
  const services = {
    design_project: ['Recalculate / save / create', 'api/propulsion_workflow.py', 'systems/workflow/orchestrator.py'],
    requirements: ['Save requirements → /save', 'systems/stages/requirements.py', 'core/quantity.py'],
    propellants: ['Save propellants → /propellants', 'systems/stages/propellants.py', 'physics/thermochemistry/cea_interface.py'],
    cycle: ['Cycle selection → /save (power balance unavailable)', 'api/propulsion_workflow.py', 'systems/workflow/graph.py'],
    operating_point: ['Run Phase 3 → /run/phase3', 'systems/stages/operating_point.py', 'systems/stages/performance.py'],
    thermochemistry: ['Run Phase 3 → /run/phase3', 'systems/stages/thermochemistry.py', 'physics/thermochemistry/cea_interface.py'],
    performance: ['Run Phase 3 → /run/phase3', 'systems/stages/performance.py', 'physics/compressible_flow/'],
    chamber: ['Run Phase 4 → /run/phase4', 'systems/stages/chamber.py', 'core/quantity.py'],
    injector: ['Run subsystem sizing → /run/subsystems', 'systems/stages/subsystems.py', 'physics/injectors/'],
    thermal: ['Run Phase 4 / Bartz tool', 'systems/stages/thermal.py', 'physics/heat_transfer/'],
    cooling: ['Run subsystem sizing → /run/subsystems', 'systems/stages/subsystems.py', 'physics/heat_transfer/regenerative.py'],
    nozzle: ['Run subsystem sizing → /run/subsystems', 'systems/stages/nozzle.py', 'physics/compressible_flow/bell_nozzle.py'],
    structure: ['Thin-wall tool (standalone; not saved stage)', 'gui/server.py', 'physics/solid_mechanics/pressure_vessels.py'],
    materials: ['Run Phase 4 → /run/phase4', 'systems/stages/chamber.py', 'systems/stages/structure.py'],
    performance_summary: ['Run Phase 6 → /run/phase6', 'systems/stages/performance_summary.py', 'systems/workflow/orchestrator.py'],
    consistency: ['Run Phase 6 → /run/phase6', 'systems/stages/consistency.py', 'systems/workflow/orchestrator.py'],
    design_review: ['Run Phase 6 → /run/phase6', 'systems/stages/design_review.py', 'systems/workflow/orchestrator.py'],
    'nozzle-flow': ['Standalone isentropic / area–Mach tools', 'gui/server.py', 'physics/compressible_flow/'],
    'heat-transfer': ['Cooling stage / standalone Bartz tool', 'systems/stages/subsystems.py', 'physics/heat_transfer/'],
    structures: ['Standalone thin-wall tool', 'gui/server.py', 'physics/solid_mechanics/pressure_vessels.py'],
  };
  class PresentationError extends Error {
    constructor(code, message) { super(message); this.name = 'PresentationError'; this.code = code; }
  }
  function freeze(value) { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; }
  function trace(id) {
    const row = services[id];
    if (!row) throw new PresentationError('UNKNOWN_WORKSPACE', 'Workspace has no verified presentation service mapping');
    return freeze({action: row[0], api: 'api/propulsion_workflow.py', system: row[1], science: row[2]});
  }
  const scalarUnits = Object.freeze({gamma:'1', expansion_ratio:'1', mixture_ratio:'1', chamber_temperature_k:'K', molecular_weight_kg_per_mol:'kg/mol', throat_area_m2:'m²', characteristic_length_m:'m', contraction_ratio:'1', wall_thickness_m:'m', external_pressure_pa:'Pa', material_temperature_k:'K', viscosity_pa_s:'Pa·s', conductivity_w_m_k:'W/(m·K)', cp_j_kg_k:'J/(kg·K)', wall_temperature_k:'K'});
  function parameters(value, source = 'API result', preference = 'source') {
    if (!['source','SI'].includes(preference)) throw new PresentationError('INVALID_UNIT_PREFERENCE', 'Unsupported display unit preference');
    const rows = []; let visited = 0;
    function walk(item, path, depth) {
      if (++visited > 12000 || depth > 12) throw new PresentationError('RESULT_LIMIT', 'Projection exceeded bounded result size/depth; inspect original API response');
      if (item === null || item === undefined) return;
      if (typeof item === 'number' && !Number.isFinite(item)) throw new PresentationError('NONFINITE_RESULT', 'Scientific value must be finite');
      if (typeof item === 'object') {
        if ('magnitude' in item || ('value' in item && (item.unit || item.unit_symbol))) {
          const magnitude = item.magnitude ?? item.value;
          const symbol = item.unit_symbol || (typeof item.unit === 'string' ? item.unit : item.unit?.symbol);
          if (typeof magnitude !== 'number' || !Number.isFinite(magnitude) || !symbol) throw new PresentationError('INVALID_QUANTITY', 'Quantity requires a finite magnitude and explicit source unit');
          const other = typeof item.unit === 'string' ? item.unit : item.unit?.symbol;
          if (item.unit_symbol && other && item.unit_symbol !== other) throw new PresentationError('CONFLICTING_UNIT', 'Quantity has conflicting source units');
          const conversion = {bar:[1e5,'Pa'], kN:[1e3,'N'], mm:[0.001,'m']};
          const entry = preference === 'SI' ? conversion[symbol] : null;
          const display = entry ? magnitude * entry[0] : magnitude;
          if (!Number.isFinite(display)) throw new PresentationError('NONFINITE_RESULT','Display conversion overflow');
          rows.push({label:path, value:display, unit:entry ? entry[1] : symbol, source});
          return;
        }
        Object.entries(item).forEach(([key, child]) => walk(child, path ? path+'.'+key : key, depth+1));
      } else if (typeof item === 'number' || typeof item === 'string' || typeof item === 'boolean') {
        const key = path.split('.').at(-1);
        rows.push({label:path, value:typeof item === 'boolean' ? String(item) : item, unit: typeof item === 'number' ? (scalarUnits[key] || 'unspecified (source)') : '—', source});
      }
    }
    walk(value, '', 0);
    return freeze(rows);
  }
  function result(payload, activeId) {
    if (payload === null || payload === undefined) return null;
    if (typeof payload !== 'object' || Array.isArray(payload)) throw new PresentationError('INVALID_RESULT', 'Expected a structured API result');
    const chosen = payload.stages?.[activeId] || payload;
    parameters(chosen.inputs); parameters(chosen.outputs);
    const copied = JSON.parse(JSON.stringify(chosen));
    const status = String(chosen.status || payload.phase_status || (payload.ok === false ? 'FAILED' : 'NOT_CALCULATED'));
    const error = chosen.error || payload.error || chosen.errors?.[0];
    return freeze({payload:copied, status, model:chosen.model_id || chosen.model?.model_id || 'Not reported',
      verification:chosen.verification?.status || chosen.model?.verification_status || 'NOT_REPORTED',
      validation:chosen.validation?.status || chosen.model?.validation_status || payload.validation_level || 'NOT_CLAIMED',
      numerical:chosen.verification?.status === 'EXTERNAL_SOLVER_CONVERGED' ? 'EXTERNAL_SOLVER_CONVERGED' : 'NOT_REPORTED',
      error:error ? {code: error.code || 'STAGE_FAILED', message:error.message || String(error), recovery:error.action || 'Inspect explicit inputs and backend diagnostic, then retry.'} : null,
      assumptions:copied.assumptions || [], warnings:copied.warnings || [], inputs:copied.inputs || {}, outputs:copied.outputs || {}});
  }
  const api = Object.freeze({groups, trace, parameters, result, PresentationError});
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else host.CosmosRocketModel = api;
})(typeof window === 'undefined' ? globalThis : window);
