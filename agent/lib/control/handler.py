"""
This module holds the ControlHandler class.
"""
import threading


from of.common.queue.handler import Handler
from optimalbpm.schemas.constants import schema_id_message_agent_control

__author__ = 'Nicklas Börjesson'


class ControlHandler(Handler):
    """
    The ControlHandler is responsible for executing the agent-level commands, as stopping, starting and supervising
    the monitors of the system.
    """

    #: A map between schema Ids and handlers
    schema_id__handler = None
    #: The Optimal BPM address of the control
    address = None
    #: The base folder for all repositories
    repository_base_folder = None

    #: The process monitor, responsible for communication with the worker processes
    worker_monitor = None
    #: The message monitor responsible for communication with entities outside of the agent
    message_monitor = None

    # A callback to the stop agent function
    stop_agent = None

    def __init__(self, _process_id, _address, _worker_monitor, _message_monitor, _stop_agent):
        """
        Initialize control handler
        :param _process_id: The currenct process Id
        :param _address: The peer address of the agent
        :param _worker_monitor: A worker monitor instance
        :param _message_monitor: The monitor for in- and outgoing message for the client
        :param _stop_agent: A callback function that stops the entire agent process
        """
        super(ControlHandler, self).__init__(_process_id)

        self.address = _address

        self.schema_id__handler = {
            schema_id_message_agent_control: self.handle_agent_control_message
        }
        self.worker_monitor = _worker_monitor
        self.message_monitor = _message_monitor
        self.stop_agent = _stop_agent

    def on_monitor_init(self, _monitor):
        """
        When the monitor initializes, it calls this callback and it by this able to register its queue with the message
        handler.
        :param _monitor: The monitor instance
        :return:
        """

        self.message_monitor.handler.control_queue = _monitor.queue

    def handle_error(self, _error):
        """
        A generic function for handling errors
        :param _error: The error message
        """
        print(self.log_prefix + "An error occured, should implement handle error. Error: " + str(_error))
        # TODO: Implement sending error log messages to the broker using error message (OB1-132)
        # self.logging_function(msg=_error, severity=logging.ERROR)

    def handle_agent_control_message(self, _message_data):
        """
        This methond executes commands in agent level control messages
        :param _message_data: The command message
        :return:
        """
        def _command_local(_command):
            print(self.log_prefix + "Told by user " + _message_data["userId"] +
                  " to " + _command + ", reason: " + _message_data["reason"])
            # Call the agent stop_agent()-callback
            if _command == "stop":
                self.stop_agent(_reason=_message_data["reason"], _restart=False)
            elif _command == "restart":
                self.stop_agent(_reason=_message_data["reason"], _restart=True)

        # Run commands in a separate thread
        _control_thread = threading.Thread(target=_command_local, args=[_message_data["command"]])
        _control_thread.start()

    def handle(self, _message_data):
        """
        This is the generic message handler for the control handler
        :param _message_data: The message data
        """
        print(self.log_prefix + "Handling message : " + str(_message_data))

        try:
            _schema_id = _message_data["schemaId"]
        except KeyError:
            self.handle_error(self.log_prefix + "No schema id found in message.")
            return

        try:
            _handler = self.schema_id__handler[_schema_id]
        except KeyError:
            self.handle_error(self.log_prefix + "No handler found for schema Id " + str(_schema_id))
            return

        try:
            _handler(_message_data)
        except Exception as e:
            # TODO: This should really not close the socket, rather return information (key:PROD-21)
            self.handle_error(self.log_prefix + "Error running handler for " + str(_schema_id) + ": " + str(e))

    def shut_down(self, _user_id):
        """
        Shut down the handler, also shuts down the worker and message monitors
        :param _user_id: The user_id that initiated the shut down
        :return:
        """
        super(ControlHandler, self).shut_down(_user_id)
        # stop the workers(reverse_order= before the messaging handlers
        # (or else they can't communicate their states to the broker)
        self.worker_monitor.stop(_reverse_order=True)
        # stop messaging
        self.message_monitor.stop()