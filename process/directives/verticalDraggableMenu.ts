import "angular";
import "jquery";
import "angular-ui-tree";

import {VerticalDraggableMenuScope} from "../controllers/verticalDraggableMenuController";

export function verticalDraggableMenu(): ng.IDirective {
    return {
        restrict: "E",
        scope: {
            columns: "=",
            treeOptions: "="
        },
        controller: "VerticalDraggableMenuController",
        link: ($scope: VerticalDraggableMenuScope, element: JQuery) => {
            console.log("link function in VerticalDraggableMenu directive called ");

        },
        templateUrl: "process/views/VerticalDraggableMenu/menu.html"
    };

}


