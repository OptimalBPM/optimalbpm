"""
The process handler module implements the ProcessHandler class
"""

import datetime
import multiprocessing
import os
from multiprocessing import Process
import time
import queue

from bson.objectid import ObjectId

from of.common.messaging.factory import log_process_state_message, reply_with_error_message, get_current_login
from optimalbpm.broker.messaging.factory import bpm_process_control, worker_process_control, get_current_login
from of.common.queue.handler import Handler
from optimalbpm.agent.lib.worker.run import run_worker_process
from of.schemas.constants import zero_object_id


__author__ = 'Nicklas Borjesson'


class WorkerSupervisor(Handler):
    """
    The Worker supervisor is responsible for managing the worker processes and their messaging.
    It also is responsible for queueing incoming jobs.

    """
    #: A dictionary with all workers, their keys are their process_id is key.
    workers = None
    #: A list of available workers
    available_workers = None
    #: A dictionary with the busy (currently running BPM processes) workers, their keys are their process_id is key.
    busy_workers = None

    #: A queue with processes that haven't been able to be run yet due to lack of available workers.
    job_queue = None
    #: The maximum allowed number of worker processes
    max_worker_count = None

    #: The base folder for all source repositories
    repo_base_folder = None

    #: The monitor of the queue that this handler gets its commands from.
    monitor = None

    #: The main agent message monitor
    message_monitor = None

    #: Statistic: Total jobs run
    total_jobs_run = None

    def __init__(self, _process_id, _repo_base_folder, _message_monitor, _max_worker_count=None):
        """
        Initates a WorkerSupervisor, initiates the queue and creates a function map.
        :param _process_id: The id of the process
        :param _repo_base_folder: The base folder for the repository
        :param _message_monitor: The main agent message monitor
        :param _max_worker_count:  The maximum allowed number of worker processes
        """
        super(WorkerSupervisor, self).__init__(_process_id)

        self.busy_workers = {}
        self.workers = {}
        self.available_workers = []

        if _max_worker_count:
            self.max_worker_count = _max_worker_count
        else:
            self.max_worker_count = 6

        self.job_queue = queue.Queue()
        self.schema_id__handler = {
            "bpm://message_bpm_process_start.json": self.handle_bpm_process_start
        }
        self.repo_base_folder = _repo_base_folder

        self.message_monitor = _message_monitor
        self.message_monitor.handler.process_handler = self

        self.total_jobs_run = 0

    def on_monitor_init(self, _monitor):
        """
        Is called by the queue monitor that calls this handler when its queue gets new items
        :param _monitor: A queue monitor
        """
        # Make the handler aware of
        self.monitor = _monitor

    def initialize_worker(self):
        """
        Initialize a new worker process
        """

        # Start a worker process
        # TODO: Look at RunAs and similar to run in context (PROD-26)

        _new_process_id = str(ObjectId())
        _new_queue_manager = multiprocessing.Manager()
        _new_queue = _new_queue_manager.Queue()

        _new_process = Process(target=run_worker_process, daemon=False,  # is in documentation, not skeleton
                               args=(self.process_id, _new_process_id, _new_queue,
                                     self.monitor.queue, self.repo_base_folder))

        print(self.log_prefix + "Calling worker process start.")
        _new_process.start()
        _new_worker = {
            "queue": _new_queue,
            "pid": _new_process.pid,
            "process": _new_process,
            "processId": _new_process_id,
            "spawnedWhen": str(datetime.datetime.utcnow()),
        }

        # Report worker process instance to server
        self.message_monitor.queue.put([None, {
            "_id": _new_process_id,
            "parent_id": self.process_id,
            "spawnedBy": get_current_login(),
            "systemPid": _new_process.pid,
            "spawnedWhen": _new_worker["spawnedWhen"],
            "name": "Worker process",
            "schemaRef": "of://process_system.json"
        }])

        self.workers[_new_process_id] = _new_worker
        return _new_worker

    def acquire_worker(self, _process_id):
        """
        Acquire an available worker process for executing a BPM process, if needed and possible, create a new one.
        If successful, the process is added to busy_workers and returned, if not, return none.

        :param _process_id: The BPM process Id
        :return Returns a worker if possible, otherwise none
        """

        if len(self.available_workers) > 0:
            # There are available workers, take one
            _worker = self.available_workers.pop()
            print(self.log_prefix + "Process " + str(_process_id) + ": Found available worker.")
        elif len(self.available_workers) + len(self.busy_workers) < self.max_worker_count:
            # There are no available workers, and we have not yet reached the maximum number of allowed workers
            _worker = self.initialize_worker()
            print(self.log_prefix + "Process " + str(_process_id) + ": Started new worker.")
        else:
            # There were no workers available
            return None

        self.busy_workers[_process_id] = _worker

        # Update worker information
        _worker["busy_since"] = datetime.datetime.utcnow()
        _worker["bpm_process_id"] = _process_id

        return _worker

    def release_worker(self, _process_id):
        """
        Release a worker that is not needed.
        If there is any more work on the queue, re-use the worker.
        :param _process_id: The BPM process id of the finished BPM process
        """

        if _process_id in self.busy_workers:
            _worker = self.busy_workers[_process_id]
        else:
            raise Exception(self.log_prefix + "release_worker - Invalid processId :" + _process_id)

        self.total_jobs_run += 1
        print(self.log_prefix + "Releasing worker process " + _worker["processId"] + " from " + _process_id +
              ". Jobs run: " + str(self.total_jobs_run))

        # Remove the worker from the list of busy workers
        del self.busy_workers[_process_id]
        # A worker has just become available, reuse for the next job.
        try:
            _next_job = self.job_queue.get(block=False)
            # If there is a job run it
            print(self.log_prefix + "Re-using worker process for " + _next_job["processId"])
            self.busy_workers[_next_job["processId"]] = _worker
            _worker["queue"].put(_next_job)
        except queue.Empty:
            # There was no job on the queue, make the worker available.
            self.available_workers.append(_worker)

    def handle_bpm_process_start(self, _message_data):
        """
        Handle and act on BPM process start messages.
        :param _message_data: The start message
        """
        print(self.log_prefix + "BPM Process(definition: " + _message_data[
            "processDefinitionId"] + "): Looking for a worker.")
        _worker = self.acquire_worker(_message_data["processId"])
        if _worker:
            # Add the message to its queue
            print(
                self.log_prefix + "BPM Process " + _message_data["processId"] +
                ": Putting the message on the workers' queue.")

            _worker["queue"].put(_message_data)
        else:
            # There was no available worker, put the job on the queue
            self.job_queue.put(_message_data)
            self.message_monitor.queue.put([None,
                                            log_process_state_message(
                                                _changed_by=zero_object_id,
                                                _state="queued",
                                                _process_id=_message_data["processId"],
                                                _reason="Queued until a worker becomes available")]
                                           )

            print(self.log_prefix + "BPM Process(definition: " + _message_data[
                "processDefinitionId"] + "): Queued for execution when a worker becomes available. "
                                         "Max worker count limit reached.")

    def handle(self, _item):
        """
        Called when the monitor has gotten a message from a worker process
        """
        if _item[0]:
            # If the websocket is set, it is not from a worker process, raise error.
            raise Exception("The process handler only handles messages from worker processes.")
        else:

            # TODO: Should any filtering be done here? (OB1-138)
            _message_data = _item[1]
            if "schemaRef" not in _message_data:
                raise Exception(self.log_prefix + "Missing schemaRef: " + str(_message_data))

            if _message_data["schemaRef"] == "bpm://message_bpm_process_result.json":
                # A process result message implies that the worker is done and available for new jobs
                self.release_worker(_message_data["sourceProcessId"])

            elif _message_data["schemaRef"] == "of://log_process_state.json" and \
                    _message_data["processId"] in self.workers and \
                    _message_data["state"] in ["killed"]:
                # If a worker is logging that it is being killed, it should be remove from the workers
                print(self.log_prefix + "Worker " + _message_data["processId"] + " shut down, removing from workers.")
                del self.workers[_message_data["processId"]]

            print(self.log_prefix + "Forwarding " + str(_message_data))
            # Pass the message on to the message queue, heading for the last destination
            self.message_monitor.queue.put([_item[0], _item[1]])

    def forward_message(self, _message_data):
        """
        Forwards a incoming message to the proper worker process queue
        """

        if _message_data["schemaRef"] == "bpm://message_bpm_process_start.json":
            # It is a process start message, start a process
            self.handle_bpm_process_start(_message_data)
        elif _message_data["schemaRef"] == "bpm://message_bpm_process_command.json" and \
                _message_data["command"] == "kill":
            # It is a command to kill a worker, do so.
            # TODO: This part should be extracted into a function. (OB1-138)
            _worker = self.busy_workers[_message_data["destinationProcessId"]]
            print(self.log_prefix + "Kill " + str(_message_data))
            _worker["process"].terminate()

            del self.busy_workers[_message_data["destinationProcessId"]]
            del self.workers[_worker["processId"]]
            # Send first a state message for the (logical) BPM process
            self.message_monitor.queue.put([None, log_process_state_message(_changed_by=_message_data["userId"],
                                                                            _state="killed",
                                                                            _process_id=_message_data[
                                                                                "destinationProcessId"],
                                                                            _reason="Unresponsive, killed.")])
            # Then a state message for the actual worker process
            self.message_monitor.queue.put([None, log_process_state_message(_changed_by=_message_data["userId"],
                                                                            _state="killed",
                                                                            _process_id=_worker["processId"],
                                                                            _reason="Had an unresponsive BPM process")])

            print(self.log_prefix + "Killed")

        elif "destinationProcessId" not in _message_data:
            raise Exception(self.log_prefix + "Missing destinationProcessId: " + str(_message_data))
        elif _message_data["destinationProcessId"] in self.busy_workers:
            # Route the data to its destination
            # The mockup must reference in exactly the same way..
            self.busy_workers[_message_data["destinationProcessId"]]["queue"].put(_message_data)
        else:
            raise Exception(self.log_prefix + "Invalid destinationProcessId: " + _message_data["destinationProcessId"])

    def shut_down(self, _user_id):
        """
        Shuts down the worker handler and all jobs.
        :param _user_id:
        :return:
        """
        try:

            """
            TODO: First tell broker and incoming message handle we are shutting down.
            Broker should then remove agent from destinations for messaging

            Move all available workers processes to temporary list, shut them all down
            All queued jobs should be unqueued and be returned to the broker to be run elsewhere
            Pause(means do not run next step all running jobs and send states to broker where they should be queued or
            continued elsewhere

            Wait n seconds for remaining jobs to complete
            Pause all running jobs and save state to broker
            n seconds for remaining and queued jobs to complete


            """
            print(self.log_prefix + "Shutting down process handler")

            print(self.log_prefix + "Telling BPM processes to stop")
            # Send process control messages to all bpm processes
            for _process_id, _process in self.busy_workers.items():
                _process["queue"].put(bpm_process_control(_destination="",
                                                          _destination_process_id=_process_id,
                                                          _command="stop",
                                                          _reason="Shutting down agent",
                                                          _message_id=0,
                                                          _source="",
                                                          _source_process_id=self.process_id,
                                                          _user_id=_user_id))
                print(self.log_prefix + str(_process_id) + " told to stop.")

            print(self.log_prefix + "BPM processes told to shut down, waiting a bit..")

            print(self.log_prefix + "Clearing job queue")
            # Loop through job queue, remove all items, tell broker
            while True:
                try:
                    _item = self.job_queue.get_nowait()
                    print(self.log_prefix + "Job in queue:" + str(_item))
                    self.message_monitor.queue.put([None,
                                                    reply_with_error_message(self, _item,
                                                                             "Unqueued, agent shutting down.")]
                                                   )
                except queue.Empty:
                    break

            _check_count = 3
            while len(self.busy_workers) > 0 and _check_count > 0:
                print(
                    self.log_prefix + "Still running BPM processes, waiting another second before stopping "
                                      "the remaining workers. Times left:" + str(_check_count))
                time.sleep(1)
                _check_count -= 1

            print(self.log_prefix + "Telling worker processes to shut down")

            # Tell workers to shut down
            for _process in self.workers.values():
                print(self.log_prefix + "Telling worker process " + _process["processId"] + " to stop")
                _process["queue"].put(worker_process_control(_destination="",
                                                             _destination_process_id=_process["processId"],
                                                             _command="stop",
                                                             _reason="Shutting down agent",
                                                             _message_id=0,
                                                             _source="",
                                                             _source_process_id=self.process_id,
                                                             _user_id=_user_id))

            time.sleep(.1)
            # Kill the remaining processes

            for _process in list(self.workers.values()):
                print(self.log_prefix + "Killing unresponsive process " + _process["processId"] + " (pid:" + str(
                    _process["pid"]) + ")")
                _process["process"].terminate()
                self.message_monitor.queue.put([None, log_process_state_message(_changed_by=_user_id,
                                                                                _state="killed",
                                                                                _process_id=_process["processId"],
                                                                                _reason="Unresponsive, killed by agent")
                                                ])
                del self.workers[_process["processId"]]
        except Exception as e:
            print(self.log_prefix + "Failed to properly shut down, error:" + str(e))


class MockupWorkerSupervisor(WorkerSupervisor):
    #: Here the message is stored
    message = None
    #: Callback for initialization on process start
    on_process_start = None

    def forward_message(self, _message_data):
        print(self.log_prefix + str(self) + "Got a message:" + str(_message_data))
        self.message = _message_data
        if _message_data["schemaRef"] == "of://message.json":
            # This is almost a mock of code that should be tested...this must be kept matching the code.
            self.busy_workers[_message_data["destinationProcessId"]]["queue"].put(_message_data)
        if self.on_process_start:
            try:
                self.on_process_start(self, _message_data)
            except Exception as e:
                print(self.log_prefix + "Error running mockup callback" + str(e))
