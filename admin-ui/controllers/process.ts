
/**
 * Module that implements a tree using MBE, a schema validated form and ui layout

 * @module nodes
 * @service Nodes
 * @author Nicklas Börjesson
 * @link https://www.github.com/OptimalBPM/
 */
'use strict';
import "angular";
import "angular-strap";
import "angular-schema-form";
import "angular-ui-layout";
import "angular-ui-layout/ui-layout.css!";
import "angular-animate";

import "ace";
import "ace/theme-monokai";
import "ace/mode-json";
import "angular-ui/ui-ace";
import "networknt/angular-schema-form-ui-ace";
import "OptimalBPM/angular-schema-form-complex-ui";

import "angular-schema-form-dynamic-select";
import {NodeManager, NodeManagement} from "types/nodeManager";
import {SchemaTreeController} from "controllers/schemaTreeController";
import {TreeNode, NodesScope, Dict, TreeScope} from "types/schemaTreeTypes"

import {Verb} from "../lib/tokens"
import "../css/process.css!";
import "../scripts/utils";

/* The SchemaTreeControl class is instantiated as a controller class in the typescript model */


/* SPECIAL STUFF */
// attach the .equals method to Array's prototype to call it on any array
Array.prototype.equals = function (array) {
    // if the other array is a falsy value, return
    if (!array)
        return false;

    // compare lengths - can save a lot of time
    if (this.length != array.length)
        return false;

    for (var i = 0, l = this.length; i < l; i++) {
        // Check if we have nested arrays
        if (this[i] instanceof Array && array[i] instanceof Array) {
            // recurse into the nested arrays
            if (!this[i].equals(array[i]))
                return false;
        }
        else if (this[i] != array[i]) {
            // Warning - two different object instances will never be equal: {x:20} != {x:20}
            return false;
        }
    }
    return true;
};

class ProcessNode extends TreeNode {
    identifier:string = "";

}
class MenuNode extends ProcessNode {
    description:string = "";
    // The data of the menu node holds the default values of the node
    data :any;
    menuTitle : string;

}

export interface ProcessScope extends NodesScope {

}

export class ProcessController extends NodeManager implements NodeManagement {

    $timeout:ng.ITimeoutService;

    /** The groups variable holds a list of all the groups. */
    groups:any[] = [];


    // Lookup lists
    lists:Dict = {};

    // Processes
    processes : any[] = [];

    // Current process
    currProcess : any;

    // The descriptive text of the process
    documentation = null;
    // The encoding of the process file
    encoding = null;

    // The function definitions by namespace
    definitions = {};

    // The menu columns
    menuColumns : any[];

    // The options for the menu tree
    menuTreeOptions : any;
    // The menu columns
    keywords : any[];

    // Externally stored parameter data
    paramData : any;

    // The scope
    nodeScope : ProcessScope;
    // A List of ids that have been changed.
    changedIds : string[] = [];

    // TODO: Create a directive for the top menu items (ORG-107)
    availableItems:ng.IScope;

    // The list of verbs
    verbs:Verb[];

    schemas: any[];

    process_data = {};

    // The currently highest id, used when adding new nodes
    maxId : number;

    // A helper for supporting drag'n drop to the tree.
    //uiTreeHelper : any;

    //  Access from template..
    objectKeys = function (obj) {
        return Object.keys(obj);
    };
    bootstrapAlert = (message: string): void => {
        this.nodeScope.$root.BootstrapDialog.alert(message)
    };
    
    
    /**
     * Returns a CSS base class given a tree item
     * @param {string} item - the tree item.
     * @returns {string}
     */
    getClassFromItem = (node:ProcessNode):string => {
        if (node.identifier == "while") {
            return "loop"
        } else if (node.identifier == "for") {
            return "loop"
        } else if (node.identifier == "try") {
            return "try"
        } else if (node.identifier == "except") {
            return "except"
        } else if (node.identifier == "if") {
            return "if"
        } else if ((node.identifier == "else") || (node.identifier ==  "elif")) {
            return "else"
        }

        return "blank";
        /*        if (node.type != null) {
         return node.type;
         } else {
         return "blank";
         }*/
    };

