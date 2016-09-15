"""
This modules sole purpose is providing a starting point for running worker processes.

Created on Jan 21, 2016

@author: Nicklas Boerjesson

"""

import time

import of.common.logging
from of.common.logging import write_to_log, make_event
from of.common.queue.monitor import Monitor

__author__ = 'Nicklas Borjesson'

send_queue = None
process_id = None

from plugins.optimalbpm.agent.lib.worker.handler import WorkerHandler

def log_to_queue(_data, _category, _severity, _process_id_param, _user_id, _occurred_when, _address_param, _node_id,
                 _uid, _pid):
    if _process_id_param is not None:
        _process_id_param = process_id

    global send_queue, process_id
    _event = make_event(_data, _category, _severity, _process_id_param, _user_id, _occurred_when, _node_id=_node_id,
                        _uid=_uid, _pid=_pid)

    send_queue.put([None, _event])

def run_worker_process(_parent_process_id, _process_id, _queue, _send_queue, _repo_base_folder, _severity):
    """
    This function is the first thing that is called when the worker process is initialized

    :param _parent_process_id: The process_id of the parent process.
    :param _process_id: The process id of this worker
    :param _queue: The instance of multiprocess queue on which the worker expects process messages to appear.
    :param _send_queue: The queue the process uses for external communication
    :param _repo_base_folder: The repository base folder.
    """

    global send_queue, process_id

    of.common.logging.callback = log_to_queue
    of.common.logging.severity = _severity
    process_id = _process_id
    send_queue = _send_queue

    write_to_log("Run.Run_worker_process: Started a new worker process.")
    # Create a worker handler using the supplied parameters
    _worker_handler = WorkerHandler(_process_id=_process_id,
                                    _parent_process_id=_parent_process_id,
                                    _send_queue=_send_queue,
                                    _repo_base_folder=_repo_base_folder)

    # Start an monitor for that the inbound queue, specify handler
    _worker_monitor = Monitor(_handler=_worker_handler,
                              _queue=_queue)

    # Run until terminated
    while not _worker_handler.terminated:
        time.sleep(0.1)

    write_to_log("Run.Run_worker_process: Exiting worker process.")

