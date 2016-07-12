console.log("Before verticalDraggableMenu definition");

import "angular";
import "angular-ui-tree";
import { VerticalDraggableMenuScope } from "../controllers/verticalDraggableMenuController";
import { VerticalDraggableMenuController } from "../controllers/verticalDraggableMenuController";
import { upgradeAdapter } from "/optimalbpm/upgrade.adapter";

export const verticalDraggableMenuDirective = {
    scope: {
        columns: "=",
        treeOptions: "="
    },
    templateUrl: "process/views/VerticalDraggableMenu/menu.html",
    controller: VerticalDraggableMenuController,
    link: ($scope: VerticalDraggableMenuScope, element: JQuery) => {
        console.log("link function in VerticalDraggableMenu directive called ");
    }
};

console.log("After verticalDraggableMenu definition");

export const VerticalDraggableMenuComponent = upgradeAdapter.upgradeNg1Component('vertical-draggable-menu');





