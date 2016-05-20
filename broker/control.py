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
    #: An OF database access instance
    db_access = None
    #: An OF node instance
    node = None
    #: A Repositories instance
    repositories = None
    #: The send queue for sending messages
    send_queue = None
    #: The logging facility
    logging = None
    #: The OF peer adress of the broker
    address = None
    #: The process ID of this Process (string ObjectId)
    process_id = None
    #: Callback to the stop broker function
    stop_broker = None

    def __init__(self, _db_access, _node, _send_queue, _stop_broker, _address, _process_id):
        """
        :param _db_access: An OF database access instance
        :param _node: An OF node instance
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

    def load_process_definition(self, _process_definition_id, _user):
        """
        Loads a the process definition defined by _process_definition_id.

        :param _process_definition_id: A process definition Id
        :param _user: A user instance
        :return: a Process definition document identified by _process_definition_id .
        """
        # TODO: This manually converts it into an ObjectId instance, likely not needed in later MBE versions(OB1-44)
        _result = self.node.find({"_id": ObjectId(_process_definition_id)}, _user)

        if len(_result) != 1:
            return None
        else:
            return _result[0]

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
