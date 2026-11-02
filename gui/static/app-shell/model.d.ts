import type { ShellPreferences, DesignSummary, HistoryEvent, ShellDiagnostic } from './contracts';
export type DeepReadonly<T> = T extends object ? {
    readonly [P in keyof T]: DeepReadonly<T[P]>;
} : T;
export interface UnitDTO {
    magnitude: number;
    unit_symbol?: string;
    unit?: {
        symbol: string;
        factor_to_si?: number;
    };
}
export interface Workbench {
    readonly workbench_id: string;
    readonly title: string;
    readonly route: string;
    readonly status: 'active' | 'planned';
}
export interface PersistedDesign {
    readonly design_id: string;
    readonly name: string;
    readonly revision: number;
    readonly change_log: readonly unknown[];
    readonly requirements: Readonly<Record<string, unknown>>;
    readonly status?: { readonly value?: string };
    readonly updated_at?: string;
}
export interface NavigationItem {
    readonly id: string;
    readonly label: string;
    readonly workbenchId: string | null;
    readonly path: string | null;
    readonly availability: 'active' | 'planned' | 'unavailable';
    readonly current: boolean;
}
export interface NavigationCommand {
    readonly id: string;
    readonly label: string;
    readonly path: string | null;
    readonly disabled: boolean;
}
export interface BridgeIdentity {
    readonly designId: string;
    readonly name: string;
    readonly revision: number;
}
export interface KnowledgeJob {
    readonly jobId: string;
    readonly status: string;
    readonly state: 'queued' | 'running' | 'idle' | 'completed' | 'failed' | 'cancelled';
    readonly sourceId: string;
    readonly domain: 'knowledge-ingestion';
    readonly progress: null;
    readonly cancellationSupported: false;
    readonly error: string | null;
}
export class ShellError extends Error {
    readonly code: string;
    constructor(code: string, message: string);
    diagnostic(): ShellDiagnostic;
}
export interface DomainJob {
    readonly domain: 'native-geometry' | 'simulation'; readonly jobId: string; readonly state: string; readonly status: string;
    readonly sourceId: string; readonly progress: number | null; readonly freshness: string; readonly scope: string; readonly stage: string | null;
    readonly cancellationSupported: boolean; readonly cancelPath: string; readonly cancelBody: Readonly<Record<string,string>>;
    readonly evidenceUrl: string; readonly workbenchUrl: string; readonly error: Readonly<Record<string,unknown>> | null;
}
export function domainJob(domain: 'native-geometry' | 'simulation', source: unknown): DomainJob;
export function immutable<T>(value: T): DeepReadonly<T>;
export function identifier(value: unknown): string;
export function summaries(payload: unknown): readonly DesignSummary[];
export function catalog(payload: unknown): readonly Workbench[];
export function design(payload: unknown, expectedId: string): PersistedDesign;
export function history(data: PersistedDesign | null): readonly HistoryEvent[];
export const defaults: Readonly<ShellPreferences>;
export function actionDescriptors(workbenchId: string): readonly Readonly<{id: string; label: string; selector: string; requiresWrite: boolean}>[];
export function layout(value: Readonly<ShellPreferences>, width: number, options?: {focus?: boolean; narrowPane?: null | 'left' | 'right' | 'bottom'}): Readonly<{narrow: boolean; focus: boolean; leftCollapsed: boolean; rightCollapsed: boolean; bottomCollapsed: boolean}>;
export function preferences(value: unknown): {
    value: ShellPreferences;
    diagnostic: string | null;
};
export function jobs(payload: unknown): readonly KnowledgeJob[];
export function route(path: string, catalogItems: readonly Workbench[]): string;
export function routeIdentity(path: string): string;
export function navigation(catalogItems: readonly Workbench[], currentPath?: string, rocketPath?: string): readonly NavigationItem[];
export function navigationCommands(catalogItems: readonly Workbench[], rocketPath?: string): readonly NavigationCommand[];
export function reconcileDesigns(current: readonly DesignSummary[], incoming: readonly DesignSummary[], selected?: PersistedDesign | null): readonly DesignSummary[];
export function reconcileInspection(previous: PersistedDesign | null, selected: PersistedDesign, key: string): string;
export function bridgeIdentity(value: unknown): BridgeIdentity | null;
export function matchesBridge(data: PersistedDesign | null, identity: BridgeIdentity | null): boolean;
export function quantity(q: UnitDTO | null | undefined, preference?: 'source' | 'SI'): {
    value: number | 'Missing';
    unit: string;
};
