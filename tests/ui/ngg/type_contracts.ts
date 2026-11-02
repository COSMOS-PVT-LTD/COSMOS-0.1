import {context,artifactUrl,eligible,mesh,NGGContext,JobStatus} from '../../../gui/static/ngg/model.js';
const current:NGGContext=context({});const candidate:JobStatus={state:'accepted',current:true,published:false,engineering_export_eligible:false,snapshot_id:current.snapshot.content_sha256};
const allowed:boolean=eligible(candidate,current.snapshot.content_sha256);
const vertices:Float32Array=mesh(new ArrayBuffer(36));
const link:string=artifactUrl('job-id',current.snapshot.content_sha256,'fixture');
// @ts-expect-error Preview UI cannot authorize engineering publication.
const invalid:JobStatus={...candidate,engineering_export_eligible:true};
// @ts-expect-error Immutable authoritative SI value cannot be edited in the browser.
current.snapshot.parameters_si[0].value_si=10;
void [allowed,vertices,link,invalid];