    getIconClass = (nodeType:string):string => {
        return "";
        if (nodeType == "def") {
            return "glyphicon glyphicon-pushpin";
        } else if (nodeType == "print") {
            return "glyphicon glyphicon-text-background";
        } else if (nodeType == "import" || nodeType == "from") {
            return "glyphicon glyphicon-log-in";
        } else if (nodeType == "@assign") {
            return "glyphicon glyphicon-pencil";
        } else if (nodeType == "@call") {
            return "glyphicon glyphicon-cog";
        } else if (nodeType == "send_message") {
            return "glyphicon glyphicon-envelope";
        } else {
            return "";
        }
    };

    /**
     *********************** Refresh functions ******************************
     */


    /**
     * Load all schemas
     */
    onInitSchemas = ():ng.IHttpPromise<any> => {
        return this.$http.get('process/views/process/schemas.json')
            .success((data):any => {
                this.tree.schemas = data;
                this.$http.get('node/get_schemas')
                    .success((data: any) => {
                        this.schemas = data;
                    })
                    .error((data: any, status: number, headers: ng.IHttpHeadersGetter, config: ng.IRequestConfig) => {
                        this.bootstrapAlert.alert("Loading schemas failed: " + status);
                    });
            })
            .error((data, status, headers, config):any => {

                this.bootstrapAlert("Loading step typ schemas failed: " + status);
            });
    };


    addToList = (listName, value):void => {
        if (!(listName in this.lists)) {
            this.lists[listName] = [value]
        }
        else {
            this.lists[listName].push(value);
        }
        console.log("added " + value + " to " + listName);

    };

    generateObjectId = () : string => {
        var increment: string = Math.floor(Math.random() * (16777216)).toString(16);
        var pid: string = Math.floor(Math.random() * (65536)).toString(16);
        var machine: string = Math.floor(Math.random() * (16777216)).toString(16);
        var timestamp: string = Math.floor(new Date().valueOf() / 1000).toString(16);

        return '00000000'.substr(0, 8 - timestamp.length) + timestamp +
               '000000'.substr(0, 6 - machine.length) + machine +
               '0000'.substr(0, 4 - pid.length) + pid +
               '000000'.substr(0, 6 - increment.length) + increment;
    };


    copyDoc = (docObj):void => {
        if (docObj) {
            return Object.create(docObj);
        }
        else {
            return null;
        }
    };

    makeParameterList = (parameters) => {
        var list:string[] = [];
        for (var key in parameters) {
            if (parameters.hasOwnProperty(key)) {
                list.push(parameters[key]);
            }
        }
        return list.join(",");
    };

    makeTitle = (item):string => {
        if (("documentation" in item) && (item["documentation"] != "")) {
            return item["documentation"].replace("\\\\n", "<br />");
        } else if (item["type"] == "keyword") {
            var title:string = item["type_title"];
            var parameters = item["parameters"];
            if (item["identifier"] == "@assign") {
                title = title.replace("%parameters%", this.makeParameterList(parameters));
                title = title.replace("%assignments%", this.makeParameterList(item["assignments"]));
            }
            else {
                for (var key in parameters) {
                    if (parameters.hasOwnProperty(key)) {
                        title = title.replace("%" + key + "%", parameters[key]);
                    }
                }
            }

            return title;
        }
        else {
            if (!item["type_title"]) {
                if (item["identifier"]) {
                    return item["identifier"] + "(" + this.makeParameterList(item["parameters"]) + ")"
                } else {
                    return item["type"]
                }
            }
            else {
                return item["type_title"];
            }
        }
    };

