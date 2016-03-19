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

from common.internal import resolve_config_path
from common.settings import JSONXPath

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

#: The process queue manager
_process_queue_manager = None


_broker_url = None
_username = None
_password = None
_session_id = None

# Global list of peers
_peers = {}

_start_pid = os.getpid()

def _make_log_prefix():
    """
    Make log prefix of the agent.
    """
    return "[" + str(datetime.datetime.utcnow()) + "] " + str(os.getpid()) + "-" + _address + ":"




def logprinter(msg, severity):
    print(msg)
    # TODO: This should be implemented and send errors to the broker (PROD-32)
    # However, it will need process_id and stuff like that.



def stop_agent(_reason, _restart=False):
    """
    Shuts down the agent
    :param _reason: The reason for shutting down
    :param _restart: If set, the agent will restart
    """
    global _process_queue_manager, _start_pid

    # Make sure this is not a child process also calling signal handler
    if _start_pid != os.getpid():
        print("Ignoring child processes' signal call to stop_agent().")
        return

    if _restart is True:
        print(_make_log_prefix() + "--------------AGENT WAS TOLD TO RESTART------------")
    else:
        print(_make_log_prefix() + "--------------AGENT WAS TERMINATED, shutting down orderly------------")

    print(_make_log_prefix() + "Reason:" + str(_reason))
    print("Process Id: " + str(_process_id))

    try:
        print(_make_log_prefix() + "try and tell the broker about shutting down")
        _control_monitor.handler.message_monitor.queue.put([None,
                                                            log_process_state_message(_changed_by=zero_object_id,
                                                                                      _state="stopped",
                                                                                      _process_id=_process_id,
                                                                                      _reason="Agent stopped at " +
                                                                                              _address)])
        # Give some time for it to get there
        time.sleep(0.1)
        print(_make_log_prefix() + "try and tell the broker about shutting down, done")
    except Exception as e:
        print(_make_log_prefix() + "try and tell the broker about shutting down, failed, error:" + str(e))


    print(_make_log_prefix() + "Stop the control monitor.")
    _control_monitor.stop(_reverse_order=True)


    time.sleep(0.4)
    print(_make_log_prefix() + "Control monitor stopped.")
    _exit_status = 0

    _process_queue_manager.shutdown()
    print(_make_log_prefix() + "Process queue manager shut down.")

    if _restart is True:
        print(_make_log_prefix() + "Agent was told to restart, so now it starts a new agent instance.")
        #set_start_method("spawn", force=True)
        _agent_process = Process(target=run_agent, name="optimalbpm_agent", daemon=False)
        _agent_process.start()

        # On the current process (source) must still exist while the new process runs if its to be run using without
        # pOpen. TODO: Investigate if it really is impossible to create standalone(non-child) processes using Process.
        print(_make_log_prefix() + "Pid of new instance: " + str(_agent_process.pid))
        _agent_process.join()

    global _terminated
    _terminated = True
    print(_make_log_prefix() + "Agent exiting with exit status " + str(_exit_status))
    if os.name == "nt":
        return _exit_status
    else:
        os._exit(_exit_status)

def register_agent(_retries, _connect=False):

    global _broker_url, _username, _password, _peers, _session_id
    _retry_count = _retries + 1

    print(
        _make_log_prefix() + "Register agent session (adress : " + _address + ") at broker(URL: https://" +
        _broker_url + ")")

    # Register session at the broker
    _data = None
    while _retry_count > 0:
        try:
            _data = register_at_broker(_address=_address, _type="agent", _server="https://" + _broker_url,
                                       _username=_username, _password=_password)
            print("AGENT TRIED REGISTERING, Data returned: " + str(_data))
        except Exception as e:
            if _retry_count > 1:
                print(_make_log_prefix() + "Failed to register at the broker, will retry " + str(
                    _retry_count - 1) + " more times, error:" + str(e))
            else:
                print(
                    _make_log_prefix() + "Failed to register at the broker, will not retry any more times, error:" +
                    str(e))
        if _data:
            break
        else:
            if _retry_count > 1:
                time.sleep(3)
            _retry_count -= 1

    if not _data:
        return False

    _session_id = _data["session_id"]
    print(_make_log_prefix() + "Register session at broker done")
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
    print(_make_log_prefix() + "Connecting web socket to broker")
    try:
        # Initiate the web socket connection to the broker
        _web_socket = AgentWebSocket(url="wss://" + _broker_url + "/socket",
                                            _session_id=_session_id,
                                            _stop_agent=stop_agent,
                                     _register_agent = register_agent)

        _web_socket.connect()
        _web_socket.run_forever()
    except Exception as e:
        print(_make_log_prefix() + "Fatal: An error occurred establishing the web socket:" + str(e))
        return False

    print(_make_log_prefix() + "Connecting web socket to broker done")
    return True

