"""
This package holds the Optimal BPM plugin, its libraries and UI
The Optimal Framework loads this that
"""
import runpy

__author__ = 'Nicklas Borjesson'


def run_agent():
    runpy.run_module(mod_name="optimalbpm.agent.agent", run_name="__main__")
