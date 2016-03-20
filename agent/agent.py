"""
This module implements the Optimal BPM agent initialization and shut down functionality
"""

import multiprocessing
import os
import sys
import datetime
from multiprocessing import Process, Queue
import time


from bson.objectid import ObjectId

# The directory of the current file
from plugins.optimalbpm.schemas.validation import bpm_uri_handler
from requests.exceptions import SSLError

from of.common.internal import resolve_config_path
from of.common.logging import write_to_log, EC_SERVICE, SEV_DEBUG, make_textual_log_message, \
    make_sparse_log_message, EC_UNCATEGORIZED, SEV_ERROR, SEV_FATAL, SEV_INFO, EC_NOTIFICATION, SEV_WARNING, \
    category_identifiers, severity_identifiers, EC_COMMUNICATION
from of.common.messaging.utils import call_api
from of.common.settings import JSONXPath

script_dir = os.path.dirname(__file__)

# Add relative optimal bpm path
sys.path.append(os.path.join(script_dir, "../../"))

from of.schemas.schema import SchemaTools
from plugins.optimalbpm.agent.lib.control.handler import ControlHandler
from plugins.optimalbpm.agent.lib.messaging.handler import AgentWebSocketHandler
from plugins.optimalbpm.agent.lib.messaging.websocket import AgentWebSocket
from plugins.optimalbpm.agent.lib.supervisor.handler import WorkerSupervisor
from plugins.optimalbpm import run_agent
from of.common.internal import register_signals
from of.common.messaging.factory import store_process_system_document, \
    log_process_state_message
from of.common.messaging.utils import register_at_broker
from of.common.queue.monitor import Monitor

from of.schemas.constants import zero_object_id
from of.schemas.validation import of_uri_handler, of_schema_folder
import of.common.messaging.websocket

if os.name == "nt":
    from of.common.logging import write_to_event_log


# Add the plugin definitions to the of ones.
import plugins.optimalbpm.schemas.constants
plugins.optimalbpm.schemas.constants.init()


__author__ = "Nicklas Borjesson"

"""
Global variables
"""

#: The processId of the agent itself, the system pid
_process_id = None
#: The monitor of the control queue, the control queue gets commands on an agent level.
_control_monitor = None
#: While true, run.
_terminated = None
#: The peer address of the agent
_address = ""

# Verify broker ssl certificate on connect if true. Always install a proper certificate on the broker.
_verify_SSL = None

#: The process queue manager
_process_queue_manager = None


_broker_url = None
_username = None
_password = None
_session_id = None

# Global list of peers
_peers = {}

_start_pid = os.getpid()



# The severity when something is logged to the database
_log_to_database_severity = None


def write_srvc_dbg(_data):
    global _process_id
    write_to_log(_address + ": " + _data, _category=EC_SERVICE, _severity=SEV_DEBUG, _process_id=_process_id)


def log_locally(_data, _category, _severity, _process_id_param, _user_id, _occurred_when, _address_param, _node_id, _uid, _pid):
    global _log_to_database_severity, _process_id, _broker_url, _peers, _address

    if _process_id_param is None:
        _process_id_param = _process_id
    if _address_param is None:
        _address_param = _address

    if os.name == "nt":
        write_to_event_log(make_textual_log_message(_data, _data, _category, _severity, _process_id_param, _user_id,
                                                    _occurred_when, _address_param, _node_id, _uid, _pid),
                           "Application", _category, _severity)
    else:
        print(
            make_sparse_log_message(_data, _category, _severity, _process_id, _user_id, _occurred_when, _node_id, _uid,
                                     _pid))
        # TODO: Add support for /var/log/message


