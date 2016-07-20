console.log("Before verticalDraggableMenu definition");

import "angular";
import "angular-ui-tree";
import { VerticalDraggableMenuController } from "./vertical.draggable.menu.controller";
import { upgradeAdapter } from "/admin/upgrade.adapter";

export const verticalDraggableMenuDirective = {
    bindings: {
        columns: "=",
        treeOptions: "="
    },
    templateUrl: "admin/ui_process/draggable_menu/menu.view.html",
    controller: VerticalDraggableMenuController
};

console.log("After verticalDraggableMenu definition");

// No need for this currently only used in angular 1.x directive
// export const VerticalDraggableMenuComponent = upgradeAdapter.upgradeNg1Component('bpmVerticalDraggableMenu');





