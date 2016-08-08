import "jquery";
declare var $:JQueryStatic;

interface IVerticalDraggableMenu {
    columns: any[];
    treeOptions: any;
}

export class VerticalDraggableMenuController implements IVerticalDraggableMenu {
    // Attribute passed to directive
    columns: any[];

    // Attribute passed to directive
    treeOptions: any;

    initPopovers = () => {      
        this.$timeout(() => {
            let _temp: any = $("[data-toggle=\"popover\"]");
            _temp.popover();
        });
    }

    fixPopoverTitle(value: string) {
        return value.replace(/%/g, "");
    }

    static $inject = ["$scope", "$timeout"];

    constructor(public $scope: ng.IScope, public $timeout: ng.ITimeoutService) {
        console.log("Initiating VerticalDraggableMenuController" + $scope.toString());
        console.log(this.columns);
        console.log(this.treeOptions);
        console.log("Initiated VerticalDraggableMenuController");
    }
}