    recurseVerbs = (parent, items):ProcessNode[] => {

        var result:ProcessNode[] = [];

        items.forEach((item) => {
            var currItem:ProcessNode = new ProcessNode();
            var currId = Number(item["id"]);
            if (currId > this.maxId) {
                this.maxId = currId
            }
            currItem.id = currId.toString();
            currItem.title = this.makeTitle(item);
            currItem.type = item["type"];
            currItem.identifier = item["identifier"];
            currItem.allowedChildTypes = item["allowedChildTypes"];
            currItem.parentItem = parent;
            this.tree.data[item["id"]] = item;
            currItem.children = this.recurseVerbs(currItem, item.children);
            result.push(currItem)
        });

        return result;
    };

    /**
     * Load process data
     */
    loadProcess = (processId : string):ng.IPromise<any> => {

        return this.$q((resolve, reject) => {
                return this.$http.post('process/load_process', {"processId": processId})
                    .success((data):any => {
                        this.process_data = data;
                        var _curr_parent = null;
                        this.maxId = 0;
                        this.paramData = data.paramData;
                        this.tree.children = this.recurseVerbs(null, data.verbs);

                        resolve()
                    })
                    .error((data, status, headers, config):any => {

                        this.bootstrapAlert("Loading schemas failed: " + status);
                    })
            }
        );
    };
    /**
     * Populate the available commands menu
     */
    populateMenuColumns = (data) => {

        // Creates a new menu node
        var createDefinition = (id, currDefinition, expanded, identifier, allowedChildTypes, type, menuTitle) => {
            var new_node:MenuNode = new MenuNode();
            new_node.id = id;
            new_node.title = currDefinition["meta"]["title"];
            new_node.menuTitle = menuTitle
            new_node.description = currDefinition["meta"]["description"];
            new_node.type = type;
            new_node.parentItem = null;
            new_node.expanded= expanded;
            new_node.identifier = identifier;
            new_node.allowedChildTypes = allowedChildTypes;
            new_node.children = [];
            new_node.data = {
                "allowedChildTypes": allowedChildTypes,
                "identifier": new_node.identifier,
                "type": type,
                "id": new_node.id,
                "type_title": new_node.title,
                "type_description": new_node.description,
                "row": null,
                "children": [],
                "expanded":expanded,
                "lead_in_whitespace": [],
                "token_begin": null,
                "token_end": null,
                "parameters": {},
                "parameter_order": null,
                "documentation": "",
                "assignments": {},
                "assignment_operator": null,
                "assignment_order": null
            };
            return  new_node;

        };

        this.menuColumns = [];
        var new_definition:MenuNode = new MenuNode();
        var keywords = data["keywords"];
        var new_column = {"title": "Keywords", "children": []};
        for (var keyword in keywords) {
            new_column.children.push(createDefinition(
                "new_keyword_"+ keyword, keywords[keyword], true , keyword,
                ["keyword","call", "documentation", "assign"], "keyword", keyword))
        }
        this.menuColumns.push(new_column);

        for (var namespace in data["definitions"]) {
            var curr_definition = data["definitions"][namespace];
            if ("functions" in curr_definition) {
                var new_column = {"title": curr_definition["meta"]["description"], "children": []};

                for (var functionName in curr_definition["functions"]) {

                    if (namespace != "") {
                        var _identifier:string = namespace + "." + functionName;
                    } else {
                        var _identifier:string = functionName;
                    }

                    new_column.children.push(createDefinition("new_" + namespace + "_" + functionName
                        , curr_definition["functions"][functionName], true, _identifier, [], "call", functionName));

                }
                this.menuColumns.push(new_column)
            }
        }

    };

    /**
     * Load definitions array
     */
    loadDefinitions = ():ng.IPromise<any> => {
        return this.$q((resolve, reject) => {
            return this.$http.get('process/load_definitions')
                .success((data):any => {
                    this.populateMenuColumns(data);
                    this.definitions =  data["definitions"];
                    this.keywords = data["keywords"];
                    resolve()
                })
                .error((data, status, headers, config):any => {

                    this.bootstrapAlert("Loading definitions failed: " + status);
                })
            }
        );
    };

