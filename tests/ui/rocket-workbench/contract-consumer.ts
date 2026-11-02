import type {RocketBridge,RocketModel,RocketContext,ResultProjection,Parameter} from '../../../gui/static/rocket-workbench/contracts';
declare const bridge:RocketBridge,model:RocketModel;
const context:RocketContext=bridge.readContext();
const result:ResultProjection|null=model.result(bridge.readResult(),context.activeId);
const rows:readonly Parameter[]=model.parameters(result?.outputs,'Backend','SI');
model.trace(context.activeId);
bridge.undoDraft();
// @ts-expect-error immutable context
context.revision=99;
// @ts-expect-error immutable output table
rows.push({label:'invented',value:1,unit:'1',source:'none'});
