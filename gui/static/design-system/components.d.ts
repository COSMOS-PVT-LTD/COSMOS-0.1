export as namespace CosmosDS;
export type ComponentState = 'idle'|'hover'|'focus'|'disabled'|'loading'|'stale'|'invalid'|'warning'|'error'|'success';
export type Dimension = 'pressure'|'length'|'temperature'|'dimensionless';
export interface Quantity { readonly valueSI:number; readonly dimension:Dimension; readonly unit:string; }
export interface UnitInputProps {label:string;dimension:Dimension;unit:string;valueSI:number|null;minSI?:number;maxSI?:number;disabled?:boolean;onChange?:(value:Quantity)=>void;}
export interface UnitInputElement extends HTMLDivElement {readonly valueSI:number|null;input:HTMLInputElement;unitSelect:HTMLSelectElement;validate():boolean;}
export interface TreeItem {id:string;label:string;children?:TreeItem[];}
export interface ArtifactGate {geometryQa:'passed'|'failed'|'unverified';freshness:'current'|'stale';sourceHash:string;}
export class DesignSystemError extends Error {readonly code:string;diagnostic():Readonly<{code:string;message:string}>;}
export const states:readonly ComponentState[];
export const units:Readonly<Record<Dimension,Readonly<Record<string,number>>>>;
export function quantity(raw:string,dimension:Dimension,unit:string,min?:number,max?:number):Quantity;
export function windowRange(count:number,start?:number,size?:number):Readonly<{start:number;end:number;total:number}>;
export function exportEligibility(artifact:ArtifactGate|null):Readonly<{allowed:boolean;reasons:readonly string[]}>;
export function safeLink(value:string):string;
export function applyState(node:HTMLElement,state:ComponentState):HTMLElement;
export function CosmosShell(props:{project:string;revision:string;inspectedRevision?:string;content?:HTMLElement}):HTMLDivElement;
export function WorkbenchTabs(props:{items:{id:string;label:string}[];selected?:string;onSelect?:(id:string)=>void}):HTMLDivElement;
export function ProjectTree(props:{items:TreeItem[];onSelect?:(id:string)=>void}):HTMLElement;
export function UnitInput(props:UnitInputProps):UnitInputElement;
export function PropertyInspector(props:{title?:string;fields:UnitInputProps[]}):HTMLElement;
export function ParameterTable(props:{title?:string;rows:{label:string;value:number|string;unit:string;source?:string}[]}):HTMLElement;
export function EngineeringStatus(props:{execution?:'idle'|'queued'|'running'|'completed'|'failed'|'cancelled';numerical?:'not-run'|'converged'|'nonconverged'|'failed';freshness?:'draft'|'current'|'stale';verification?:'unverified'|'verified'|'rejected';validation?:'not-validated'|'validated';verificationEvidence?:string[];validationEvidence?:string[]}):HTMLElement;
export function JobMonitor(props:{state?:'idle'|'queued'|'running'|'cancel-requested'|'cancelled'|'completed'|'failed';progress?:number|null;details?:string;onCancel?:()=>void}):HTMLElement;
export function EvidenceLink(props:{label:string;href:string}):HTMLAnchorElement;
export interface PlotPanelElement extends HTMLElement {updatePoints(points:[number,number][]):void;dispose():void;}
export function PlotPanel(props:{title:string;x:{quantity:string;unit:string};y:{quantity:string;unit:string};points:[number,number][];kind?:'curve'|'residual';scale?:'linear'|'log';residualDefinition?:string}):PlotPanelElement;
export function Legend(props:{quantity:string;unit:string;min:number;max:number;clipping?:string;colorMap?:string}):HTMLElement;
export function ArtifactBrowser(props:{items:{name:string;representation:string;status:string;hash?:string;href?:string}[]}):HTMLElement;
export function SplitDock(props:{left?:HTMLElement;right?:HTMLElement;storageKey?:string}):HTMLElement;
export function CommandPalette(props:{commands:{id:string;label:string;disabled?:boolean}[];onCommand?:(id:string)=>void}):HTMLElement & {dispose():void;setCommands(commands:{id:string;label:string;disabled?:boolean}[]):void;openButton:HTMLButtonElement;dialog:HTMLDialogElement};
export function ErrorDetails(props:{code:string;message:string;correlationId?:string;recovery?:string}):HTMLDetailsElement;
export function ReviewSignoff(props:{onReview?:(intent:Readonly<{evidenceReviewed:true;experimentallyValidated:false}>)=>void}):HTMLElement;
export function ExportWizard(props:{artifact:ArtifactGate;onExport?:(intent:Readonly<{format:'stl';sourceHash:string;cadReady:false}>)=>void}):HTMLElement;
export function EmptyState(props:{title:string;reason:string;action?:string;onAction?:()=>void}):HTMLElement;
