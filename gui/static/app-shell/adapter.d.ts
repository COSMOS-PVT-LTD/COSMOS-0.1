import type { DesignSummary } from './contracts';
import type { Workbench, PersistedDesign, KnowledgeJob, DomainJob } from './model';
import type { ShellDiagnostic } from './contracts';
export interface ReadAPI {
    get(url: string): Promise<unknown>;
}
export interface ShellConfiguration {
    readonly schemaVersion: 1;
    readonly enabled: true;
    readonly historicalSnapshots: false;
    readonly scientificBackendActivated: false;
    readonly jobDomain: 'knowledge-ingestion';
    readonly projectContext: string;
}
export interface ShellBootstrap {
    readonly configuration: ShellConfiguration;
    readonly catalog: readonly Workbench[];
    readonly designs: readonly DesignSummary[];
}
export interface DesignSelection {
    readonly design: PersistedDesign;
    readonly designs: readonly DesignSummary[];
    readonly summaryDiagnostic: ShellDiagnostic | null;
}
export class Adapter {
    constructor(api: ReadAPI);
    bootstrap(): Promise<ShellBootstrap>;
    selectDesign(id: string): Promise<PersistedDesign | null>;
    selectDesignContext(id: string, current?: readonly DesignSummary[]): Promise<DesignSelection | null>;
    refreshDesigns(current?: readonly DesignSummary[]): Promise<readonly DesignSummary[] | null>;
    invalidate(): void;
    readJobs(): Promise<readonly KnowledgeJob[]>;
    readDomainJobs(catalog: readonly Workbench[]): Promise<Readonly<{jobs: readonly (KnowledgeJob | DomainJob)[]; diagnostics: readonly Readonly<{domain:string;code:string;message:string}>[];retention:string}> | null>;
    readDesigns(): Promise<readonly DesignSummary[]>;
}
