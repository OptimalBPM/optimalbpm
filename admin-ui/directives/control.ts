/**
 * Created by nibo on 2015-09-05.
 */
/// <reference path="../typings/angularjs/angular.d.ts" />
/// <reference path="../typings/jquery/jquery.d.ts" />

'use strict';

import "angular";

import "jquery";
import "angular-ui-select";

import {ControlScope} from "../controllers/control"

export function control():ng.IDirective {
    return {
        restrict: 'E',
        scope: {
        },
        controller: "ControlController",
        link: ($scope:ControlScope, element:JQuery) => {
            console.log("link function in process directive called ");

        },
        templateUrl: 'process/views/control/control.html'
    }

}


