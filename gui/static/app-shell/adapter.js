/* Read-only migration adapter over COSMOS's existing application services. */
(function (host, factory) { if (typeof module === 'object' && module.exports)
    module.exports = factory(require('./model.js'));
else
    host.CosmosShellAdapter = factory(host.CosmosShellModel); })(globalThis, function (M) {
    'use strict';
    class Adapter {
        constructor(api) { this.api = api; this.generation = 0; this.jobsGeneration = 0; }
        async read(url) { const payload = await this.api.get(url); if (payload?.ok === false || payload?.error)
            throw new M.ShellError(payload.error?.code || 'API_READ', payload.error?.message || 'Application read failed'); return payload; }
        async bootstrap() {
            const [configuration, workbenches, designs] = await Promise.all([
                this.read('/api/ui/shell'), this.read('/api/workbenches'), this.read('/api/propulsion/designs')
            ]);
            if (configuration?.schemaVersion !== 1 || configuration.enabled !== true)
                throw new M.ShellError('SHELL_DISABLED', 'Modern shell is disabled by the server');
            if (configuration.historicalSnapshots !== false || configuration.scientificBackendActivated !== false ||
                configuration.jobDomain !== 'knowledge-ingestion' || typeof configuration.projectContext !== 'string')
                throw new M.ShellError('SHELL_CONFIGURATION', 'Server capabilities do not match this read-only migration adapter');
            return Object.freeze({configuration:M.immutable(configuration),catalog:M.catalog(workbenches),designs:M.summaries(designs)});
        }
        async selectDesign(id) { M.identifier(id); const generation = ++this.generation; const payload = await this.read('/api/propulsion/designs/' + encodeURIComponent(id)); return generation === this.generation ? M.design(payload, id) : null; }
        async selectDesignContext(id, current = []) {
            M.identifier(id);
            const generation = ++this.generation;
            const [payload, listing] = await Promise.all([
                this.read('/api/propulsion/designs/' + encodeURIComponent(id)),
                this.readDesigns().then(designs => ({ designs, error: null }), error => ({ designs: current, error }))
            ]);
            if (generation !== this.generation) return null;
            let selected = M.design(payload, id);
            const requiredRevision = Math.max(current.find(row => row.designId === id)?.revision ?? -1, listing.designs.find(row => row.designId === id)?.revision ?? -1);
            // A save may fall between these GETs. Retry only the persisted DTO,
            // once, and never publish mismatched list/design revisions.
            if (requiredRevision > selected.revision) {
                selected = M.design(await this.read('/api/propulsion/designs/' + encodeURIComponent(id)), id);
                if (generation !== this.generation) return null;
            }
            return Object.freeze({ design: selected, designs: M.reconcileDesigns(current, listing.designs, selected),
                summaryDiagnostic: listing.error ? Object.freeze({ code: 'DESIGN_SUMMARIES_UNAVAILABLE', message: 'Design details were refreshed, but the full design list could not be read: ' + (listing.error.message || String(listing.error)) }) : null });
        }
        async refreshDesigns(current = []) {
            const generation = ++this.generation;
            const designs = await this.readDesigns();
            return generation === this.generation ? M.reconcileDesigns(current, designs) : null;
        }
        invalidate() { this.generation++; this.jobsGeneration++; }
        async readDomainJobs(catalog) {
            const generation=++this.jobsGeneration, diagnostics=[], collected=[];
            const diagnostic=(domain,error)=>diagnostics.push(Object.freeze({domain,code:error.code||'JOB_READ',message:error.message||String(error)}));
            await Promise.all([
                this.readJobs().then(values=>collected.push(...values.map(job=>M.immutable({...job,evidenceUrl:job.sourceId==='unknown'?null:'/api/sources/'+encodeURIComponent(job.sourceId),scope:'Knowledge ingestion/review; not a scientific solver',freshness:'read snapshot'}))),error=>diagnostic('knowledge-ingestion',error)),
                ...[['native-geometry','/api/ngg/','job_ids'],['simulation','/api/simulation/','run_ids']].filter(([domain])=>catalog.some(item=>item.workbench_id===domain && item.status==='active')).map(async([domain,base,key])=>{
                    try {
                        const context=await this.read(base+'context'), ids=context[key];
                        if(!Array.isArray(ids)||ids.length>32) throw new M.ShellError('JOB_LIMIT','Domain context exceeds supported retained-job bounds');
                        for(const id of ids) M.identifier(id);
                        await Promise.all(ids.map(async id=>{try{const value=M.domainJob(domain,await this.read(base+(domain==='simulation'?'runs/':'jobs/')+encodeURIComponent(id))); if(value.jobId!==id) throw new M.ShellError('JOB_IDENTITY','Returned job does not match the requested identity'); collected.push(value);}catch(error){diagnostic(domain,error);}}));
                    } catch(error) {diagnostic(domain,error);}
                })
            ]);
            if(generation!==this.jobsGeneration) return null;
            return Object.freeze({jobs:Object.freeze(collected.sort((a,b)=>a.domain.localeCompare(b.domain)||a.jobId.localeCompare(b.jobId))),diagnostics:Object.freeze(diagnostics),
                retention:'Knowledge jobs are persisted by their service; native/simulation histories are bounded actor sessions, not durable Project authority.'});
        }
        async readJobs() { return M.jobs(await this.read('/api/jobs')); }
        async readDesigns() { return M.summaries(await this.read('/api/propulsion/designs')); }
    }
    return Object.freeze({ Adapter });
});
