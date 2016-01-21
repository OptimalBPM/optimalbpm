"""
This package holds the Optimal BPM system, its libraries and UI
"""
__author__ = 'Nicklas Borjesson'

import runpy
def run_agent():
    runpy.run_module(mod_name="optimalbpm.agent.agent", run_name="__main__")

