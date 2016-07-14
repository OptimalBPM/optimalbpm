console.log("Before control definition");

import "angular";
import "angular-ui-select";
import { ControlScope } from "../controllers/control";
import { ControlController } from "../controllers/control";
import { upgradeAdapter } from "/admin/upgrade.adapter";

let __moduleName: any; // fully resolved filename; defined at module load time  

export const controlDirective = {
    templateUrl: "admin/ui_process/views/control/control.html",
    controller: ControlController,
    link: ($scope: ControlScope, element: JQuery) => {
        console.log("link function in control directive called ");
    }
};

console.log("After control definition");


