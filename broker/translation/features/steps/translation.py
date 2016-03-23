from filecmp import cmp
import json
from tokenize import TokenInfo
from behave import *
from nose.tools.trivial import ok_
from plugins.optimalbpm.broker.translation.python.translator import ProcessTokens, core_language

from of.common.cumulative_dict import CumulativeDict

use_step_matcher("re")

import os
script_dir = os.path.dirname(__file__)



@given("a source file is tokenized")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    _namespaces = CumulativeDict()
    _namespaces.load_dicts(_definition_files=core_language + [os.path.join(script_dir, "../fake_bpm_lib.json")],
                           _top_attribute="namespaces")
    context.tokens = ProcessTokens(_namespaces = _namespaces)
    context.verbs = context.tokens.parse_file(os.path.join(script_dir, "../source.py"))


@then("the output must match spot check verbs")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(context.verbs[7].children[1].children[0].identifier == 'print' and context.verbs[7].children[1].children[0].parameters == {'expression': '"This should always happen three times."'})



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
    _output = context.tokens.encode_process(context.verbs, os.path.join(script_dir, "../source_out.py"))


@then("the files must match")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    ok_(cmp(os.path.join(script_dir, "../source.py"), os.path.join(script_dir, "../source_out.py"), "Files do not match!"))
