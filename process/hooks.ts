import {ProcessController} from "./controllers/process";
import {VerticalDraggableMenuController} from "./controllers/verticalDraggableMenuController";
import {verticalDraggableMenu} from "./directives/verticalDraggableMenu";

import {ProcessRoutes} from "./directives/process.routes";
import {ControlRoutes} from "./directives/control.routes";

//Angular 1 directives import
import {processDirective, ProcessComponent} from "./directives/process";
import {controlDirective, ControlComponent} from "./directives/control";

/*
 * Export angular functionality directives,components, services e.t.c
 * This are components that are not part of any other component within the plugin
 * and are going to be available in global scope of the app.
 */
export const pluginStructure = [
    ProcessComponent,
    ControlComponent
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
    app.controller("VerticalDraggableMenuController", ["$scope", "$timeout", VerticalDraggableMenuController]);

    app.directive("verticalDraggableMenu", verticalDraggableMenu);
    app.directive("process", processDirective);
    app.component('control', controlDirective);
    
    console.log("initFramework for Optimal BPM was run");
}


export function initRoutes($routeProvider) {
    // Configure all routes
    $routeProvider.when("/process", {"templateUrl": "process/views/process.html"});
    
    console.log("initRoutes for Optimal BPM was run");
}