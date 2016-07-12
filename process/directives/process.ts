import "angular";

import "jquery";
import "angular-ui-select";

import { upgradeAdapter } from "/admin/upgrade.adapter";
import { ProcessController } from "../controllers/process";

export const processDirective = {
    templateUrl: "process/views/process/process.html",
    controller: ProcessController
};


export const ProcessComponent = upgradeAdapter.upgradeNg1Component('process');

/*export function process(): ng.IDirective {
    return {
        restrict: "E",
        scope: {
        },
        controller: "ProcessController",
        link: ($scope: any, element: JQuery) => {
            console.log("link function in process directive called ");
        },
        templateUrl: "process/views/process/process.html"
    };

}*/


