console.log("Before process definition");

import "angular";
import "jquery";
import "angular-ui-select";
import { ProcessScope, ProcessController } from "./process.controller";

export const processDirective = {
    templateUrl: "admin/ui_process/process/process.view.html",
    controller: ProcessController,
    controllerAs: 'nodeManager'
};

console.log("After process definition");