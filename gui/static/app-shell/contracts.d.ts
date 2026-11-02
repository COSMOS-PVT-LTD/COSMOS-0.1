export interface ShellPreferences {
    schemaVersion: 1;
    enabled: boolean;
    leftWidth: number;
    rightWidth: number;
    bottomHeight: number;
    leftCollapsed: boolean;
    rightCollapsed: boolean;
    bottomCollapsed: boolean;
    mode: 'Guided' | 'Standard' | 'Expert';
    theme: 'dark' | 'high-contrast';
    fontScale: 100 | 125 | 150 | 200;
    units: 'source' | 'SI';
}
export interface DesignContext {
    readonly designId: string | null;
    readonly name: string | null;
    readonly revision: number | null;
    readonly dirty: boolean;
    readonly busy: boolean;
}
export interface DesignSummary {
    readonly designId: string;
    readonly name: string;
    readonly revision: number;
    readonly state: string;
    readonly updatedAt: string | null;
}
export interface HistoryEvent {
    readonly key: string;
    readonly revision: number;
    readonly field: string;
    readonly oldValue: unknown;
    readonly newValue: unknown;
    readonly representation: 'change-event-only';
    readonly restorable: false;
}
export interface ShellDiagnostic {
    readonly code: string;
    readonly message: string;
}
export interface ShellController {
    mount(cosmos: unknown, session: unknown): Promise<void>;
    rollback(): void;
}
