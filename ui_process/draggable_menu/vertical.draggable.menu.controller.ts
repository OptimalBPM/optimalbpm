export interface VerticalDraggableMenuScope extends ng.IScope  {
    columns: any[];
    menuManager: VerticalDraggableMenuController;
    treeOptions: any;
}

export class VerticalDraggableMenuController {

    initPopovers = () => {
        this.$timeout(function() {
            let _temp: any = $("[data-toggle=\"popover\"]");
            _temp.popover();
        });
    };
    fixPopoverTitle = (value: string) => {
        return value.replace(/%/g, "");
    };

    static $inject = ["$scope", "$timeout"];

    constructor(public $scope: VerticalDraggableMenuScope, public $timeout: ng.ITimeoutService) {

        console.log("Initiating VerticalDraggableMenuController" + $scope.toString());

        this.$scope.menuManager = this;
        console.log(this.$scope.columns);

        console.log("Initiated VerticalDraggableMenuController");

    }
}