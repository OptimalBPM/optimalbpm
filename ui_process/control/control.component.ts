import { Component, OnInit } from '@angular/core';
import { CORE_DIRECTIVES } from '@angular/common';
import { upgradeAdapter } from "/admin/upgrade.adapter";

//TODO:: remove angular2 wrapper around upgraded components if fixed https://github.com/angular/angular/issues/10069
let UpgradedComponent = upgradeAdapter.upgradeNg1Component('uControl');

let __moduleName: any; // fully resolved filename; defined at module load time 

@Component({
    moduleId: __moduleName,  
    selector: 'bpmControl',
    template: '<u-control></u-control>',
    directives: [ CORE_DIRECTIVES, UpgradedComponent]
})
export class ControlComponent {}