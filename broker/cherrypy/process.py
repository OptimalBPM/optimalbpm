"""
This module exposes the Optimal BPM Process API as a web service through a CherryPy module

Created on Nov 27, 2014

@author: Nicklas Borjesson
"""

import sys
import os
import json

sys.path.append(os.path.dirname(__file__))

import cherrypy

from of.broker.cherrypy_api.node import aop_check_session
from of.schemas.constants import id_right_admin_everything
from of.common.security.groups import has_right
from plugins.optimalbpm.broker.translation.python.translator import ProcessTokens, core_language


# TODO: Consider what the documentation in the top of each module should look like (PROD-40)

__author__ = 'Nicklas Borjesson'

script_dir = os.path.dirname(__file__)


class CherryPyProcess(object):
    """
    This is a CherryPy helper class that provides the API for processes.
    """
    # Cached python keywords
    keywords = None
    # Cached function definitions
    root_object = None

    # Reference to the central definitions instance
    definitions = None
    def __init__(self, _definitions):
        """
        Initiates the class, loads keywords and definitions for the translation
        """
        self.keywords = ProcessTokens.load_keywords()
        # Load all of BPAL
        self.definitions = _definitions
        self.definitions.load_definitions(core_language + [os.path.join(script_dir, "../translation/features/fake_bpm_lib.json")])


    # TODO: There should exist some special right for this like object_id_admin_process(ORG-110)


    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def load_process(self, **kwargs):
        """
        Parses a source file into a process structure and returns it to the client
        :param kwargs: A parameter object
        """
        has_right(id_right_admin_everything, kwargs["_user"])

        _process_id = cherrypy.request.json["processId"]
        _tokens = ProcessTokens(_keywords=self.keywords, _definitions=self.definitions)
        _repo_path = os.path.expanduser("~/optimalframework/agent_repositories/" + _process_id)
        _filename_process = _repo_path +"/main.py"
        if os.path.exists(_filename_process):
            _verbs = _tokens.parse_file(_filename_process)
        else:
            _verbs = []
        _result = dict()
        _result["processId"] = _process_id
        _result["verbs"] = _tokens.verbs_to_json(_verbs)
        _result["encoding"] = _tokens.encoding
        _result["name"] = "source.py"
        _result["documentation"] = _tokens.documentation
        _filename_data = _repo_path+"/data.json"

        if os.path.exists(_filename_data):
            with open(_filename_data, "r") as f:
                _result["paramData"] = json.load(f)
        else:
            _result["paramData"] = {}

        return _result

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def save_process(self, **kwargs):
        """
        Save a process structure into a source file
        :param kwargs: A parameter object
        """
        # TODO: Document the structure of the process parameters, perhaps create a schema?(ORG-110)
        has_right(object_id_right_admin_everything, kwargs["_user"])
        _tokens = ProcessTokens(_keywords=self.keywords, _definitions=self.definitions)
        _tokens.documentation = cherrypy.request.json["documentation"]

        _process_id = cherrypy.request.json["processId"]
        _repo_path = os.path.expanduser("~/optimalframework/agent_repositories/" + _process_id)
        if not os.path.exists(_repo_path):
            os.makedirs(_repo_path)

        _filename = os.path.join(_repo_path,"main.py")
        _verbs = _tokens.json_to_verbs(_json= cherrypy.request.json["verbs"])
        if "documentation" in cherrypy.request.json:
            _tokens.documentation = cherrypy.request.json["documentation"]
        _namespaces, _map = _tokens.encode_process(_verbs = _verbs, _filename=_filename)

        _filename_namespaces = os.path.join(_repo_path,"namespaces.json")
        with open(_filename_namespaces, "w") as f:
            json.dump(_namespaces, f)
        _filename_map = os.path.join(_repo_path,"map.json")
        with open(_filename_map, "w") as f:
            json.dump(_map, f)

        _filename_data = os.path.join(_repo_path,"data.json")
        with open(_filename_data, "w") as f:
            json.dump(cherrypy.request.json["paramData"], f)

        print("save_process to " + _repo_path + ", done")

    @cherrypy.expose
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def load_definitions(self, **kwargs):
        """
        Load all definitions
        :param kwargs: Unused, but injected by check session
        """
        return {"definitions": self.definitions.as_dict(), "keywords": self.keywords}
