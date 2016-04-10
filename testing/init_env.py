"""
The init_env module/script initializes an OptimalBPM testing environment.
"""
import os
import sys
script_dir = os.path.dirname(__file__)
# Add relative optimal bpm path to be able to load the modules of this repository properly
sys.path.append(os.path.join(script_dir, "../../../"))

# Standalone Workaround until of pip package is done.
sys.path.append(os.path.join(script_dir, "../../../../"))


from of.broker.testing.init_env import init_env
from plugins.optimalbpm.schemas.validation import bpm_uri_handler

__author__ = 'nibo'

import plugins.optimalbpm.schemas.constants
plugins.optimalbpm.schemas.constants.init()


def init_bpm_env(_context=None):

    init_env(_context, _data_files=[os.path.join(script_dir, "data_struct.json"),os.path.join(script_dir, "data_test.json")],
             _json_schema_folders=[os.path.abspath(os.path.join(script_dir, "..", "schemas"))],
             _uri_handlers={"bpm": bpm_uri_handler})


if __name__ == "__main__":
    init_bpm_env()
