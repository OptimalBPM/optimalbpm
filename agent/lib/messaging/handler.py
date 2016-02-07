"""
This module holds the AgentWebSocketHandler class
"""
import logging


from of.common.messaging.factory import reply_with_error_message
from of.common.messaging.handler import WebSocketHandler
from plugins.optimalbpm.broker.messaging.constants import AGENT_SHUTTING_DOWN

__author__ = 'Nicklas Börjesson'


class AgentWebSocketHandler(WebSocketHandler):
    """
    Distributes messages from and to the incoming and outgoing message queues of the agent
    """

    #: The process handler. Usually the process handler sets this property by itself.
    process_handler = None
    #: The agent control monitors' queue. Usually the control handler sets this property by itself.
    control_queue = None

    #: The broker peer address
    broker_address = None
    #: The number of inbound messages so far
    inbound_message_count = None
    #: The number of outbound messages so far
    outbound_message_count = None

    def __init__(self, _process_id, _peers, _schema_tools, _address, _broker_address):
        """
        Initialize the class, most significantly the schemaRef category to function short cut map
        :param _process_id: The processId of the agent
        :param _peers: A dict holding the peers
        :param _schema_tools: An SchemaTools instance for validation
        :param _address: The peer address
        :param _broker_address: The peer address of the broker
        """
        super(AgentWebSocketHandler, self).__init__(_process_id, _peers, _schema_tools, _address)
        self.broker_address = _broker_address
        # Map each category to a handler function
        self.category_shortcut.update({
            "process": self.handle_message,
            "message": self.handle_message,
            "log": self.handle_message,
            "control": self.handle_control,
        })
        # Reset statistics
        self.inbound_message_count = 0
        self.outbound_message_count = 0

    def handle_control(self, _web_socket, _message_data):
        """
        Handle control messages, put them on the correct queue
        :param _web_socket: Yet unused in this category
        :param _message_data: The control message
        """
        self.schema_tools.validate(_message_data)
        # TODO: Should this verify that this is from the broker websocket?? (PROD-20)
        if _message_data["schemaRef"] == "bpm://message_worker_process_command.json":
            self.process_handler.forward_message(_message_data)
        else:
            self.control_queue.put(_message_data)

    def send_to_address(self, _address, _message_data):
        """
        This is a message, send it to the message queue of the destinations' session.
        :param _address: The destination address
        :param _message_data: The message data
        """

        try:
            _destination_session = self.peers[self.address__session[_address]]
        except KeyError:
            raise KeyError(self.log_prefix + "Missing or invalid destination = " + str(_address))
        _destination_session["web_socket"].queue_message(_message_data)

    def handle_message(self, _source_web_socket, _message_data):
        """
        Handle inbound and outbound messages.
        :param _source_web_socket: The web socket of the source, if none, it is outbound
        :param _message_data: The message data
        """

        if _source_web_socket is None:
            # This is an outbound message

            self.outbound_message_count += 1
            # TODO: Handle multiple broker peers(other peers?), be informed trough some kind of messaging.(PROD-25)
            # For now, however, always have one broker.
            _message_data["source"] = self.address

            self.send_to_address(self.broker_address, _message_data)
        else:

            self.inbound_message_count += 1
            # This is an inbound message
            try:
                self.schema_tools.validate(_message_data)
            except Exception as e:
                _error = "An error occurred validating an inbound message:" + str(e)
                self.logging_function(_error, logging.ERROR)
                # Respond to sender with an error message
                self.send_to_address(self.broker_address,
                                     reply_with_error_message(self, _message_data, "test"))
            else:
                self.process_handler.forward_message(_message_data)

    def shut_down(self, _user_id):
        """
        Shut down the handler, also shuts down the worker and message monitors
        :param _user_id: The user_id that initiated the shut down
        :return:
        """
        super(AgentWebSocketHandler, self).shut_down(_user_id, AGENT_SHUTTING_DOWN)