import {dataset, points, Dataset} from '../../../gui/static/simulation/model';
declare const untrusted:unknown;
const d:Dataset=dataset(untrusted);
const units:'K'=d.field.unit;
const published:false=d.production_handoff;
const scale:'linear'=d.residual_scale;
points(d.radii_m,d.temperature_k);
void units; void published; void scale;
// @ts-expect-error Display declarations cannot mark this benchmark as experimentally validated.
const validation:'validated'=d.experimental_validation;
void validation;
