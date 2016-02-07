import sys
import os
import time

import copy
import json
import logging
import importlib
from importlib._bootstrap import ModuleSpec, SourceFileLoader
import runpy

from threading import Thread
import threading
from types import FunctionType, MethodType, ModuleType

from of.common.internal import not_implemented
from of.common.messaging.factory import reply_with_error_message, log_process_state_message
from plugins.optimalbpm.broker.messaging.factory import store_bpm_process_instance_message, log_progress_message, \
    message_bpm_process_result, log_process_message
from of.common.messaging.utils import message_is_none
from of.common.queue.handler import Handler


__author__ = 'Nicklas Borjesson'


class BPMTread(Thread):
    """
    This class adds BPM-specific information to the thread class
    """
    #: The user_id
    user_id = None

    #: The message that started the thread
    start_message = None

    #: The message that terminated the thread
    termination_message = None

    #: If true, the thread is terminated
    terminated = None

    def __init__(self, target, name, args, _user_id, _start_message):
        self.terminated = False
        self.user_id = _user_id
        self.start_message = _start_message
        super(BPMTread, self).__init__(target=target, name=name, args=args)


class TerminationException(Exception):
    """
    This exception is raised inside a job when the worker has gotten a message saying that the job is supposed to stop.
    """
    #: The global variables at the time of the exception
    globals = None