    /**
     * Load definitions array
     */
    loadProcesses = ():ng.IPromise<any> => {

        return this.$q((resolve, reject) => {
            // See schema/constants.py
            return this.$http.post('node/lookup', {"collection": "node", "conditions": {"parent_id": "ObjectId(000000010000010002e64d02)"}})
                .success((data):any => {
                    this.processes =  data;
                    resolve()
                })
                .error((data, status, headers, config):any => {

                    this.bootstrapAlert("Loading processes failed: " + status);
                })
            }
        );
    };


    parseNamespace = (identifier) => {
        var parts:string[] = identifier.split(".");
        if (parts.length == 1) {
            return ["", identifier];
        }
        else {
            return [parts.slice(0, parts.length - 1).join("."), parts[parts.length - 1]];
        }
    };

    getDefinition = (uri:string) : any => {
        var parser = document.createElement("a");
        parser.href = uri;
        var schema: any = _this.schemas[parser.protocol + parser.pathname];
        if (parser.hash != "") {
            var parts = parser.hash.substr(2).split("/");
            var subattr = schema;
            // Drill down the schema
            parts.forEach(function (part) {
                subattr = subattr[part]
            });
            schema = subattr
        }

        return {"schema" : schema, "form": ["*"]}
    };


    // Generate a form and a schema
    generateForm = (node:ProcessNode, data: any) => {
        var type:string = node.type;
        var schema = clone(this.tree.schemas[type]);
        var form: any[] = [];


        var makeField = (type: string, key: string, title: string, description?: string, titleMap? : any, options?: string) => {
            var field = {};
            field["type"] = type;
            field["key"] = key;
            field["title"] = title;
            field["titleMap"] = titleMap;
            if (description !== undefined) {
                field["description"] = description;
            }
            if (titleMap !== undefined) {
                field["titleMap"] = titleMap;
            }

            field["onChange"] = this.onChange;

            if (options) {
                field["options"] = options;
                if (field["type"] == "complex-ui") {
                    // Options will always be set in these cases, Handle complex parameters
                    field["options"]["definitionsCallback"] =this.getDefinition;
                }
            }

            return field
        };

        var addDocumentation = () => {
            if ("documentation" in node) {
                schema["properties"]["documentation"] = {"type": "string"};
                form.push(makeField("textarea", "documentation", "Documentation"));
            };

        };

        var prettyfyKey = (string : string) => {
            string = string.replace("_", " ");
            return string.charAt(0).toUpperCase() + string.slice(1);
        };

        // START GENERATION

        // New nodes doesn't have any orders yet.
        var add_assignment_order = !(data.assignment_order);
        if (add_assignment_order) {data.assignment_order = []}
        var add_parameter_order = !(data.parameter_order);
        if (add_parameter_order) {data.parameter_order = []}

        if (type == "documentation") {
            // Do nothing at all.

        } else
        if (type == "keyword") {
            var keyword_definition = this.keywords[node["identifier"]];
            keyword_definition["parts"].forEach((item) => {
                if (["expression", "python-reference"].indexOf(item["kind"]) > -1) {
                    schema["properties"]["parameters." + item["key"]] = {"type": "string"};
                    form.push(makeField("string", "parameters." + item["key"], prettyfyKey(item["key"])));
                }
            });


        } else if (type == "call") {
            var refs:string[] = this.parseNamespace(node["identifier"]);
            var _parameters = this.definitions[refs[0]]["functions"][refs[1]]["parameters"];

            // Loop assignments

            for (key in node["assignments"]) {
                schema["properties"]["assignments." + key] = {"type": "string"};

                form.push(makeField("string", "assignments." + key, prettyfyKey(key)));
                if (add_assignment_order) {
                    data.assignment_order.push(key)
                }
            }

            if (_parameters) {
                // A definition is available, use that
                _parameters.forEach((parameter) => {
                    if ("options" in parameter) {
                        var options: any = parameter["options"]
                    }
                    else {
                        var options: any = {}
                    }
                    if (parameter["type"] == "complex-ui") {
                        // Handle complex parameters
                        schema["properties"]["parameters." + parameter["key"]] = {"type": "object"};

                        // If a call has a complex parameter, it needs to have a resolution map for later use
                        if (!("dataRefs" in data)) {
                            data.dataRefs = {}
                        }
                        // TODO: Parts of this handling is somewhat bit hacky, investigate if setDetails couldn't do some of this
                        // Check if the data hasn't been replaced already
                        if (!(parameter["key"] in data.dataRefs)) {

                            // Change the data in the parameter to the actual data

                            // If initialized, Complex ui always have a get_data("00000000000000000")-call, parse that objectId.
                            if (parameter["key"] in data.parameters) {
                                var dataRef: string = data.parameters[parameter["key"]].substr(10, 24);
                                // Store the reference so this can be changed back later on
                                data.dataRefs[parameter["key"]] = dataRef;

                                if (dataRef in this.paramData) {
                                    data.parameters[parameter["key"]] = this.paramData[dataRef];
                                } else {
                                    // No data in paramData, initialize empty
                                    data.parameters[parameter["key"]] = {};
                                }



                            }
                            else {
                                // Initialize the parameter
                                var dataRef = this.generateObjectId();
                                data.dataRefs[parameter["key"]] = dataRef;
                                this.paramData[dataRef] = {};
                                // Complex ui needs to have some kind of value
                                data.parameters[parameter["key"]] = this.paramData[dataRef];
                            }

                        }

                    } else {
                        schema["properties"]["parameters." + parameter["key"]] = {"type": parameter["type"]};

                    }
                    form.push(makeField(parameter["type"], "parameters." + parameter["key"], prettyfyKey(parameter["key"]), parameter["description"], parameter["titleMap"], options=options));

                    if (add_parameter_order) {
                        data.parameter_order.push(parameter["key"])
                    }
                });
            }
            else {
                // No definition is available
                for (var key in node["parameters"]) {
                    schema["properties"]["parameters." + key] = {"type": "string"};
                    form.push(makeField("string", "parameters." + key, prettyfyKey(key)));
                    if (add_parameter_order) {
                        data.parameter_order.push(node["key"])
                    }
                }

                // TODO: Add some kind of instruction somewhere on how to define fields. In help?

                form.push(
                    {
                        "type": "help",
                        "helpvalue": "<i>These fields are auto generated based on the call signature.</i>" +
                        "<br /><i>Consider adding definitions</i>"
                    });
            }


        } else if (type == "assign") {

            form.push(
                {
                    "type": "help",
                    "helpvalue": "<i>The variable(s) to assign the data to.</i>"
                });

            // TODO: Add data from documentation.(PROD-31)
            // TODO: Add new input type for identifiers. (PROD-31)

            // Loop assignments
            for (key in node["assignments"]) {
                schema["properties"][key] = {"type": "string"};
                form.push(makeField("string", "assignments." + key, prettyfyKey(key)));
                if (add_assignment_order) {
                    data.assignment_order.push(node["key"])
                }
            }

            form.push(
                {
                    "type": "help",
                    "helpvalue": "<i>Where to get the data from.</i>"
                });

            // Loop parameters
            for (var key in node["parameters"]) {
                schema["properties"]["parameters." + key] = {"type": "string"}
                form.push(makeField("string", "parameters." + key, prettyfyKey(key)));
                if (add_parameter_order) {
                    data.parameter_order.push(node["key"])
                }
            }

        }

        if (node.identifier != "Newline") {
            addDocumentation();
            this.nodeScope.selected_schema = schema;
            this.nodeScope.selected_form = form;
            this.nodeScope.selected_data = data;
        } else {
            console.log("Handling newline");
            this.nodeScope.selected_schema = {type: "object", properties : {"dummy": {type: "string"}}};
            this.nodeScope.selected_form = [{type : "help", helpvalue: "<i>This item can not have any documentation</i>"}];
            this.nodeScope.selected_data = {};
        }


    };
    /**
     * Set the currently edited schema form
     * @param node
     */
    setDetails = (node):void => {
        var data = this.tree.data[node.id]
        this.generateForm(node, data);


    };

