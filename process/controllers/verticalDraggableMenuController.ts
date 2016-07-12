export interface VerticalDraggableMenuScope extends ng.IScope  {
    columns: any[];
    menuManager: VerticalDraggableMenuController;
    treeOptions: any;
}

export class VerticalDraggableMenuController {
    $scope: VerticalDraggableMenuScope;
    $timeout: ng.ITimeoutService;

    initPopovers = () => {
        this.$timeout(function() {
            let _temp: any = $("[data-toggle=\"popover\"]");
            _temp.popover();
        });
    };
    fixPopoverTitle = (value: string) => {
        return value.replace(/%/g, "");
    };


    constructor(private $scope: VerticalDraggableMenuScope, $timeout: ng.ITimeoutService) {

        console.log("Initiating VerticalDraggableMenuController" + $scope.toString());


        this.$scope = $scope;
        this.$scope.menuManager = this;
        this.$timeout = $timeout;
        console.log(this.$scope.columns);

        console.log("Initiated VerticalDraggableMenuController");

    }
}