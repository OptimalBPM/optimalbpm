/**
 * Created by nibo on 2015-10-18.
 */
/// <reference path="../typings/angularjs/angular.d.ts" />
/// <reference path="../typings/jquery/jquery.d.ts" />

'use strict';

import "angular";

import "jquery";
import "angular-ui-tree";

import {VerticalDraggableMenuScope} from "../controllers/verticalDraggableMenuController";

export function verticalDraggableMenu():ng.IDirective {
    return {
        restrict: 'E',
        scope: {
            columns: "=",
            treeOptions: "="
        },
        controller: "VerticalDraggableMenuController",
        link: ($scope:VerticalDraggableMenuScope, element:JQuery) => {
            console.log("link function in VerticalDraggableMenu directive called ");

        },
        templateUrl: 'process/views/VerticalDraggableMenu/menu.html'
    }

}