    /**
     * Select the provided node
     * @param treeNode
     */
    onSelectNode = (treeNode):void => {

        this.setDetails(this.tree.data[treeNode.id]);
        this.tree.selectedItem = treeNode;
    };






    /**
     * Async. Called when a children should be loaded. Typically contains code to load from backend, Must return a promise.
     * @returns {ng.IPromise}
     */


    // *********************** Initialization *************************
    onAsyncInitTree = ():ng.IPromise<any> => {
        return new this.$q((resolve, reject) => {
            this.onInitSchemas().then(() => {
                this.loadDefinitions().then(() => {
                    resolve();

                });
            });
            /*  // Initialize all metadata
             this.onInitGroups().then(() => {
             this.onInitForms().then(() => {
             this.onInitSchemas().then(() => {
             resolve();
             });
             });
             });*/
        });
    };
    /**
     * Initialize the node controller
     * @param schemaTreeController
     */
    onInit = (schemaTreeController):void => {
        console.log("In NodesController.onInit");
        this.tree = schemaTreeController;
        this.tree.treeScope.nodeManager = this;
    };

    resizeProcess = () => {
        $("#processContainer").height($(window).height() - $("#footerDiv").height() - $("#menuDiv").height() - 170)
    };


    recurseData = ( items):ProcessNode[] => {

        var result = [];

        items.forEach((item) => {
            var curr_data = this.tree.data[item["id"]]
            if ("dataRefs" in curr_data) {
                // Loop all parameters, save data and create calls if they are complex
                for (var paramId in curr_data.dataRefs) {
                    this.paramData[curr_data.dataRefs[paramId]] = curr_data.parameters[paramId];
                    curr_data.parameters[paramId] = "get_data(\"" + curr_data.dataRefs[paramId] + "\")";

                }
                // Remove the dataRefs, it will be recreated next time the item is edited.
                delete curr_data.dataRefs;

            }

            if (item.children && item.children.length) {
                curr_data.children = this.recurseData(item.children);
            }

            result.push(curr_data)
        });


        return result;
    };


