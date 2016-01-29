import json
import os
import time

from behave import *

from nose.tools.trivial import ok_

from optimalbpm.broker.messaging.factory import bpm_process_control

use_step_matcher("re")

_last_message_id = 0


def getNextMessageId():
    global _last_message_id
    _last_message_id += 1
    return _last_message_id


def on_blocking_message(_socket, _message):
    print("on_blocking_message : " + str(_message))
    _socket.context.schema_tools.validate(_message)
    if _message["schemaRef"] == "of://log_progression.json" and \
                    _message["processId"] == _socket.context.blocking_process_id:
        _socket.context.test_blocking_bpm_process_progress = True
    elif _message["schemaRef"] == "of://log_process_state.json" and \
                    _message["processId"] == _socket.context.blocking_process_id and \
                    _message["state"] == "running":
        _socket.context.test_blocking_bpm_log_process_state = True
    elif _message["schemaRef"] == "of://log_process_state.json" and \
                    _message["processId"] == _socket.context.blocking_process_id and \
                    _message["state"] == "stopped":
        _socket.context.test_message_bpm_process_stop_success = True
    elif _message["schemaRef"] == "of://log_process_state.json" and \
                    _message["processId"] == _socket.context.blocking_process_id and \
                    _message["state"] == "killed":
        _socket.context.test_message_bpm_process_kill_success = True


def on_message(_socket, _message):
    print("on_message : " + str(_message))
    _socket.context.schema_tools.validate(_message)

    if _message["schemaRef"] == "of://process_system.json":
        _socket.context.test_worker_process_instance = True
    elif _message["schemaRef"] == "bpm://process_bpm.json" and \
                    _message["_id"] == _socket.context.first_process_id:
        _socket.context.test_bpm_process_instance = True
    elif _message["schemaRef"] == "of://log_process_state.json" and _message["state"] == "running" and \
                    _message["processId"] == _socket.context.first_process_id:
        _socket.context.test_bpm_process_state_running = True
    elif _message["schemaRef"] == "bpm://log_process_message.json" and _message["message"] == "message from print_globals" \
            and _message["processId"] == _socket.context.first_process_id:
        _socket.context.test_bpm_process_message = True
    # Reply by starting a new process
    elif _message["schemaRef"] == "bpm://message_bpm_process_result.json" \
            and _message["sourceProcessId"] == _socket.context.first_process_id \
            and _message["result"] == "result":
        _socket.context.test_message_bpm_process_result = True
        _socket.context.message = {
            "userId": _socket.context.user["_id"],
            "processDefinitionId": "5564bca7a5cb644b68801b94",
            "destination": "agent_peer",
            "globals": {"global_variable": "global_variable value"},
            "entryPoint": {"moduleName": "long_running"},
            "processId": _socket.context.second_process_id,
            "runAs": "someoneelse",
            "sourceProcessId": str(_socket.context.process_process_id),
            "messageId": getNextMessageId(),
            "source": "broker_peer",
            "schemaRef": "bpm://message_bpm_process_start.json"
        }

        _socket.received_message(json.dumps(_socket.context.message))
        _socket.context.test_bpm_process_second_start = True

    elif _message["schemaRef"] == "bpm://log_process_message.json" and _message["message"] == "second process log" \
            and _message["processId"] == _socket.context.second_process_id:
        _socket.context.test_bpm_process_second_log = True
        _socket.context.message = {
            "userId": _socket.context.user["_id"],
            "processDefinitionId": "5564bca7a5cb644b68801b94",
            "destination": "agent_peer",
            "globals": {"global_variable": "global_variable value"},
            "runAs": "someoneelse",
            "processId": _socket.context.third_process_id,
            "sourceProcessId": str(_socket.context.process_process_id),
            "messageId": getNextMessageId(),
            "source": "broker_peer",
            "schemaRef": "bpm://message_bpm_process_start.json"
        }

        _socket.received_message(json.dumps(_socket.context.message))
        _socket.context.test_bpm_process_third_start = True
    elif _message["schemaRef"] == "bpm://message_bpm_process_result.json" \
            and _message["sourceProcessId"] == _socket.context.third_process_id \
            and _message["globals"]["result"] == "main result":
        _socket.context.test_message_bpm_third_process_result = True

        _socket.context.message = bpm_process_control(_destination="agent_peer",
                                                      _destination_process_id=str(_socket.context.second_process_id),
                                                      _command="stop",
                                                      _reason="testing",
                                                      _source="broker_peer",
                                                      _message_id=getNextMessageId(),
                                                      _source_process_id=str(_socket.context.process_process_id),
                                                      _user_id=_socket.context.user["_id"])

        _socket.received_message(json.dumps(_socket.context.message))
        _socket.context.test_message_bpm_process_second_stop = True
    elif (_message["schemaRef"] == "of://log_process_state.json" and \
                      _message["state"] == "stopped" and \
                      _message["processId"] == _socket.context.second_process_id):
        _socket.context.test_message_bpm_process_second_stopped = True
    else:
        print("Ignoring the message type in message:" + str(_message))

