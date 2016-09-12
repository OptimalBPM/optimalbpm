import datetime
import json
import queue
import time

from behave import *
from bson.objectid import ObjectId
from nose.tools.trivial import ok_
from of.common.messaging.factory import reply_with_error_message



use_step_matcher("re")

message_id = 0

def getNextMessageId():
    global message_id
    message_id+= 1
    return message_id


def on_broker_message(web_socket, message):
    print("\non_broker_message: " + str(message))
    if message['schemaRef'] == "ref://of.message.message":
        # This is the first start process, respond with process instance
        web_socket.context.process_id = str(ObjectId())
        web_socket.received_message(json.dumps(
            {
            "destination": "agent",
            "messageId": message['messageId'],
            "destinationProcessId": message['sourceProcessId'],
            "sourceProcessId": message['destinationProcessId'],
            "data": "The_Response_Data_åäö",
            "schemaRef": "ref://of.message.message",
            "source": "broker_peer"
            }))


@given("a process mockup puts a message on the send_queue")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    context.broker_socket.on_message = on_broker_message
    context.process_monitor.handler.busy_workers[context.process_process_id] = {
        "queue": context.worker_monitor.queue,
        "processId": context.process_process_id
    }

    destination_process_id = str(ObjectId())
    context.message = {
        "destination": "other_agent",
        "messageId": getNextMessageId(),
        "sourceProcessId": context.process_process_id,
        "destinationProcessId": destination_process_id,
        "data": "The_Data_åäö",
        "source": "agent_peer",
        "schemaRef": "ref://of.message.message"
    }
    context.message_monitor.queue.put([None, context.message])


@then("it should reach the broker mockup")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    time.sleep(0.01)
    ok_(context.broker_socket.message['schemaRef'] == "ref://of.message.message")


@step("a response should be sent")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    context.broker_process_id = str(ObjectId())
    context.message = {
        "destination": "other_agent",
        "messageId": getNextMessageId(),
        "sourceProcessId": context.broker_process_id,
        "destinationProcessId": context.process_process_id,
        "data": "The_Data_åäö",
        "schemaRef": "ref://of.message.message",
        "source": "broker_peer"
    }

    context.broker_socket.received_message(json.dumps(context.message))


@step("be received by the worker handler")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    time.sleep(0.01)
    ok_(context.worker_handler.message['schemaRef'] == "ref://of.message.message" and
        context.worker_handler.message['data'] == context.message["data"])


@given("a broker mockup sends a process start message")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    context.process_monitor.handler.on_process_start = on_process_start
    context.broker_socket.on_message = None
    context.message = {
            "userId": context.user["_id"],
            "processDefinitionId": str(ObjectId()),
            "destination": "agent_peer",
            "globals": {"global_variable": "global_variable value"},
            "entryPoint": {"moduleName": "module name", "functionName": "function name"},
            "runAs": "someoneelse",
            "processId": str(ObjectId()),
            "sourceProcessId": str(context.process_process_id),
            "messageId": getNextMessageId(),
            "source": "broker_peer",
            "schemaRef": "ref://bpm.message.bpm.process.start"
        }

    context.broker_socket.received_message(json.dumps(context.message))
    time.sleep(0.01)


@then("a control mockup should receive the message")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.process_monitor.handler.message["messageId"] == context.message["messageId"])


def on_process_start(_handler, _message_data):
    print("Control handler mockup, putting error on queue...")
    _handler.message_monitor.queue.put([None, reply_with_error_message(_handler, _message_data, "Mockup error.")])


@step("the broker mockup should receive an error message")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    time.sleep(0.01)
    ok_(context.broker_socket.message["errorMessage"] == "Mockup error.")
