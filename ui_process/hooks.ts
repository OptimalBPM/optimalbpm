import { ProcessRoutes } from "./process/process.routes";
import { ControlRoutes } from "./control/control.routes";

//Angular 1 directives import
import { processDirective } from "./directives/process";
import { controlDirective } from "./directives/control";
import { verticalDraggableMenuDirective, VerticalDraggableMenuComponent } from "./directives/verticalDraggableMenu";

/*
 * Export angular functionality directives,components, services e.t.c
 * This are components that are not part of any other component within the plugin
 * and are going to be available in global scope of the app.
 */
export const pluginStructure = [
    VerticalDraggableMenuComponent
];

/*
 * Export your available routes. Note components that are routes should be excluded from above structure e.t.c
 * Angular2 uses a component router hence this components will already be imported when defining routes
 */
export const pluginRoutes = [
    ...ProcessRoutes,
    ...ControlRoutes
];

/*
 * Export menus that should be made available in admin. Note two types supported right, left, & dropdown. Dropdown
 * menu ideally appears in settings menu dropdown on top right corner. Main is append next to last menu
 * item from left to right.
 *
 * This menu items will simply be iterated over by NavbarComponent that is responsible for displaying menus
 */
export const pluginMenus = [
    {
        display: 'Control',
        path: '/control',
        type: 'left'
    },
    {
        display: 'Process',
        path: '/process',
        type: 'left'
    }
];

export function initFramework(app) {
    app.component('uControl', controlDirective);
    app.component('uProcess', processDirective);
    app.component('bpmVerticalDraggableMenu', verticalDraggableMenuDirective);

    console.log("initFramework for Optimal BPM  plugin was run");
}