def log_to_database(_data, _category, _severity, _process_id_param, _user_id, _occurred_when, _address_param, _node_id, _uid, _pid):
    global _log_to_database_severity, _process_id, _broker_url, _peers, _address, _verify_SSL

    if _process_id_param is None:
        _process_id_param = _process_id
    if _address_param is None:
        _address_param = _address

    if _severity < _log_to_database_severity:
        log_locally(_data, _category, _severity, _process_id_param, _user_id, _occurred_when, _address_param, _node_id, _uid, _pid)
    else:

        _event = (
            {
                "data": _data,
                "category": category_identifiers[_category],
                "severity": severity_identifiers[_severity],
                "uid": _uid,
                "pid": _pid,
                "occurredWhen": _occurred_when,
                "address": _address_param,
                "process_id": _process_id_param,
                "schemaRef": "of://event.json"
            }
        )
        if _node_id is not None:
            _event["node_id"] = _node_id
        if _user_id is not None:
            _event["user_id"] = _user_id

        if _session_id in _peers:
            _session =  _peers[_session_id]
            if "web_socket" in _session and _session["web_socket"].connected:
                _session["queue"].put(_event)
            else:
                try:
                    call_api("https://" + _broker_url + "/write_to_log", _session_id, _event, _print_log=True, _verify_SSL=_verify_SSL)

                except Exception as e:
                    log_locally("Failed to send to broker, error: " + str(e) + "\nEvent:" + str(_event), EC_UNCATEGORIZED, SEV_ERROR,
                                _process_id_param, _user_id, _occurred_when, _address_param, _node_id, _uid, _pid)

        log_locally(_data, _category, _severity, _process_id, _user_id, _occurred_when, _address_param, _node_id, _uid, _pid)


def register_agent(_retries, _connect=False):

    global _broker_url, _username, _password, _peers, _session_id, _verify_SSL
    _retry_count = _retries + 1

    write_srvc_dbg("Register agent session (adress : " + _address + ") at broker(URL: https://" +
        _broker_url + ")")

    # Register session at the broker
    _data = None
    while _retry_count > 0:
        try:
            _data = register_at_broker(_address=_address, _type="agent", _server="https://" + _broker_url,
                                       _username=_username, _password=_password, _verify_SSL=_verify_SSL)
            write_srvc_dbg("Agent tried registering, data returned: " + str(_data))
        except Exception as e:
            if _retry_count > 1:
                write_to_log("Failed to register at the broker, will retry " + str(
                    _retry_count - 1) + " more times, error:" + str(e),
                             _category=EC_SERVICE, _severity=SEV_INFO)
            else:
                write_to_log( "Failed to register at the broker, will not retry any more times, error:" +
                    str(e),
                             _category=EC_SERVICE, _severity=SEV_FATAL)
        if _data:
            break
        else:
            if _retry_count > 1:
                time.sleep(3)
            _retry_count -= 1

    if not _data:
        return False

    _session_id = _data["session_id"]
    write_srvc_dbg("Register session at broker done")
    _peers[_session_id] = {
            "address": "broker",
            "session_id": _session_id,
            "queue": Queue()
        }


    if _connect:
        return connect_to_websocket()
    else:
        return True

def connect_to_websocket():
    global _broker_url, _session_id
    write_srvc_dbg("Connecting web socket to broker")
    try:
        # Initiate the web socket connection to the broker
        _web_socket = AgentWebSocket(url="wss://" + _broker_url + "/socket",
                                            _session_id=_session_id,
                                            _stop_agent=stop_agent,
                                     _register_agent = register_agent)

        _web_socket.connect()
        _web_socket.run_forever()
    except Exception as e:
        write_to_log("Fatal: An error occurred establishing the web socket:" + str(e),
                     _category=EC_SERVICE, _severity=SEV_FATAL)
        return False

    write_srvc_dbg("Connecting web socket to broker done")
    return True

