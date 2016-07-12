console.log("Before control definition");

import "angular";
import "angular-ui-select";
import { ControlScope } from "../controllers/control";
import { ControlController } from "../controllers/control";
import { upgradeAdapter } from "/optimalbpm/upgrade.adapter";

export const controlDirective = {
    templateUrl: "process/views/control/control.html",
    controller: ControlController,
    link: ($scope: ControlScope, element: JQuery) => {
        console.log("link function in control directive called ");
    }
};

console.log("After control definition");

export const ControlComponent = upgradeAdapter.upgradeNg1Component('control');


