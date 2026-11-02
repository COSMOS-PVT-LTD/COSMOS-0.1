import {claim,report,ClaimReceipt,ReportReceipt} from '../../../gui/static/knowledge-reports/model.js';
const c:ClaimReceipt=claim({}),r:ReportReceipt=report({});
const accepted:false=c.claim.independent_acceptance,released:false=r.report.status.production_handoff;
void [accepted,released];
// @ts-expect-error published report status is immutable
r.report.status.production_handoff=true;
// @ts-expect-error claim source state is immutable
c.claim.source=null;
