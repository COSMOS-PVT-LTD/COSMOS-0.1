export interface NGGContext {
 readonly policy: 'software-fixtures-only'; readonly published: false; readonly physical_validation: false;
 readonly settings: Readonly<{operation:'sphere'|'union'|'difference'|'intersection'|'self_union';backend:'occt'|'picogk';voxel_m:number}>;
 readonly snapshot: Readonly<{content_sha256:string;project_id:string;revision_id:string;frame_id:string;parameters_si:ReadonlyArray<Readonly<{name:string;value_si:number;unit_symbol:'m';source_ref_id:string}>>;source_refs:ReadonlyArray<Readonly<{ref_id:string;source_uri:string;source_sha256:string}>>}>;
 readonly graph: Readonly<{snapshot_id:string;content_sha256:string}>;
 readonly request: Readonly<{snapshot_id:string;source_tolerance_m:number;export_tolerance_m:number;voxel_resolution_m:number|null;correlation_id:string}>;
 readonly job_ids:readonly string[];
}
export interface JobStatus {readonly state:string;readonly current:boolean;readonly byte_integrity?:boolean;readonly fixture_exchange_eligible?:boolean;readonly published:false;readonly engineering_export_eligible:false;readonly snapshot_id:string;readonly qa?:Readonly<Record<string,unknown>>;readonly record?:Readonly<Record<string,unknown>>}
export class NGGError extends Error {readonly code:string; constructor(code:string,message:string)}
export function context(value:unknown):NGGContext;
export function eligible(value:JobStatus|null,snapshot:string):boolean;
export function mesh(buffer:ArrayBuffer):Float32Array;
export function artifactUrl(job:string,snapshot:string,kind:'preview'|'fixture'):string;
