"""
    Initialization for MBE tests.
"""
import multiprocessing
import os
import time
from multiprocessing import Queue as MultiprocessingQueue, Queue

from bson.objectid import ObjectId
from of.schemas.schema import SchemaTools

from plugins.optimalbpm.agent.lib.control.handler import ControlHandler
from plugins.optimalbpm.agent.lib.messaging.handler import AgentWebSocketHandler
from plugins.optimalbpm.agent.lib.messaging.websocket import MockupAgentWebSocketClient
import plugins.optimalbpm.agent.lib.messaging.websocket
from plugins.optimalbpm.agent.lib.supervisor.handler import WorkerSupervisor, MockupWorkerSupervisor
from plugins.optimalbpm.agent.lib.worker.handler import WorkerHandlerMockup
from of.common.queue.monitor import Monitor
from of.schemas.validation import of_uri_handler, of_schema_folder
from plugins.optimalbpm.schemas.validation import bpm_uri_handler
import of.common.messaging.websocket
from plugins.optimalbpm.testing.init_env import init_bpm_env

script_dir = os.path.dirname(__file__)
__author__ = 'nibo'

_log_prefix = str(os.getpid()) + "-Environment.py: "

# Test users uuids
object_id_user_root = "000000010000010001e64c30"
object_id_user_test = "000000010000010001e64c31"
object_id_user_testagent = "000000010000010001e64c32"

object_id_right_admin_nodes = "000000010000010001e64d01"


def stop_broker():
    pass
def before_all(context):
    init_bpm_env(context)

def before_feature(context, feature):
    """

    Initialisation for all features.

    :param context:
    :param feature:
    :return:

    """
    print(
        "\n" + _log_prefix + "Testing feature " + feature.name + "\n=========================================================================\n")
    context.schema_tools = SchemaTools(_json_schema_folders=[os.path.abspath(os.path.join(script_dir, "..", "..", "..", "schemas")), of_schema_folder()],
                _uri_handlers={"of": of_uri_handler, "bpm": bpm_uri_handler})


    # Fake a user (parts of data only)
    context.user = {"_id": "000000010000010001e64d10",
                    "name": "Test User"}

    # Fake session registration
    _peers = {
        "broker":
            {
                "address": "broker_peer",
                "user": context.user,
                "queue": Queue()
            },
        "broker2":
            {
                "address": "broker2_peer",
                "user": context.user,
                "queue": Queue()
            }
    }
    _process_send_queue_manager = multiprocessing.Manager()

    _process_send_queue = _process_send_queue_manager.Queue()

    if feature.name == "Worker process functionality":
        context.first_process_id = str(ObjectId())
        context.second_process_id = str(ObjectId())
        context.third_process_id = str(ObjectId())
        context.blocking_process_id = str(ObjectId())
        _process_handler_class = WorkerSupervisor
    else:
        _process_handler_class = MockupWorkerSupervisor

    context.agent_process_id = str(ObjectId())

    context.repo_base_folder = os.path.join(os.path.dirname(__file__), "repositories")

    context.message_monitor = Monitor(
        _handler=AgentWebSocketHandler(_process_id=context.agent_process_id, _peers=_peers,
                                       _schema_tools=context.schema_tools, _address="agent_peer",
                                       _broker_address="broker_peer"))

    context.process_monitor = Monitor(
        _handler=_process_handler_class(_process_id=context.agent_process_id,
                                        _message_monitor=context.message_monitor,
                                        _repo_base_folder=context.repo_base_folder),
        _queue=_process_send_queue)

    context.control_monitor = Monitor(
        _handler=ControlHandler(_process_id=context.agent_process_id,
                                _address="agent_peer",
                                _message_monitor=context.message_monitor,
                                _worker_monitor=context.process_monitor,
                                _stop_agent=stop_broker
                                ))

    of.common.messaging.websocket.monitor = context.message_monitor
    context.process_process_id = str(ObjectId())

    if feature.name == "Handle in- and outgoing messages":
        context.worker_handler = WorkerHandlerMockup(_send_queue=context.process_monitor.queue,
                                                     _process_id=context.process_process_id,
                                                     _parent_process_id=context.agent_process_id,
                                                     _repo_base_folder="")

        context.worker_monitor = Monitor(_handler=context.worker_handler)

    # Register mockup WebSockets
    context.broker_socket = MockupAgentWebSocketClient(_session_id="broker", _context=context)
    context.broker_socket2 = MockupAgentWebSocketClient(_session_id="broker2", _context=context)


def after_feature(context, feature):
    print("\n" + _log_prefix + "XOXOXOXOXOXOXO-After feature , stopping control monitor.")
    context.control_monitor.stop(context.user["_id"])
    context.process_monitor.stop(context.user["_id"])
    context.message_monitor.stop(context.user["_id"])
    if feature.name == "Handle in- and outgoing messages":
        context.worker_monitor.stop(context.user["_id"])

    time.sleep(.1)
