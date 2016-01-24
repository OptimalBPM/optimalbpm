import copy

from behave import *
from nose.tools.trivial import ok_

use_step_matcher("re")


@given("a new process definition is saved")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    context.original_definition = {
        "parent_id": "000000010000010001e64d42",
        "name": "Test_Process_definition",
        "runAs": "TestUser",
        "pipPackages": ["lxml"],
        "schemaRef": "bpm://node_process.json",
        "createdWhen": "2014-11-13T01:00:00+00:00",
        "canRead": ["000000010000010001e64c28", "000000010000010001e64d02"],
        "canWrite": [
            "000000010000010001e64c28",
            "000000010000010001e64d02"
        ],
        "canStart": ["000000010000010001e64c28", "000000010000010001e64d02"],
        "canStop": [
            "000000010000010001e64c28",
            "000000010000010001e64d02"
        ]
    }

    context.original_definition["_id"] = context.control.save_process_definition(
        copy.deepcopy(context.original_definition),
        context.user)


@then("loading a process definition should return the same definition")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    _result = context.control.load_process_definition(context.original_definition["_id"], context.user)
    if _result:
        ok_(context.original_definition == _result, "Failed to load process definition, differing result.")
    else:
        ok_(False, "Failed to load process definition, empty array. Check permissions, formatting and Id.")



@given("a process definition is changed")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    context.original_definition = context.node.find({"name" : "Test_Process_definition"}, context.user)[0]
    context.original_definition["name"] = "Test_Process_definition_CHANGED"

    context.control.save_process_definition(copy.deepcopy(context.original_definition), context.user)

@step("a matching repository should be created")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(False)


@then("the process definition should not exist")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    _result = context.control.load_process_definition(context.original_definition["_id"], context.user)
    if len(_result) > 0:
        ok_(False, "Failed to load process definition, differing result.")
    else:
        ok_(True)


@given("a process definition is deleted")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    context.original_definition = context.node.find({"name" : "Test_Process_definition_CHANGED"}, context.user)[0]
    _result = context.control.remove_process_definition(context.original_definition["_id"], context.user)
    ok_(True)

@step("the repository should be deleted")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(False)