def start_agent():
    """
    Starts the agent; Loads settings, connects to database, registers process and starts the web server.
    """

    global _process_id, _control_monitor, _terminated, _address, _process_queue_manager, _broker_url, \
        _username, _password, _peers, _log_to_database_severity, _verify_SSL

    _process_id = str(ObjectId())
    of.common.logging.callback = log_locally
    _terminated = False

    write_srvc_dbg("=====start_agent===============================")
    try:
        _cfg_filename = resolve_config_path()
        _settings = JSONXPath(_cfg_filename)

    except Exception as e:
        write_to_log("Error loading settings: " + str(e), _category=EC_SERVICE, _severity=SEV_FATAL,
                     _process_id=_process_id)
        return

    of.common.logging.severity = of.common.logging.severity_identifiers.index(
        _settings.get("agent/logging/severityLevel", _default="warning"))

    _log_to_database_severity = of.common.logging.severity_identifiers.index(
        _settings.get("agent/logging/databaseLevel", _default="warning"))

    write_srvc_dbg("===register signal handlers===")
    register_signals(stop_agent)

    # An address is completely necessary.
    _address = _settings.get("agent/address", _default=None)
    if not _address or _address == "":
        raise Exception(write_to_log(
            "Fatal error: Agent cannot start, missing [agent] address setting in configuration file.",
            _category=EC_SERVICE, _severity=SEV_FATAL))
    # An address is completely necessary.
    _verify_SSL = _settings.get("agent/verifySSL", _default=True)
    # Gather credentials
    _broker_url = _settings.get("agent/brokerUrl", _default="127.0.0.1:8080")
    _username = _settings.get("agent/username")
    if not _username:
        raise Exception(write_to_log("Username must be configured", _category=EC_SERVICE, _severity=SEV_FATAL))


    _password = _settings.get("agent/password")
    if not _password:
        raise Exception(write_to_log("Password must be configured", _category=EC_SERVICE, _severity=SEV_FATAL))
    _retries = int(_settings.get("agent/connectionRetries", 5))

    # Register at the broker
    if not register_agent(_retries):
        raise Exception(write_to_log("Fatal: The agent failed to register with the broker, tried " + str(
            _retries + 1) + " time(s), quitting.", _category=EC_SERVICE, _severity=SEV_FATAL))
        os._exit(1)

    of.common.logging.callback = log_to_database

    _repository_base_folder = _settings.get("agent/repositoryFolder",
                                            _default=os.path.join(os.path.dirname(__file__), "repositories"))

    write_srvc_dbg("Load schema tool")

    try:
        # Initiate a schema tools instance for validation other purposes.
        _schema_tools = SchemaTools(_json_schema_folders=[os.path.abspath(os.path.join(script_dir, "..", "schemas")),
                                                          of_schema_folder()],
                                    _uri_handlers={"of": of_uri_handler, "bpm": bpm_uri_handler})
    except Exception as e:
        raise Exception(write_to_log("An error occurred while loading schema tools:" + str(e),
                                     _category=EC_SERVICE, _severity=SEV_FATAL))
        os._exit(1)
        return

    write_srvc_dbg("Load schema tool done")
    try:

        write_srvc_dbg("Initializing monitors")

        # Init the monitor for incoming messages
        _message_monitor = Monitor(
            _handler=AgentWebSocketHandler(_process_id=_process_id,
                                           _peers=_peers,
                                           _schema_tools=_schema_tools,
                                           _address=_address,
                                           _broker_address="broker"))

        # The manager for the process queue
        _process_queue_manager = multiprocessing.Manager()

        # Init the monitor for the worker queue
        _worker_monitor = Monitor(
            _handler=WorkerSupervisor(_process_id=_process_id,
                                      _message_monitor=_message_monitor,
                                      _repo_base_folder=_repository_base_folder), _queue=_process_queue_manager.Queue())

        # Init the monitor for the agent queue
        _control_monitor = Monitor(
            _handler=ControlHandler(_process_id=_process_id,
                                    _address=_address,
                                    _message_monitor=_message_monitor,
                                    _worker_monitor=_worker_monitor,
                                    _stop_agent=stop_agent
                                    ))

        # The global variable for handling websockets. TODO: Could this be done without globals? (PROD-33)
        of.common.messaging.websocket.monitor = _message_monitor
        write_srvc_dbg("Initializing monitors done")

    except Exception as e:
        raise Exception(write_to_log("Fatal: An error occurred while initiating the Agent class:" + str(e),
                                         _category=EC_SERVICE, _severity=SEV_FATAL))
        os._exit(1)

    # Try to connect to websocket, quit on failure
    if not connect_to_websocket():
        os._exit(1)

    write_srvc_dbg("Register agent system process")
    _control_monitor.handler.message_monitor.queue.put(
        [None, store_process_system_document(_process_id=_process_id,
                                             _name="Agent instance(" + _address + ")")])
    write_srvc_dbg("Log agent system state")
    _control_monitor.handler.message_monitor.queue.put([None,
                                                        log_process_state_message(_changed_by=zero_object_id,
                                                                                  _state="running",
                                                                                  _process_id=_process_id,
                                                                                  _reason="Agent starting up at " +
                                                                                          _address)])


    # Security check to remind broker if it is unsecured

    if not _verify_SSL:
        try:
            call_api("https://"+ _broker_url + "/status", _data={}, _session_id= _session_id, _verify_SSL=True)
        except SSLError as e:
                write_to_log("There is a problem with the security certificate:\n" + str(e) + "\n"
                             "This is a security risk, and and important thing to address.",
                             _category=EC_NOTIFICATION, _severity=SEV_WARNING)
        except Exception as e:
            write_to_log("An error occured while checking status of broker and SSL certificate:" + str(e),
                             _category=EC_NOTIFICATION, _severity=SEV_ERROR)

    write_srvc_dbg("Agent up and running.")

    while not _terminated:
        time.sleep(0.1)

    write_srvc_dbg("Exiting main thread")

