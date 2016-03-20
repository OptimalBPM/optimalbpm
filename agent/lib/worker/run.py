"""
This modules sole purpose is providing a starting point for running worker processes.
"""

import os
import time

import of.common.logging
from of.common.logging import category_identifiers, severity_identifiers, write_to_log
from of.common.queue.monitor import Monitor

__author__ = 'Nicklas Borjesson'

send_queue = None
process_id = None
adress = None

from optimalbpm.agent.lib.worker.handler import WorkerHandler

def log_to_queue(_data, _category, _severity, _process_id_param, _occurred_when, _uid, _pid):
    if _process_id_param is not None:
        _process_id_param = process_id
    global send_queue, process_id
    _event = (
        {
            "data": _data,
            "category": category_identifiers[_category],
            "severity": severity_identifiers[_severity],
            "uid": _uid,
            "pid": _pid,
            "occurredWhen": _occurred_when,
            "address": adress,
            "process_id": _process_id_param,
            "schemaRef": "of://event.json"
        }
    )
    send_queue.put(_event)

def run_worker_process(_parent_process_id, _process_id, _queue, _send_queue, _repo_base_folder, _severity, _address):
    """
    This function is the first thing that is called when the worker process is initialized

    :param _parent_process_id: The process_id of the parent process.
    :param _process_id: The process id of this worker
    :param _queue: The instance of multiprocess queue on which the worker expects process messages to appear.
    :param _send_queue: The queue the process uses for external communication
    :param _repo_base_folder: The repository base folder.
    """

    global send_queue, address, process_id

    of.common.logging.callback = log_to_queue
    of.common.logging.severity = _severity
    address = _address
    process_id = _process_id

    write_to_log("Run.Run_worker_process: Started a new worker process.")
    # Create a worker handler using the supplied parameters
    _worker_handler = WorkerHandler(_process_id=_process_id,
                                    _parent_process_id=_parent_process_id,
                                    _send_queue=_send_queue,
                                    _repo_base_folder=_repo_base_folder,
                                    _severity=_severity)

    # Start an monitor for that the inbound queue, specify handler
    _worker_monitor = Monitor(_handler=_worker_handler,
                              _queue=_queue)

    # Run until terminated
    while not _worker_handler.terminated:
        time.sleep(0.1)

    write_to_log("Run.Run_worker_process: Exiting worker process.")

