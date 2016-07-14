console.log("Before verticalDraggableMenu definition");

import "angular";
import "angular-ui-tree";
import { VerticalDraggableMenuScope } from "../controllers/verticalDraggableMenuController";
import { VerticalDraggableMenuController } from "../controllers/verticalDraggableMenuController";
import { upgradeAdapter } from "/admin/upgrade.adapter";

export const verticalDraggableMenuDirective = {
    scope: {
        columns: "=",
        treeOptions: "="
    },
    templateUrl: "admin/ui_process/views/VerticalDraggableMenu/menu.html",
    controller: VerticalDraggableMenuController,
    link: ($scope: VerticalDraggableMenuScope, element: JQuery) => {
        console.log("link function in VerticalDraggableMenu directive called ");
    }
};

console.log("After verticalDraggableMenu definition");

export const VerticalDraggableMenuComponent = upgradeAdapter.upgradeNg1Component('bpmVerticalDraggableMenu');





