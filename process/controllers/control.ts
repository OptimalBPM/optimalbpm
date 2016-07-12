export interface ControlScope extends ng.IScope {
    startedProcesses: string[];
    states: {};
    controller: ControlController;
    current_process_history: any[];

}

class StartProcessMessage {

    process_definition_id: string;
    destination: string;
    source: string;
    globals: {};
    reason: string;
    source_process_id: string;
    message_id: number;
}

export class ControlController {

    $http: ng.IHttpService;
    $scope: ControlScope;
    $cookies: angular.cookies.ICookiesService;
    $interval: ng.IIntervalService;
    $q: ng.IQService;

    // Processes
    processes: any[] = [];

    // Processes
    agents: any[] = [];

    // The currently selected agent
    currAgent: string;

    // The callback to the rootscope's bootstrapAlert function
    bootstrapAlert: Function;

    // Starts a process
    start_process = (process_definition_id: string) => {
        let _process_data: StartProcessMessage = new StartProcessMessage();
        _process_data.process_definition_id = process_definition_id;
        _process_data.destination = "agent01";
        _process_data.reason = "Started through the administrator interface";
        _process_data.source = "web_client" + this.$cookies.get("session_id");
        _process_data.globals = {};
        _process_data.source_process_id = "";
        _process_data.message_id = 1;

        this.$http.post("control/start_process", _process_data).success((data, status, headers, config) => {
            this.$scope.startedProcesses.push(data);

        }).error((data, status, headers, config) => {
            console.log("Failed to start process, error: " + status);
        });
    };

    get_process_states = () => {

        this.$http.get("control/get_process_states").success((data, status, headers, config) => {
            this.$scope.states = data;

        }).error((data, status, headers, config) => {
            console.log("Failed to get states, error: " + status);
        });
    };

    get_process_history = (process_id: string) => {

        this.$http.post("control/get_process_history", {"process_id": process_id}).success((data, status, headers, config) => {
            this.$scope.current_process_history = data;

        }).error((data, status, headers, config) => {
            console.log("Failed to get states, error: " + status);
        });
    };

    attack = (process_definition_id: string) => {
        for (i = 0; i < 100; i++) {
            this.start_process(process_definition_id);
        }
        this.get_process_states();
    };

    kill_agent = () => {
        this.$http.post("control/agent_control", {
            "address": this.currAgent,
            "command": "stop",
            "reason": "Testing to stop an Agent."
        }).success((data, status, headers, config) => {
            this.$scope.current_process_history = data;

        }).error((data, status, headers, config) => {
            console.log("Failed to get states, error: " + status);
        });
    };
    loadAgents = (): ng.IPromise<any> => {

        // See schema/constants.py
        return this.$http.post("/node/lookup", {
                "collection": "node", "conditions": {
                    "schemaRef": "bpm://node_agent.json",
                    "parent_id": "ObjectId(000000010000010002e64d03)"
                }
            })
            .success((data): any => {
                this.agents = data;
            })
            .error((data, status, headers, config): any => {
                this.bootstrapAlert("Loading processes failed: " + status);
            });
    };

    loadProcesses = (): ng.IPromise<any> => {

        // See schema/constants.py
        return this.$http.post("/node/lookup", {
                "collection": "node", "conditions": {
                    "parent_id": "ObjectId(000000010000010002e64d02)"
                }
            })
            .success((data): any => {
                this.processes = data;
            })
            .error((data, status, headers, config): any => {
                this.bootstrapAlert("Loading processes failed: " + status);
            });
    };

    constructor(private $scope: ControlScope, $http: ng.IHttpService, $cookies: angular.cookies.ICookiesService, $interval: ng.IIntervalService) {

        console.log("Initiating ControlController" + $scope.toString());


        this.$scope = $scope;
        this.$scope.controller = this;
        this.$cookies = $cookies;
        this.$interval = $interval;

        this.$interval(this.get_process_states, 2000);
        this.$http = $http;
        this.loadAgents();
        this.loadProcesses();

        console.log("Initiated ControlController");

    }
}