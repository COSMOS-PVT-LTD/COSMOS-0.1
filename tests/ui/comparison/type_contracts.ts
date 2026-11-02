import {report,Receipt} from '../../../gui/static/comparison/model.js';
const r:Receipt=report({});
const accepted:false=r.report.independent_acceptance;
const production:false=r.report.production_handoff;
// @ts-expect-error Preview cannot be independently accepted.
const impossible:true=r.report.independent_acceptance;
if(r.report.kind==='thermal'){
 const unknown:readonly number[]|null=r.report.combined_standard_uncertainty_k;
 // @ts-expect-error Experimental acceptance is never asserted by display contracts.
 const validation:'validated'=r.report.experimental_validation;
 void unknown;void validation;
}
void accepted;void production;void impossible;
