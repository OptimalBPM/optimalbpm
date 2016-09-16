


__author__ = 'nibo'

import os


import traceback
from multiprocessing import Process
import time

from behave import *
from nose.tools.trivial import ok_


from plugins.optimalbpm.agent.lib.features import run_agent_testing
from of.common.messaging.utils import register_at_broker, call_api
from of.broker.features.steps import broker_cycles

use_step_matcher("re")

_log_prefix = "Tester - Broker Cycles :"
script_dir = os.path.dirname(__file__)


@step("the agent is started")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    try:
        print(_log_prefix + "Starting agent process.")
        context.agent_process = Process(target=run_agent_testing, daemon=False)
        context.agent_process.start()
        time.sleep(1)
        if context.broker_process.exitcode:
            ok_(False, "Failed starting the agent process, it terminated within wait time.")
        else:
            ok_(True)
    except Exception as e:
        print(_log_prefix + "Error starting agent: " + str(e) + "\nTraceback:" + traceback.format_exc())
        ok_(False)



@step("the agent process is registered")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    _processes = call_api(_url="https://127.0.0.1:8080/admin/control/get_system_processes",
             _session_id=context.session["session_id"],
             _data={}, _verify_SSL=False
             )
    print("Processes:")
    for _process in _processes:
        print(str(_process))
        if _process["name"] == "Agent instance(agent01)":
            ok_(True)
            return
    ok_(False)


@step("the agent is told to stop using the API")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    call_api(_url="https://127.0.0.1:8080/admin/control/agent_control",
             _session_id=context.session["session_id"],
             _data={"address": "agent01", "command": "stop", "reason": "Testing to stop an Agent."},
             _verify_SSL=False
             )
    ok_(True)