def start_agent():
    """
    Starts the agent; Loads settings, connects to database, registers process and starts the web server.
    """

    global _process_id, _control_monitor, _terminated, _address, _process_queue_manager, _broker_url, \
        _username, _password, _peers

    _process_id = str(ObjectId())

    _terminated = False

    print("=====start_agent===============================")
    print("=====Process Id: " + str(_process_id) + "=====")
    try:
        _cfg_filename = resolve_config_path()
        _settings = JSONXPath(_cfg_filename)


    except Exception as e:
        print("Error loading settings: " + str(e))
        return

    print("===register signal handlers===")
    register_signals(stop_agent)

    # An address is completely necessary.
    _address = _settings.get("agent/address", _default=None)
    if not _address or _address == "":
        print("Fatal error: Agent cannot start, missing [agent] address setting in configuration file.")
        raise Exception("Agent cannot start, missing address.")

    # Gather credentials
    _broker_url = _settings.get("agent/broker_url", _default="127.0.0.1:8080")
    _username = _settings.get("agent/username")
    if not _username:
        raise Exception("Username must be configured")

    _password = _settings.get("agent/password")
    if not _password:
        raise Exception("Password must be configured")

    _retries = int(_settings.get("agent/connectionRetries", 5))

    # Register at the broker
    if not register_agent(_retries):
        print(_make_log_prefix() + "Fatal: The agent failed to register with the broker, tried " + str(
            _retries + 1) + " time(s), quitting.")
        os._exit(1)

    _repository_base_folder = _settings.get("agent/repositoryFolder",
                                            _default=os.path.join(os.path.dirname(__file__), "repositories"))

    print(_make_log_prefix() + "Load schema tool")

    try:
        # Initiate a schema tools instance for validation other purposes.
        _schema_tools = SchemaTools(_json_schema_folders=[os.path.abspath(os.path.join(script_dir, "..", "schemas")),
                                                          of_schema_folder()],
                                    _uri_handlers={"of": of_uri_handler, "bpm": bpm_uri_handler})
    except Exception as e:
        print(_make_log_prefix() + "Fatal: An error occurred while loading schema tools:" + str(e))
        # TODO: Here other things should be done, like reporting to system logs, sending messages or something.(PROD-32)
        os._exit(1)
        return

    print(_make_log_prefix() + "Load schema tool done")
    try:

        print(_make_log_prefix() + "Initializing monitors")

        # Init the monitor for incoming messages
        _message_monitor = Monitor(
            _handler=AgentWebSocketHandler(_process_id=_process_id,
                                           _peers=_peers,
                                           _schema_tools=_schema_tools,
                                           _address=_address,
                                           _broker_address="broker"),
            _logging_function=logprinter)

        # The manager for the process queue
        _process_queue_manager = multiprocessing.Manager()

        # Init the monitor for the worker queue
        _worker_monitor = Monitor(
            _handler=WorkerSupervisor(_process_id=_process_id,
                                      _message_monitor=_message_monitor,
                                      _repo_base_folder=_repository_base_folder),
            _logging_function=logprinter, _queue=_process_queue_manager.Queue())

        # Init the monitor for the agent queue
        _control_monitor = Monitor(
            _handler=ControlHandler(_process_id=_process_id,
                                    _address=_address,
                                    _message_monitor=_message_monitor,
                                    _worker_monitor=_worker_monitor,
                                    _stop_agent=stop_agent
                                    ),
            _logging_function=logprinter)

        # The global variable for handling websockets. TODO: Could this be done without globals? (PROD-33)
        of.common.messaging.websocket.monitor = _message_monitor
        print(_make_log_prefix() + "Initializing monitors done")

    except Exception as e:
        print(_make_log_prefix() + "Fatal: An error occurred while initiating the Agent class:" + str(e))
        os._exit(1)

    # Try to connect to websocket, quit on failure
    if not connect_to_websocket():
        os._exit(1)

    print(_make_log_prefix() + "Register agent system process")
    _control_monitor.handler.message_monitor.queue.put(
        [None, store_process_system_document(_process_id=_process_id,
                                             _name="Agent instance(" + _address + ")")])
    print(_make_log_prefix() + "Log agent system state")
    _control_monitor.handler.message_monitor.queue.put([None,
                                                        log_process_state_message(_changed_by=zero_object_id,
                                                                                  _state="running",
                                                                                  _process_id=_process_id,
                                                                                  _reason="Agent starting up at " +
                                                                                          _address)])
    print(_make_log_prefix() + "Agent up and running.")

    while not _terminated:
        time.sleep(0.1)

    print(_make_log_prefix() + "Exiting main thread")

if __name__ == "__main__":
    """
    If name is set it is run as a separate script, start the agent.
    """
    start_agent()