def stop_agent(_reason, _restart=False):
    """
    Shuts down the agent
    :param _reason: The reason for shutting down
    :param _restart: If set, the agent will restart
    """
    global _process_queue_manager, _start_pid

    # Make sure this is not a child process also calling signal handler
    if _start_pid != os.getpid():
        write_srvc_dbg("Ignoring child processes' signal call to stop_agent().")
        return

    if _restart is True:
        write_srvc_dbg( "--------------AGENT WAS TOLD TO RESTART------------")
    else:
        write_srvc_dbg( "--------------AGENT WAS TERMINATED, shutting down orderly------------")

    write_srvc_dbg( "Reason:" + str(_reason))
    write_srvc_dbg("Process Id: " + str(_process_id))

    try:
        write_srvc_dbg("try and tell the broker about shutting down")
        _control_monitor.handler.message_monitor.queue.put([None,
                                                            log_process_state_message(_changed_by=zero_object_id,
                                                                                      _state="stopped",
                                                                                      _process_id=_process_id,
                                                                                      _reason="Agent stopped at " +
                                                                                              _address)])
        # Give some time for it to get there
        time.sleep(0.1)
        write_srvc_dbg("try and tell the broker about shutting down, done")
    except Exception as e:
        write_to_log("Tried and tell the broker about shutting down, failed, error:" + str(e),
                     _category=EC_COMMUNICATION, _severity=SEV_ERROR)


    write_srvc_dbg( "Stop the control monitor.")
    _control_monitor.stop(_reverse_order=True)


    time.sleep(0.4)
    write_srvc_dbg("Control monitor stopped.")
    _exit_status = 0

    _process_queue_manager.shutdown()
    write_srvc_dbg("Process queue manager shut down.")

    if _restart is True:
        write_to_log("Agent was told to restart, so now it starts a new agent instance.", _category=EC_SERVICE, _severity=SEV_INFO )
        #set_start_method("spawn", force=True)
        _agent_process = Process(target=run_agent, name="optimalbpm_agent", daemon=False)
        _agent_process.start()

        # On the current process (source) must still exist while the new process runs if its to be run using without
        # pOpen. TODO: Investigate if it really is impossible to create standalone(non-child) processes using Process.
        write_srvc_dbg("Pid of new instance: " + str(_agent_process.pid))
        _agent_process.join()

    global _terminated
    _terminated = True
    write_srvc_dbg("Agent exiting with exit status " + str(_exit_status))
    if os.name == "nt":
        return _exit_status
    else:
        os._exit(_exit_status)

if __name__ == "__main__":
    """
    If name is set it is run as a separate script, start the agent.
    """
    start_agent()