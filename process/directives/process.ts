console.log("Before process definition");

import "angular";
import "jquery";
import "angular-ui-select";
import { ProcessScope } from "../controllers/process";
import { ProcessController } from "../controllers/process";
import { upgradeAdapter } from "/optimalbpm/upgrade.adapter";

export const processDirective = {
    templateUrl: "process/views/process/process.html",
    controller: ProcessController,
    link: ($scope: ProcessScope, element: JQuery) => {
        console.log("link function in process directive called ");
    }
};

console.log("After process definition");

export const ProcessComponent = upgradeAdapter.upgradeNg1Component('process');