@given("a process start message is sent to control monitor")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    print("\n\nA BPM process is run and a worker is reused\n==================================================\n")
    context.broker_socket.on_message = on_message
    context.message = {
        "userId": context.user["_id"],
        "processDefinitionId": "5564bca7a5cb644b68801b94",
        "destination": "agent_peer",
        "globals": {"global_variable": "global_variable value"},
        "entryPoint": {"moduleName": "functions", "functionName": "print_globals_function"},
        "processId": context.first_process_id,
        "runAs": "someoneelse",
        "sourceProcessId": str(context.process_process_id),
        "messageId": getNextMessageId(),
        "source": "broker_peer",
        "schemaRef": "bpm://message_bpm_process_start.json"
    }

    context.broker_socket.received_message(json.dumps(context.message))


@then("a worker process instance message should be received by broker socket")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    if os.name == "nt":
        time.sleep(2.6)
    else:
        time.sleep(.6)

    ok_(context.test_worker_process_instance)


@step("a bpm process instance message should be received by broker socket")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.test_bpm_process_instance)


@step("a process running state message should be received by broker socket")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    ok_(context.test_bpm_process_state_running)


@step("a log message from the process should be received by the broker socket")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.test_bpm_process_message)


@step("a process result message from the process should be received by the broker socket")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.test_message_bpm_process_result)


@step("a different process start message is sent to the control monitor")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.test_message_bpm_process_result)


@step("a second process start message is sent to the control monitor")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.test_bpm_process_second_start)


@step("a log message from the second process should be received by the broker socket")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.test_bpm_process_second_log)


@step("a third process start message is sent to the control monitor")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.test_bpm_process_third_start)


@step("a third process result message should be received by the broker socket")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    ok_(context.test_message_bpm_third_process_result)


@step("a process stop message should be sent to the second process")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.test_message_bpm_process_second_stop)


@step("a second process running state stopped message should be received by the socket")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    ok_(context.test_message_bpm_process_second_stopped)


@given("a blocking process start message is sent to control monitor")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    print("\n\nA running BPM process has to be killed\n==================================================\n")
    context.broker_socket.on_message = on_blocking_message
    context.message = {
        "userId": context.user["_id"],
        "processDefinitionId": "5564bca7a5cb644b68801b94",
        "destination": "agent_peer",
        "globals": {"global_variable": "global_variable value"},
        "entryPoint": {"moduleName": "block"},
        "processId": context.blocking_process_id,
        "runAs": "someoneelse",
        "sourceProcessId": str(context.process_process_id),
        "messageId": getNextMessageId(),
        "source": "broker_peer",
        "schemaRef": "bpm://message_bpm_process_start.json"
    }

    context.broker_socket.received_message(json.dumps(context.message))
    time.sleep(0.1)
    ok_(True)


@step("a process progress message should be received by broker socket")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    ok_(context.test_blocking_bpm_process_progress)


@step("the broker should send a process stop message to the worker")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    ok_(context.test_blocking_bpm_log_process_state)
    context.message = bpm_process_control(_destination="agent_peer",
                                          _destination_process_id=str(context.blocking_process_id),
                                          _command="stop",
                                          _reason="testing",
                                          _source="broker_peer",
                                          _message_id=getNextMessageId(),
                                          _source_process_id=str(context.process_process_id),
                                          _user_id=context.user["_id"])
    context.test_message_bpm_process_stop_success = None
    context.broker_socket.received_message(json.dumps(context.message))
    time.sleep(0.1)
    ok_(True)


@step("the broker should not receive a success message")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(not context.test_message_bpm_process_stop_success)


@step("the broker should send a process kill message to the worker")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    context.message = bpm_process_control(_destination="agent_peer",
                                          _destination_process_id=str(context.blocking_process_id),
                                          _command="kill",
                                          _reason="testing",
                                          _source="broker_peer",
                                          _message_id=getNextMessageId(),
                                          _source_process_id=str(context.process_process_id),
                                          _user_id=context.user["_id"])

    context.broker_socket.received_message(json.dumps(context.message))
    time.sleep(0.1)
    ok_(True)


@step("the broker should receive a process state killed message")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.test_message_bpm_process_kill_success)
