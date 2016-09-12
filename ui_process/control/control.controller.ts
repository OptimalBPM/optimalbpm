interface IControl {
    startedProcesses: string[];
    states: {};
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

export class ControlController implements IControl {

    startedProcesses: string[];

    states: {};

    current_process_history: any[];

    // Processes
    processes: any[] = [];

    // Agents
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

        this.$http.post("admin/control/start_process", _process_data).success((data, status, headers, config) => {
            this.startedProcesses.push(data.toString());
        }).error((data, status, headers, config) => {
            console.log("Failed to start process, error: " + status);
        });
    };

    get_process_states = () => {

        this.$http.get("admin/control/get_process_states").success((data, status, headers, config) => {
            this.states = data;
            
        }).error((data, status, headers, config) => {
            console.log("Failed to get states, error: " + status);
        });
    };

    get_process_history = (process_id: string) => {

        this.$http.post("admin/control/get_process_history", {"process_id": process_id}).success((data, status, headers, config) => {
            this.current_process_history = <Array<any>>data;

        }).error((data, status, headers, config) => {
            console.log("Failed to get states, error: " + status);
        });
    };

    attack = (process_definition_id: string) => {
        for (var i = 0; i < 100; i++) {
            this.start_process(process_definition_id);
        }
        this.get_process_states();
    };

    kill_agent = () => {
        this.$http.post("admin/control/agent_control", {
            "address": this.currAgent,
            "command": "stop",
            "reason": "Testing to stop an Agent."
        }).success((data, status, headers, config) => {
            this.current_process_history = <Array<any>>data;

        }).error((data, status, headers, config) => {
            console.log("Failed to get states, error: " + status);
        });
    };
    loadAgents = (): ng.IPromise<any> => {

        // See schema/constants.py
        return this.$http.post("/node/lookup", {
                "collection": "node", "conditions": {
                    "schemaRef": "ref://of.node.agent",
                    "parent_id": "ObjectId(000000010000010002e64d03)"
                }
            })
            .success((data): any => {
                this.agents = <Array<any>>data;
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

                this.processes = <Array<any>>data;
            })
            .error((data, status, headers, config): any => {
                this.bootstrapAlert("Loading processes failed: " + status);
            });
    };

    //Called when view is loaded to initialize our variables.
    $onInit() {
        console.log('onInit', this);        
        this.startedProcesses = [];
        this.states = {};
    }
    // Inject all necessary dependencies
    static $inject = ["$scope", "$http", "$cookies", "$interval"];

    constructor(public $scope: ng.IScope, public $http: ng.IHttpService, public $cookies: angular.cookies.ICookiesService, public $interval: ng.IIntervalService) {

        console.log("Initiating ControlController");
        this.$interval(this.get_process_states, 2000);
        this.loadAgents();
        this.loadProcesses();
        console.log("Initiated ControlController");
    }
}