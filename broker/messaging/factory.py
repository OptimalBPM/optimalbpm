"""
The factory module contains a number of functions that return message structures.
Use these function instead of building messages manually to follow changes.
"""

import datetime
import os


if os.name != "nt":
    import pwd


from bson.objectid import ObjectId



__author__ = 'Nicklas Borjesson'


def get_current_login():
    if os.name == "nt":
        return os.getlogin()
    else:
        return pwd.getpwuid(os.geteuid()).pw_name


def start_process_message(_user_id, _process_definition_id, _destination, _globals, _message_id, _reason,
                          _source_process_id=None):
    """
    Generate a start process message, used to start a BPM process
    """
    _process_message = {
        "userId": _user_id,
        "processDefinitionId": _process_definition_id,
        "destination": _destination,
        "globals": _globals,
        "processId": str(ObjectId()),
        "reason": _reason,
        "messageId": _message_id,
        "schemaRef": "bpm://message_bpm_process_start.json"
    }
    if _source_process_id:
        _process_message["sourceProcessId"] = _source_process_id
    return _process_message



def store_bpm_process_instance_message(_start_message, _worker_process_id):
    """
    Creates a BPM process instance message, used to save information about an Optimal BPM process to the back end,
    """

    _struct = {
        "_id": _start_message["processId"],
        "parent_id": _start_message["processId"],
        "workerProcessId": _worker_process_id,
        "spawnedBy": _start_message["userId"],
        "spawnedWhen": str(datetime.datetime.utcnow()),
        "processDefinitionId": _start_message["processDefinitionId"],
        "schemaRef": "bpm://process_bpm.json"
    }

    if "entryPoint" in _start_message:
        _struct["entryPoint"] = _start_message["entryPoint"]
    if "runAs" in _start_message:
        _struct["runAs"] = _start_message["runAs"]
    if "pip_packages" in _start_message:
        _struct["pipPackages"] = _start_message["pipPackages"]
    if "globals" in _start_message:
        _struct["globals"] = _start_message["globals"]
    return _struct


def log_process_message(_message, _process_id, _kind):
    """
    Creates a log message that is saved to the Optimal BPM log
    """
    return {
        "message": _message,
        "kind": _kind,
        "processId": _process_id,
        "createdWhen": str(datetime.datetime.utcnow()),
        "schemaRef": "bpm://log_process_message.json"
    }


def log_progress_message(_process_id, _progression_id, _absolute, _change, _user_id):
    """
    Creates a progress message that is save to the Optimal BPM log
    :param _process_id:
    :param _progression_id:
    :param _absolute:
    :param _change:
    :param _user_id:
    :return:
    """
    _struct = {
        "processId": _process_id,
        "progressionId": _progression_id,
        "userId": _user_id,
        "schemaRef": "of://log_progression.json"
    }
    if _absolute:
        _struct["absolute"] = _absolute

    if _change:
        _struct["change"] = _change

    return _struct


def message_bpm_process_result(_start_message, _globals, _process_id, _result):
    """
    Creates a BPM process result message, deduct most data from start message
    """
    _result = {
        "destination": _start_message["source"],
        "globals": _globals,
        "messageId": _start_message["messageId"],
        "result": _result,
        "sourceProcessId": _process_id,
        "source": _start_message["destination"],
        "createdWhen": str(datetime.datetime.utcnow()),
        "schemaRef": "bpm://message_bpm_process_result.json"
    }
    if "sourceProcessId" in _start_message:
        _result["destinationProcessId"] = _start_message["sourceProcessId"]

    return _result


def bpm_process_control(_destination, _destination_process_id, _command, _reason, _message_id, _source,
                        _source_process_id, _user_id):
    """
    Created a BPM process control message, user to tell a process to stop, kill, etcetera.
    """
    return {
        "destination": _destination,
        "destinationProcessId": _destination_process_id,
        "command": _command,
        "reason": _reason,
        "messageId": _message_id,
        "source": _source,
        "sourceProcessId": _source_process_id,
        "userId": _user_id,
        "schemaRef": "bpm://message_bpm_process_command.json"
    }


def worker_process_control(_destination, _destination_process_id, _command, _reason, _message_id, _source,
                           _source_process_id, _user_id):
    """
    Creates a worker process control message. Tells a worker process to stop, kill, etcetera.
    """
    return {
        "destination": _destination,
        "destinationProcessId": _destination_process_id,
        "command": _command,
        "reason": _reason,
        "messageId": _message_id,
        "source": _source,
        "sourceProcessId": _source_process_id,
        "userId": _user_id,
        "schemaRef": "bpm://message_worker_process_command.json"
    }


def agent_control(_destination, _destination_process_id, _command, _reason, _message_id, _source,
                  _source_process_id, _user_id):
    """
    Creates a worker process control message. Tells a worker process to stop, kill, etcetera.
    """
    return {
        "destination": _destination,
        "destinationProcessId": _destination_process_id,
        "command": _command,
        "reason": _reason,
        "messageId": _message_id,
        "source": _source,
        "sourceProcessId": _source_process_id,
        "userId": _user_id,
        "schemaRef": "bpm://message_agent_control.json"
    }
