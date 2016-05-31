import {ProcessController} from "./controllers/process";
import {ControlController} from "./controllers/control";
import {VerticalDraggableMenuController} from "./controllers/verticalDraggableMenuController";
import {process} from "./directives/process";
import {control} from "./directives/control";
import {verticalDraggableMenu} from "./directives/verticalDraggableMenu";

export function initFramework(app) {

    app.controller("ProcessController", ["$scope", "$http", "$q", "$timeout", ProcessController]);
    app.controller("ControlController", ["$scope", "$http", "$cookies", "$interval", ControlController]);
    app.controller("VerticalDraggableMenuController", ["$scope", "$timeout", VerticalDraggableMenuController]);

    app.directive("process", process);
    app.directive("control", control);
    app.directive("verticalDraggableMenu", verticalDraggableMenu);
    console.log("initFramework for Optimal BPM was run");
};


export function initRoutes($routeProvider) {
    // Configure all routes
    $routeProvider.when("/process", {"templateUrl": "process/views/process.html"})
        .when("/control", {"templateUrl": "process/views/control.html"});
    console.log("initRoutes for Optimal BPM was run");
};