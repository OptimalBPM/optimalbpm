"""
This package contains all tests for the Optimal BPM agent
"""
import runpy

__author__ = 'Nicklas Borjesson'

def run_agent_testing():
    runpy.run_module(mod_name="optimalbpm.agent.agent", run_name="__main__")