    /**
     * Save process
     */
    saveProcess = (savedata):ng.IPromise<any> => {
        return this.$http.post('process/save_process', savedata)
            .success((data):any => {
                console.log("Successfully saved process to server.")
            })
            .error((data, status, headers, config):any => {

                this.bootstrapAlert("Saving process failed: " + status);
            })


    };


    save = () => {
        // TODO: Add resetting of token lists for changed items. (PROD-31)
        this.process_data["verbs"] = this.recurseData(this.tree.children)
        this.saveProcess(this.process_data);
    };

    onChange = (modelValue, key) => {
        declare var _this :any;
        var _curr_item : TreeNode = _this.tree.selectedItem;
        _curr_item.title = _this.makeTitle(_this.nodeScope.selected_data);

        while (_curr_item.parentItem) {
            _curr_item = _curr_item.parentItem;
        }
    };

    onBeforeDrop = function(event) {
        // When an external object is dropped, it must be assigned a "real" id.
        declare var _this :any;
        var new_id : string = (_this.maxId + 1).toString();
        _this.tree.data[new_id] = event.source.cloneModel.data;
        event.source.cloneModel.id = new_id;
        event.source.cloneModel.data.id = new_id;
        delete event.source.cloneModel.data;
        _this.maxId = _this.maxId + 1;
        // console.log("In onDropped" + JSON.stringify(_this.tree.data))
    };

    constructor(private $scope:ProcessScope, $http:ng.IHttpService, $q:ng.IQService, $timeout:ng.ITimeoutService/*, UiTreeHelper: any*/) {
        console.log("Initiating the process controller" + $scope.toString());
        super($scope, $http, $q);

        /*this.uiTreeHelper = UiTreeHelper;*/
        this.$timeout = $timeout;

        $timeout(() => {
            // Set height
            this.resizeProcess();
            $(window).resize(() => {
                this.resizeProcess();
            });
        });
        this.menuTreeOptions= {
            beforeDrop: this.onBeforeDrop
        };

        this.loadProcesses();
        console.log("Initiated the process controller");

    }



}