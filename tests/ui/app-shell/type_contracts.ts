import { Adapter } from '../../../gui/static/app-shell/adapter';
import { defaults, quantity, history, navigation, navigationCommands, routeIdentity, reconcileDesigns, reconcileInspection, bridgeIdentity, matchesBridge } from '../../../gui/static/app-shell/model';
import type { ShellPreferences } from '../../../gui/static/app-shell/contracts';
const valid: ShellPreferences = { ...defaults, units: 'SI' };
quantity({ magnitude: 5, unit: { symbol: 'bar' } }, valid.units);
const adapter = new Adapter({ get: async () => ({}) });
adapter.selectDesign('design-id').then(design => {
    if (design) {
        history(design);
        // @ts-expect-error Persisted scientific DTO is immutable.
        design.revision = 5;
    }
});
// @ts-expect-error Undefined display units are not accepted.
quantity({ magnitude: 5, unit_symbol: 'Pa' }, 'US');
// @ts-expect-error Modes are a closed presentation contract.
const invalid: ShellPreferences = { ...defaults, mode: 'Automatic' };
void invalid;
const navigationItems = navigation([{ workbench_id: 'rocket-engine', title: 'Rocket Engine', status: 'active', route: '/app/workbench/rocket-engine' }]);
routeIdentity('/app/projects?view=history');
navigationCommands([]).forEach(command => { if (!command.disabled && command.path) void command.path; });
// @ts-expect-error Navigation projections are immutable.
navigationItems[0].path = '/wrong';
adapter.selectDesignContext('design-id').then(selection => {
    if (!selection) return;
    reconcileDesigns(selection.designs, selection.designs, selection.design);
    reconcileInspection(null, selection.design, 'latest');
    // @ts-expect-error Combined list/design selection remains read-only.
    selection.designs[0].revision = 1;
});
adapter.refreshDesigns([]).then(designs => { if (designs) void designs[0]?.revision; });
const editorIdentity = bridgeIdentity({ designId: 'design-id', revision: 9, name: 'Saved name' });
matchesBridge(null, editorIdentity);
if (editorIdentity) {
    // @ts-expect-error Editor identity projections are immutable.
    editorIdentity.revision = 10;
}
