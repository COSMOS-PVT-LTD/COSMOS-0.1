/* Presentation contracts only. All scientific lineage, QA and measurements are server-owned. */
(function(host,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else host.CosmosNGGModel=factory();})(globalThis,function(){
 'use strict';
 class NGGError extends Error {constructor(code,message){super(message);this.code=code;}}
 function requireValue(ok,code,message){if(!ok)throw new NGGError(code,message);}
 const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
 function context(value){requireValue(value?.policy==='software-fixtures-only'&&value.published===false&&value.physical_validation===false&&hash(value.snapshot?.content_sha256)&&value.request?.snapshot_id===value.snapshot.content_sha256&&value.graph?.snapshot_id===value.snapshot.content_sha256,'INVALID_CONTEXT','Missing exact immutable fixture lineage');return value;}
 function eligible(status,snapshot){return status?.state==='accepted'&&status.current===true&&status.byte_integrity===true&&status.fixture_exchange_eligible===true&&status.published===false&&status.engineering_export_eligible===false&&status.snapshot_id===snapshot;}
 function mesh(buffer){requireValue(buffer instanceof ArrayBuffer&&buffer.byteLength>0&&buffer.byteLength<=7200000&&buffer.byteLength%36===0,'INVALID_PREVIEW','Expected bounded SI triangle buffer');const values=new Float32Array(buffer);requireValue(values.every(Number.isFinite),'INVALID_PREVIEW','Nonfinite preview vertices');return values;}
 function artifactUrl(job,snapshot,kind){requireValue(/^job-[a-f0-9]{32}$/.test(job)&&hash(snapshot)&&['preview','fixture'].includes(kind),'INVALID_LINK','Unknown artifact link');return `/api/ngg/jobs/${job}/${kind}?snapshot_id=${snapshot}`;}
 return Object.freeze({NGGError,context,eligible,mesh,artifactUrl});
});
