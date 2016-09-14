import datetime
import json
import time

from behave import *
from bson.objectid import ObjectId
from nose.tools.trivial import ok_
from of.common.messaging.factory import log_process_state_message

from plugins.optimalbpm.broker.messaging.factory import start_process_message

use_step_matcher("re")

message_id = 0

def getNextMessageId():
    global message_id
    message_id+= 1
    return message_id

def on_destination_process_control_message(web_socket, message):
    print("\non_destination_process_control_message: " + str(message))
    if message['schemaRef'] == "ref://bpm.message.bpm.process.start":
        # This is the first start process, respond with process instance
        web_socket.context.process_id = message['processId']
        web_socket.received_message(json.dumps(
            {
                "processId": web_socket.context.process_id,
                "spawnedBy": web_socket.context.user["_id"],
                "spawnedWhen": str(datetime.datetime.utcnow()),
                "name": "Test_process_name",
                "processDefinitionId": message["processDefinitionId"],
                "schemaRef": "ref://bpm.process.bpm"
            })
        )

        for _state in ["running", "paused", "stopped", "killed", "failed", "finished"]:
            print("Send :" + _state)
            web_socket.received_message(json.dumps(log_process_state_message(_changed_by=web_socket.context.user["_id"],
                                                      _state= _state, _reason="testing",
                                                      _process_id=web_socket.context.process_id)
                                        ))

        web_socket.received_message(json.dumps(
            {
                "destination": "source_peer" ,
                "processId": web_socket.context.process_id,
                "schemaRef": "ref://bpm.message.bpm.process.result",
                "sourceProcessId": web_socket.context.process_id,
                "messageId": getNextMessageId(),
                "source": "destination_peer",
                "globals" : {"context": "context"},
                "result" : {"result": "result"}
            })
        )

def on_source_process_control_message(web_socket, message):
    print("\non_source_process_control_message: " + str(message))
    if message['schemaRef'] == "ref://bpm.message.bpm.process.result":
        web_socket.context.tests_ended = time.perf_counter()
        web_socket.context.process_result = message


@given("an example process is started")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    context.tests_started = time.perf_counter()
    context.receiver.on_message = on_destination_process_control_message
    context.sender.on_message = on_source_process_control_message
    # The definition below was saved by having the first step of the process definitions tests as first step.
    context.original_definition = context.node.find({"name": "Test_Process_definition"}, context.user)[0]
    context.process_id = context.control.start_process(
        start_process_message(_user_id = context.user["_id"],
                              _process_definition_id = context.original_definition["_id"],
                              _destination = "destination_peer",
                              _globals = {},
                              _message_id = 1,
                              _reason="Testing",
                              _source_process_id = str(ObjectId())
                    ), context.user)

    time.sleep(0.1)

@step("the destination peer must receive the command")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    ok_(context.receiver.message['schemaRef'] == 'ref://bpm.message.bpm.process.start')


@step("the state must become (?P<process_state>.+)")
def step_impl(context, process_state):
    """
    :type context behave.runner.Context
    """
    print("lookin for processId: " + context.process_id + ", state: " + process_state)
    context.log_item = context.db_access.find(
        {"conditions": {"processId": ObjectId(context.process_id), "state": process_state},
         "collection": "log"
         },
        context.user)[0]
    print(str(context.log_item))
    ok_(True)


@step("the result must match expectations")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    print("Took " + str(
        (context.tests_ended - context.tests_started) * 1000) + " milliseconds.")
    ok_(context.process_result["result"] == {"result": "result"} and
        context.process_result["globals"] == {"context": "context"})

