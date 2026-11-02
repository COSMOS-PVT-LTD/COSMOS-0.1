import * as DS from '../../../gui/static/design-system/components';

const input = DS.UnitInput({label:'Pc',dimension:'pressure',unit:'MPa',valueSI:500000});
const scalar:number|null=input.valueSI;
const plot=DS.PlotPanel({title:'Residual',x:{quantity:'Iteration',unit:'1'},y:{quantity:'Residual',unit:'1'},points:[[0,1],[1,.1]],scale:'log'});
plot.updatePoints([[0,1],[1,.01]]);
plot.dispose();
DS.EngineeringStatus({execution:'completed',verification:'unverified',validation:'not-validated'});
// @ts-expect-error Unknown dimensions must not satisfy the public consumer contract.
DS.UnitInput({label:'bad',dimension:'unknown',unit:'Pa',valueSI:scalar});
// @ts-expect-error Completion is not a validation state.
DS.EngineeringStatus({validation:'completed'});
// @ts-expect-error Plot coordinates are numerical pairs, not string values.
plot.updatePoints([['bad',1],[1,.01]]);
