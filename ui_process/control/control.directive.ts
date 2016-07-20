console.log("Before control definition");

import "angular";
import "angular-ui-select";
import { ControlScope, ControlController } from "./control.controller";
import { upgradeAdapter } from "/admin/upgrade.adapter";

let __moduleName: any; // fully resolved filename; defined at module load time  

export const controlDirective = {
    templateUrl: "admin/ui_process/control/control.view.html",
    controller: ControlController
};

console.log("After control definition");


