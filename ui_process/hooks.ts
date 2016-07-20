import { ProcessRoutes, processDirective } from "./process/index";
import { ControlRoutes, controlDirective } from "./control/index";

import { verticalDraggableMenuDirective } from "./draggable_menu/index";

/*
 * Export angular functionality directives,components, services e.t.c
 * This are components that are not part of any other component within the plugin
 * and are going to be available in global scope of the app.
 */
export const pluginStructure = [

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
        display: 'CONTROL',
        path: '/control',
        type: 'left'
    },
    {
        display: 'DESIGN',
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