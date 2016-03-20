"""
This modules sole purpose is providing a starting point for running worker processes.
"""

import os
import time


from of.common.queue.monitor import Monitor

__author__ = 'Nicklas Borjesson'

from plugins.optimalbpm.agent.lib.worker.handler import WorkerHandler


def run_worker_process(_parent_process_id, _process_id, _queue, _send_queue, _repo_base_folder):
    """
    This function is the first thing that is called when the worker process is initialized

    :param _parent_process_id: The process_id of the parent process.
    :param _process_id: The process id of this worker
    :param _queue: The instance of multiprocess queue on which the worker expects process messages to appear.
    :param _send_queue: The queue the process uses for external communication
    :param _repo_base_folder: The repository base folder.
    """

    print(str(os.getpid()) + "-Run.Run_worker_process: Started a new worker process.")

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

    print(str(os.getpid()) + "-Run.Run_worker_process: Exiting worker process.")