class WorkerHandler(Handler):
    """
    This is the message handler of a worker process.
    It is responsible for all worker messaging
    """
    #: The process handler send queue, used for outbound messages
    send_queue = None
    #: It truthy, a job is running
    job_running = None
    #: The parent processId of the worker
    parent_process_id = None
    #: The thread in which the BPM process runs
    bpm_process_thread = None
    #: The base folder of the repository, the base of all references
    repo_base_folder = None
    #: The worker has been terminated
    terminated = None
    #: The monitor of the worker handlers' inbound queue
    monitor = None

    #: The path of the script
    script_path = None
    #: The processId of the BPM process
    bpm_process_id = None
    #: The source peer of the BPM process, the initiator
    bpm_source = None

    def __init__(self, _process_id, _parent_process_id, _send_queue, _repo_base_folder):
        """
        Initializer the handler, set all parameters
        :param _process_id: The processId of the worker
        :param _parent_process_id: The parent processId of the worker
        :param _send_queue: The process handler send queue
        :param _repo_base_folder:
        :return:
        """
        super(WorkerHandler, self).__init__(_process_id)
        self.send_queue = _send_queue
        self.repo_base_folder = _repo_base_folder
        self.parent_process_id = _parent_process_id
        self.terminated = False
        self.bpm_terminated = False
        self.log_prefix = self.log_prefix

    def on_monitor_init(self, _monitor):
        """
        Called when the monitor initiates
        :param _monitor: An instance of a queue monitor

        """
        self.monitor = _monitor

    def handle(self, _message):
        """
        Handles all incoming messages to the process handler on the monitor queue.

        :param _message: A message
        """
        _message_data = _message
        print(self.log_prefix + "Worker process got a message:" + str(_message_data))

        if _message_data["schemaRef"] == "bpm://message_bpm_process_start.json":
            # The message is a process start message,start a process.
            if self.job_running:
                # If the worker has a job currently running, reply with an error message and do nothing
                # TODO: This message should probably be handled in some way by the agent (PROD-28)
                self.send_queue.put([None, reply_with_error_message(self, _message_data,
                                                                    "Worker.handle_message: Cannot start BPM Process, process " + str(
                                                                        self.bpm_process_id) + " already running.")])
            else:
                print(self.log_prefix + "Starting BPM process")
                self.start_bpm_process(_message=_message_data)

        elif _message_data["schemaRef"] == "bpm://message_bpm_process_command.json":
            # The message is a command to the bpm process
            print(self.log_prefix + "Got a BPM process control message:" + _message_data["command"])
            if _message_data["command"] == "stop":
                # Told to stop. Stopping process.
                # TODO: Break out BPM process termination, should be done in worker termination as well. (PROD-27)
                # TODO: The broker should be able to offer the users the option to retry running the process (PROD-28)
                print(self.log_prefix + "XXXXXXXXXXXX-Telling thread to terminate, script :" + str(self.script_path))
                self.bpm_process_thread.termination_message = _message_data
                self.bpm_process_thread.terminated = True
                # TODO: Implement "pause" (PROD-29)

        elif _message_data["schemaRef"] == "bpm://message_worker_process_command.json":
            # The message is a command to the actual worker process
            if _message_data["command"] == "stop":
                # Told to stop the worker. Stopping process.

                print(self.log_prefix + "Told to stop the worker.")
                # First stop the monitor, we don't want any more commands coming in.
                self.monitor.stop()

                # TODO: First stop the bpm process thread. (PROD-27)

                print(self.log_prefix + "Worker monitor stopped.")
                self.send_queue.put([None, log_process_state_message(
                    _changed_by=message_is_none(_message_data, "userId", "No user mentioned"),
                    _state="stopped",
                    _process_id=self.process_id,
                    _reason=message_is_none(_message_data, "reason", "No reason mentioned"))])
                print(self.log_prefix + "Reported stopping to process handler")
                self.terminated = True
            else:
                print(self.log_prefix + "Unhandled command " + _message_data["command"])

        elif _message_data["schemaRef"] == "of://message":
            #: TODO: Figure out if processes should just ever get general messages, and if so, how to handle?(PROD-30)
            self.message = _message_data
            print(self.log_prefix + "Got a message:" + self.message)

    """
    The following functions are imported into BPM process modules. They can then be used from within these modules.
    """

    def log_progress(self, _progression_id, _change, _absolute):
        """
        Send a progress log message to the broker.

        :param _progression_id: The id pf the progression
        :param _change: If set, the value will change by this number
        :param _absolute: If set, the value will be set to this number

        """
        self.send_queue.put([None,
                             log_progress_message(_process_id=self.bpm_process_id,
                                                  _progression_id=_progression_id,
                                                  _change=_change,
                                                  _absolute=_absolute,
                                                  _user_id=self.bpm_process_thread.user_id)])

    def pause(self, _duration):
        """
        Pause execution for duration (not to be confused with the pausing of the process, perhaps wait is a better name)
        :param _duration: Time in seconds
        :return:
        """
        time.sleep(_duration)



    def report_result(self, _globals, _result):
        """
        Send a process result message to the destination

        :param _globals: The globals as set when the process returns
        :param _result: If from a function call, the result is stored here.
        """
        if _globals:
            _globals = self.sanitize_result(_globals)
        else:
            _globals = {}

        self.send_queue.put([None, message_bpm_process_result(_start_message=self.bpm_process_thread.start_message,
                                                              _process_id=self.bpm_process_id,
                                                              _globals=_globals,
                                                              _result=_result)])

    def log_message(self, _message, _kind):
        """
        Send a log message to the broker.

        :param _message: Message
        :param _kind: Kind (Info/Warning/Error
        :return:
        """
        self.send_queue.put([None, log_process_message(_message=_message,
                                                       _kind=_kind,
                                                       _process_id=self.bpm_process_id)])

    @staticmethod
    def sanitize_result(_globals):
        """
        Sanitize result globals from modules to remove irrelevant and unserializeable data

        :param _globals: The dict to sanitize
        :return: sanitized global
        """
        _result = copy.copy(_globals)
        for _key, _value in _globals.items():

            if (isinstance(_value, (FunctionType, MethodType, ModuleType, ModuleSpec, SourceFileLoader)) or
                    (_key[0:2] == "__" and _key[-2:2] == "__")):
                del _result[_key]
            elif isinstance(_value, (str, int, float)):
                pass
            elif _key == "__cached__":
                del _result[_key]
            else:
                # And it is not any of the base types
                try:
                    json.dumps(_value)
                except Exception:
                    del _result[_key]

        return _result

    def report_termination(self, _globals):
        """
        Reports termination of a BPM process.
        :param _globals: The current globals of the BPM process
        """
        # Stop tracing
        sys.settrace(None)
        print(self.log_prefix + "XXXXXXXXXXXX-Script has been stopped: " + self.script_path + ".")
        # Send stopped running state to broker.
        self.send_queue.put([None, log_process_state_message(
            _changed_by=self.bpm_process_thread.user_id,
            _state="stopped",
            _reason=self.bpm_process_thread.termination_message["reason"],
            _process_id=self.bpm_process_id)])

        # Create a return value for the caller
        return {"bpm_error":
            {
                "exception": TerminationException,
                "message": "The process was stopped, reason:" +
                           self.bpm_process_thread.termination_message["reason"],
                "globals": self.sanitize_result(_globals)
            }
        }

    def report_error(self, _error, e):
        """
        Report an error from inside a BPM process.
        :param _error:
        :param e:
        :return:
        """
        # Stop tracing
        sys.settrace(None)

        print(_error)
        # Send failed running state to broker.
        self.send_queue.put([None, log_process_state_message(
            _changed_by=self.bpm_process_thread.user_id,
            _state="failed",
            _reason=_error,
            _process_id=self.bpm_process_id)])

        # Create a return value for the caller
        return {"bpm_error":
            {
                "exception": str(type(e)),
                "message": _error
            }
        }

    def report_finished(self):
        """
        Report that a BPM process has finished successfully
        """
        # Stop tracing
        sys.settrace(None)
        # Send finished running state to broker.
        self.send_queue.put([None, log_process_state_message(
            _changed_by=self.bpm_process_thread.user_id,
            _state="finished",
            _reason="Process finished successfully",
            _process_id=self.bpm_process_id)])

    def run_module(self, _module_name, _globals):
        """
        Run a BPM process module

        :param _module_name: Full path to the model.
        :param _globals: The globals.

        """
        print(self.log_prefix + "->>>>>>>>>>>> Running module " + _module_name + ", globals: " + str(_globals))

        try:
            # Call the run_module, it returns the globals after execution
            _new_globals = runpy.run_module(mod_name=_module_name, init_globals=_globals)
        except TerminationException as e:
            print("TerminationException running the process:" + str(e))
            # The process was terminated
            _result = self.report_termination(_globals)
            _new_globals = _globals

        except Exception as e:
            # An unhandled error occured running the process
            print("Error running the process:" + str(e))
            _result = self.report_error(self.log_prefix + "Error in module " + _module_name + ".py:" + str(e), e)
            _new_globals = None
        else:
            # The process ended normally
            self.report_finished()
            # A module has no return value
            _result = None

        print(self.log_prefix + "<<<<<<<<<<<<- Done calling " + self.script_path + ".")
        self.report_result(_globals=_new_globals, _result=_result)

        self.job_running = False

    def run_function(self, _function):
        """
        Call a BPM process function

        :param _function: A reference to a function object

        """

        print(self.log_prefix + "->>>>>>>>>>>>Running function " + _function.__module__ + ", globals: " + str(
            _function.__globals__))

        try:
            # Call the function
            _result = _function()
        except TerminationException:
            # The BPM process was terminated
            _result = self.report_termination(_function.__globals__)
        except Exception as e:
            # An unhandled error occured running the BPM process
            _result = self.report_error(
                self.log_prefix + "Error in function " + _function.__module__ + ".py: " + "." + \
                _function.__name__ + " - Error class:" + e.__class__.__name__ + " Error: " + str(e), e)

        else:
            # The process ended normally
            # Stop tracing
            sys.settrace(None)
            self.report_finished()

        print(self.log_prefix + "<<<<<<<<<<<<-Done running " + self.script_path + ".")

        self.report_result(_globals=_function.__globals__, _result=_result)
        self.job_running = False

    def trace_calls(self, frame, event, arg):
        """
        This function traces the execution of optimal BPM process code.

        :param frame: The frame
        :param event: The type of event
        :param arg: Unused (compat)

        """

        if self.bpm_process_thread.terminated:
            sys.settrace(None)
            raise TerminationException(
                self.log_prefix + "The script has been told to terminate." + self.script_path)

        else:
            return self.trace_calls

        # TODO: Implement breaking functionality (PROD-29)
        # TODO: Implement pausing functionality (PROD-29)
        # TODO: Implement stepping functionality (PROD-29)

        """
        # This is to implement breaking, pausing, and stepping functionality
        caller = frame.f_back
        caller_line_no = caller.f_lineno
        caller_filename = caller.f_code.co_filename

        if caller_filename != self.script_path:
            return self.trace_calls

        co = frame.f_code

        # Only trace function calls

        func_name = co.co_name

        # if event == "line":
        #    print("line " + str(co))



        elif event == "call":
            frame.f_locals["bpm_start_time"] = time.perf_counter()
            print(co.co_name + " was called at " + time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()))
            print("locals/arguments: " + str(frame.f_locals))
            return self.trace_calls
        elif event == "return":
            delta = time.perf_counter() - frame.f_locals["bpm_start_time"]
            print(co.co_name + " returned after " + str(delta * 100000) + " ms.")

        return self.trace_calls


        if int(caller_line_no) > _termination_line:
            sys.settrace(None)

        """
        return self.trace_calls

    def start_bpm_process(self, _message):
        """
        Initializes and starts a BPM process based on the content of the message

        :param _message: A message_bpm_process_start-message
        """
        try:

            # Extract caller information

            self.bpm_process_id = _message["processId"]
            self.bpm_source = str(message_is_none(_message, "source", ""))

            # Execution context

            _entry_point = message_is_none(_message, "entryPoint", None)
            _globals = message_is_none(_message, "globals", {})

            # Add repository location to sys,path to be able to import
            _source_path = os.path.join(os.path.expanduser(self.repo_base_folder), _message["processDefinitionId"])
            sys.path.append(_source_path)

            print(self.log_prefix + "Source path: " + _source_path)

            if _entry_point:
                # If there is an entry point, it is a function call
                _module_name = _entry_point["moduleName"]
                if "functionName" in _entry_point:
                    _module = importlib.import_module(_module_name)
                    _function_name = _entry_point["functionName"]
                    print(self.log_prefix + "In start_bpm_process, initializing: " + str(_message))

                    # Find function
                    _function = getattr(_module, _function_name)

                else:
                    _function = None
            else:
                # If there is no entry point, it is a module
                _module_name = "main"
                _function = None

            self.script_path = os.path.join(_source_path, _module_name + ".py")
            # Send an instance message to the broker. This tells the broker that a worker has instantiated a process.
            self.send_queue.put(
                [None, store_bpm_process_instance_message(_start_message=_message, _worker_process_id=self.process_id)])

            print(self.log_prefix + "In start_bpm_process, initializing of " + self.script_path + " done.")
        except Exception as e:
            _error_message = self.log_prefix + "error initiating BPM process. processDefinitionId: " + \
                             message_is_none(_message, "processDefinitionId", "not set") + \
                             ", process_id: " + message_is_none(_message, "processId", "not set") + \
                             ", Error: " + str(e)
            print(_error_message)

            self.send_queue.put([None, reply_with_error_message(self, _message, _error_message)])

        else:
            try:
                _thread_name = "BPM Process " + self.bpm_process_id + " thread"
                # Add callbacks to scope
                _globals.update(
                    {
                        "report_error": self.report_error,
                        "report_result": self.report_result,
                        "log_progress": self.log_progress,
                        "log_message": self.log_message,
                        "pause": self.pause
                    }
                )

                if _function:
                    _function.__globals__.update(_globals)
                    self.bpm_process_thread = BPMTread(target=self.run_function,
                                                       name=_thread_name, args=[_function],
                                                       _user_id=_message["userId"],
                                                       _start_message=_message)
                else:
                    self.bpm_process_thread = BPMTread(target=self.run_module,
                                                       name=_thread_name,
                                                       args=[_module_name, _globals],
                                                       _user_id=_message["userId"],
                                                       _start_message=_message)

                # Send running state.
                if "reason" in _message:
                    _reason = _message["reason"]
                else:
                    _reason = "No reason"
                self.send_queue.put([None, log_process_state_message(
                    _changed_by=self.bpm_process_thread.user_id,
                    _state="running",
                    _process_id=self.bpm_process_id,
                    _reason=_reason)])

                threading.settrace(self.trace_calls)
                self.bpm_process_thread.start()

            except Exception as e:
                self.logging_function(self.log_prefix + "error initiating module " +
                                      self.script_path + '.run() - ' + str(e), logging.ERROR)


class WorkerHandlerMockup(WorkerHandler):
    """
    Used for testing purposes, only sets the message property for the framework to test messaging.
    """

    #: A place to store the message when testing messaging
    message = None

    def handle(self, _message):
        """
        Handles incoming messages and sets the message property
        :param _message: A message
        """
        _message_data = _message
        if _message_data["schemaRef"] == "of://message.json":
            self.message = _message_data
            print(self.log_prefix + "Got this data:" + str(_message_data))
