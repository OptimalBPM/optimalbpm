/**
 * Created by nibo on 2015-09-05.
 */
/// <reference path="../typings/angularjs/angular.d.ts" />
/// <reference path="../typings/jquery/jquery.d.ts" />

'use strict';

import "angular";

import "jquery";
import "angular-ui-select";



export function process():ng.IDirective {
    return {
        restrict: 'E',
        scope: {
        },
        controller: "ProcessController",
        link: ($scope:any, element:JQuery) => {
            console.log("link function in process directive called ");
        },
        templateUrl: 'process/views/process/process.html'
    }

}


