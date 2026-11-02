/** Read-only UI DTOs. Draft undo is delegated, never a scientific revision undo. */
export interface RocketContext {
 readonly projectId?:string; readonly savedVersion?:number; readonly savedCommitId?:string; readonly savedContentHash?:string;
 readonly designId:string|null; readonly name:string|null; readonly revision:number|null;
 readonly activeKind:'stage'|'module'; readonly activeId:string; readonly dirty:boolean; readonly busy:boolean;
 readonly resultGeneration:number; readonly resultDisplayableAsCurrent?:boolean; readonly loading:boolean; readonly canUndo:boolean; readonly canRedo?:boolean; readonly stages:readonly Readonly<{stage_id:string;implementation_status:string;status?:string;engineering_note?:string;dependency_edges?:readonly unknown[]}>[];
}
export interface RocketBridge {readContext():RocketContext;readResult():Readonly<Record<string,unknown>>|null;readTargetComparison?():Readonly<Record<string,unknown>>|null;undoDraft():boolean;redoDraft?():boolean;restoreNavigation():void;retryResult():Promise<void>|undefined;}
export interface Parameter {readonly label:string;readonly value:string|number;readonly unit:string;readonly source:string;}
export interface ServiceTrace {readonly action:string;readonly api:string;readonly system:string;readonly science:string;}
export interface ResultProjection {
 readonly payload:Readonly<Record<string,unknown>>;readonly status:string;readonly model:string;
 readonly verification:string;readonly validation:string;readonly numerical:string;
 readonly error:Readonly<{code:string;message:string;recovery:string}>|null;
 readonly assumptions:readonly string[];readonly warnings:readonly string[];
 readonly inputs:Readonly<Record<string,unknown>>;readonly outputs:Readonly<Record<string,unknown>>;
}
export interface RocketModel {
 readonly groups:readonly Readonly<{name:string;ids:readonly string[]}>[];
 trace(id:string):ServiceTrace;parameters(value:unknown,source?:string,preference?:'source'|'SI'):readonly Parameter[];
 result(payload:unknown,activeId:string):ResultProjection|null;
}
declare global {interface Window {CosmosRocketModel:RocketModel;CosmosRocketUI:Readonly<{mount():void;rollback():void}>;}}
