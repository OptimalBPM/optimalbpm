from filecmp import cmp
import json
from tokenize import TokenInfo
from behave import *
from nose.tools.trivial import ok_
from of.broker.lib.definitions import Definitions
from plugins.optimalbpm.web.server.translation.python.translator import ProcessTokens, core_language

use_step_matcher("re")

import os
script_dir = os.path.dirname(__file__)


def load_definitions(_definition_files):
    """
    MANUALLY Load function definitions from files

    :param _definition_files: A list of _definition_files
    :return: A definitions structure
    """
    # TODO: This should be deprecated, it is only used for testing
    def load_definition_file(_filename):
        with open(_filename, "r") as _local_file:
            _local_def_data = json.load(_local_file)
            try:
                
                _definitions[_local_def_data["meta"]["namespace"]] = _local_def_data
            except Exception as e:
                print(str(e))

    _definitions = {}

    # Add pythons' system functions to the "" namespace
    load_definition_file(os.path.join(script_dir, "..", "..", "python", "system.json"))

    # Also add Optimal BPMs internal functionality to the ""
    with open(os.path.join(script_dir, "..", "..", "python","internal.json"), "r") as _file:
        _def_data = json.load(_file)
        _definitions[""]["functions"].update(_def_data["functions"])

    if _definition_files:
        for _curr_definition in _definition_files:
            load_definition_file(_curr_definition)

    return _definitions


@given("a source file is tokenized")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    _definitions = Definitions()
    _definitions.load_definitions(_definition_files=core_language + [os.path.join(script_dir, "../fake_bpm_lib.json")])
    context.tokens = ProcessTokens(_definitions = _definitions)
    context.verbs = context.tokens.parse_file(os.path.join(script_dir, "../source.py"))


@then("the output must match spot check verbs")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.verbs[6].children[1].children[0].identifier == 'print' and context.verbs[6].children[1].children[0].parameters == {'expression': '"This should always happen three times."'})



@given("an array of verb is converted to json")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    context.json = ProcessTokens.verbs_to_json(context.verbs)


@then("the output must match spot check json")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.json[6]["children"][1]["children"][0]["identifier"] == 'print' and context.json[6]["children"][1]["children"][0]["parameters"] == {'expression': '"This should always happen three times."'})


@step("it is converted back to verbs")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    try:
        context.verbs = ProcessTokens.json_to_verbs(context.json)
    except Exception as e:
        print(str(e))

@step("is untokenized into another file")
def step_impl(context):
    """
    :type context behave.runner.Context
    """

    _definitions = context.tokens.encode_verbs(context.verbs, context.tokens.raw, os.path.join(script_dir, "../source_out.py"))


@then("the files must match")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(cmp(os.path.join(script_dir, "../source.py"), os.path.join(script_dir, "../source_out.py"), "Files do not match!"))


@step("all verbs raw property is reset")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    def reset_verbs_recursively(_verb):
        _verb.raw = None
        for _curr_child in _verb.children:
            reset_verbs_recursively(_curr_child)

    for _curr_child in context.verbs:
        reset_verbs_recursively(_curr_child)
