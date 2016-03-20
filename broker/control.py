"""
The administrative API of Optimal BPM
"""


from bson.objectid import ObjectId

from of.common.logging import EC_SERVICE, SEV_DEBUG, write_to_log
from of.common.security.groups import user_in_any_of_groups
from of.common.internal import not_implemented

from of.schemas.constants import zero_object_id
from of.broker.lib.repositories import Repositories
from plugins.optimalbpm.broker.messaging.factory import agent_control
from of.common.messaging.factory import log_process_state_message
__author__ = 'Nicklas Borjesson'


class Control:
    """
    This class presents the administrative API of Optimal BPM
    """
    #: An MBE database access instance
    db_access = None
    #: An MBE node instance
    node = None
    #: A Repositories instance
    repositories = None
    #: The send queue for sending messages
    send_queue = None
    #: The logging facility
    logging = None
    #: The BPM peer adress of the broker
    address = None
    #: The process ID of this Process (string ObjectId)
    process_id = None
    #: Callback to the stop broker function
    stop_broker = None

    def __init__(self, _db_access, _node, _send_queue, _stop_broker, _address, _process_id):
        """
        :param _db_access: An MBE database access instance
        :param _node: An MBE node instance
        :param _send_queue: The send queue for sending messages
        :param _stop_broker: Callback to the stop broker function
        :param _address: The BPM peer adress of the broker
        :param _process_id: The processId of the Process (string ObjectId)
        """
        self.db_access = _db_access
        self.node = _node
        self.repositories = Repositories(_db_access, _node)
        self.send_queue = _send_queue

        self.process_id = _process_id
        self.stop_broker = _stop_broker

    def save_process_definition(self, _process_definition, _user):
        """
        Save a process definition. Data is a Process definition document identified by _process_definition_id.
        If an id is not defined, the definition is created.

        :param _process_definition: Process definition document
        :param _user: A user instance
        :return: A resulting id
        """
        if "schemaRef" in _process_definition and _process_definition[
                "schemaRef"] == "bpm://node_process.json":

            _init_repository = "_id" not in _process_definition
            _result_id = self.node.save(_process_definition, _user)
            if _init_repository:
                pass
                # TODO: Implement GIT stuff (PROD-11)

                # self.repositories.init_repository(_result_id)
        else:
            raise Exception("save_process_definition: Missing or wrong schemaRef for process definition data.")
        return _result_id

    def load_process_definition(self, _process_definition_id, _user):
        """
        Loads a the process definition defined by _process_definition_id.

        :param _process_definition_id: A process definition Id
        :param _user: A user instance
        :return: a Process definition document identified by _process_definition_id .
        """
        # TODO: This manually converts it into an ObjectId instance, likely not needed in later MBE versions(PROD-41)
        _result = self.node.find({"_id": ObjectId(_process_definition_id)}, _user)

        if len(_result) != 1:
            return None
        else:
            return _result[0]

    def remove_process_definition(self, _process_definition_id, _user):
        """
        Deletes a process definition identified by _process_definition_id.

        :param _process_definition_id: A process definition Id
        :param _user:  User instance
        :return: Result
        """

        return self.node.remove({"_id": ObjectId(_process_definition_id)}, _user)

    @not_implemented
    def get_process_definition_hash(self, _process_definition_id, _user):
        """
        Returns the full hash for HEAD on the repository of the process definition identified by _process_definition_id.
        (Calls the Dulwich Repo.head() - function)

        :param _process_definition_id:
        :param _user: User instance
        :return: The SHA1 Hash value.
        """

        pass

    def start_process(self, _start_process_message, _user):
        """
        Starts a process given a start process message.

        :param _start_process_message: An instance of a _start_process_message
        :param _user: A user instance


        """
        # Read process definition information
        _process_definition = self.load_process_definition(_start_process_message["processDefinitionId"], _user)
        # Check permissions
        if not user_in_any_of_groups(_user, _process_definition["canStart"]):
            raise Exception("User doesn't have the canStart permission.")

        self.send_queue.put([None, _start_process_message])

        return _start_process_message["processId"]

    @not_implemented
    def pause_process(self, process_id, _user):
        """
        Pauses a BPM process given a BPM process process_id (3.0).

        :param process_id: Optimal BPM Process Id
        :param _user: A user instance

        """

        pass

    @not_implemented
    def stop_process(self, _process_id, _user):
        """
        Terminate a BPM process gracefully given a BPM process_id.

        :param _process_id: Optimal BPM Process Id
        :param _user: A user instance
        """
        pass

    @not_implemented
    def kill_process(self, _process_id, _user):
        """
        Kills a process – Instructs an agent to kill a  BPM process given a BPM process process_id.

        :param _process_id: Optimal BPM Process Id
        :param _user: A user instance
        """
        pass



    def agent_control(self, _address, _command, _reason, _user):
        """
        Controls an agent's running state

        :param _address: The address of the agent to control
        :param _command: Can be "stop" or "restart".
        :param _user: A user instance
        """
        write_to_log("Control.agent_control: Got the command " + str(_command), _category=EC_SERVICE, _severity=SEV_DEBUG)

        self.send_queue.put([None, agent_control(_destination=_address,
                                                 _destination_process_id=zero_object_id,
                                                 _command=_command,
                                                 _reason=_reason,
                                                 _user_id=_user["_id"],
                                                 _source=self.address,
                                                 _source_process_id=self.process_id,
                                                 _message_id=1
                                                 )])

        return {}
    @not_implemented
    def save_tokens(self, _process_definition_id, _file_path, _tokens, _user):
        """
        Saves an array of tokens to a process definition file. file_path is the relative path to the repository root.
        Server-side, the tokens are translated to text, and saved to the file.

        :param _process_definition_id: The process definition Id
        :param _file_path: The path to the file inside the repository
        :param _tokens: Array of tokens
        :param _user: A user instance
        """
        pass

    @not_implemented
    def load_tokens(self, _process_definition_id, _file_path, _user):
        """
        Loads an array of tokens from a process definition.
        Server-side, the specified text file is read, turned into a token array using a tokenizer, and sent to the peer.
        file_path is the relative path to the repository root.

        :param _process_definition_id: The process definition Id
        :param _file_path: The path to the file inside the repository
        :param _user: A user instance
        """
        pass

    def get_module_definitions(self, _module_name, _user):
        """
        Loads all function definitions of a module referenced by module_name.
        The definition is fetched from two places, the function definition itself using ast.parse + ast.get_docstring
        and a form definition file located in the root of the repository named module_name.def
        Definitions is a module_definition document.

        :param _module_name:
        :param _user: A user instance
        """
        pass

    def get_modules(self, _user):
        """
        Returns a list of module names.

        :param _user: A user instance
        :return: A list of module names
        """
        pass

    def get_processes(self, _user):
        """
        Returns a list of all active processes

        :return: A list of all active processes
        """
        # TODO: Filter by what canRead on the nodes? Have some node rights cache? (ORG-110)
        # Also, this is more of a web socket stream.
        return self.db_access.find({"conditions": {}, "collection": "process"})

    def get_schemas(self, _user):
        """
        Returns a list of all schemas

        :return: A list of all schemas
        """
        # TODO: Filter by what canRead on the nodes? Have some node rights cache? (ORG-110)
        # Also, this is more of a web socket stream.
        result = {}
        for key, schema in self.db_access.schema_tools.json_schema_objects.items():
            result[key] = self.db_access.schema_tools.resolveSchema(schema)

        return result

    def get_process_history(self, _process_id, _user):
        """
        Returns the history of a process

        :return: A list of all the states
        """
        # TODO: Filter by what canRead on the nodes? Have some node rights cache? (ORG-110)
        # Also, this is more of a web socket stream.
        return self.db_access.find({"conditions": {"processId": ObjectId(_process_id)}, "collection": "log"})
