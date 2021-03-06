"""
This module exposes the Optimal BPM Process API as a web service through a CherryPy helper class

Created on Nov 27, 2014

@author: Nicklas Boerjesson
"""

import sys
import os
import json

from of.common.logging import write_to_log, EC_NOTIFICATION, SEV_DEBUG, EC_INTERNAL, SEV_ERROR, SEV_INFO

sys.path.append(os.path.dirname(__file__))

import cherrypy

from of.broker.cherrypy_api.node import aop_check_session
from of.schemas.constants import id_right_admin_everything
from of.common.security.groups import has_right
from plugins.optimalbpm.broker.translation.python.translator import ProcessTokens, core_language


__author__ = 'Nicklas Borjesson'

script_dir = os.path.dirname(os.path.abspath(__file__))


class CherryPyProcess(object):
    """
    This is a CherryPy helper class that provides a web service API for processes.
    """
    # Cached python keywords
    keywords = None
    # The root CherryPy object
    root_object = None

    # The root repository folder
    repository_parent_folder = None

    # Reference to the central namespaces instance
    namespaces = None

    def __init__(self, _namespaces, _repository_parent_folder):
        """
        Initiates the class, loads keywords and namespaces for the translation
        """
        try:
            self.keywords = ProcessTokens.load_keywords()
        except Exception as e:
            raise Exception("Process init - Error loading keywords: " + str(e))
        # Load all of BPAL
        self.namespaces = _namespaces
        self.repository_parent_folder = _repository_parent_folder

        try:
            # TODO: Remove this before 1.0 (PROD-39)
            self.namespaces.load_dicts(
                core_language + [os.path.join(script_dir, "../translation/features/fake_bpm_lib.json")],
                _top_attribute="namespaces")
        except Exception as e:
            raise Exception("Process init - Error loading testing dummy dictionatries: " + str(e))
    # Load all of BPAL


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
        _tokens = ProcessTokens(_keywords=self.keywords, _namespaces=self.namespaces)

        _result = dict()
        _result["processId"] = _process_id

        _result["encoding"] = _tokens.encoding
        _result["name"] = "source.py"
        _result["documentation"] = _tokens.documentation

        _repo_path = os.path.join(os.path.expanduser(self.repository_parent_folder), _process_id)
        _filename_data = os.path.join(_repo_path, "data.json")
        _filename_process = os.path.join(_repo_path, "main.py")
        if not os.path.exists(_filename_process):
            # No process definition exists
            # Parse a dummy string to have something to begin with
            _verbs = _tokens.parse(_string="pass")
            _result["verbs"] = _tokens.verbs_to_json(_verbs)
            _result["paramData"] = {}
        else:
            # Parse the source file
            _verbs = _tokens.parse(_filename=_filename_process)
            _result["verbs"] = _tokens.verbs_to_json(_verbs)

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
        has_right(id_right_admin_everything, kwargs["_user"])
        _tokens = ProcessTokens(_keywords=self.keywords, _namespaces=self.namespaces)
        _tokens.documentation = cherrypy.request.json["documentation"]

        _verbs = _tokens.json_to_verbs(_json=cherrypy.request.json["verbs"])
        if "documentation" in cherrypy.request.json:
            _tokens.documentation = cherrypy.request.json["documentation"]

        _process_id = cherrypy.request.json["processId"]
        _repo_path = os.path.join(os.path.expanduser(self.repository_parent_folder), _process_id)
        _filename = os.path.join(_repo_path, "main.py")

        # Store in repository
        if not os.path.exists(_repo_path):
            # No process definition, it is a new process, create a folder.
            write_to_log("Initating new repo at " + _repo_path, EC_NOTIFICATION, SEV_INFO)
            os.makedirs(_repo_path)
            # TODO: Init git repo (PROD-11)

        _namespaces, _map = _tokens.encode_process(_verbs=_verbs, _filename=_filename)

        _filename_namespaces = os.path.join(_repo_path, "namespaces.json")
        with open(_filename_namespaces, "w") as f:
            json.dump(_namespaces, f)
        _filename_map = os.path.join(_repo_path, "map.json")
        with open(_filename_map, "w") as f:
            json.dump(_map, f)
        _filename_data = os.path.join(_repo_path, "data.json")
        with open(_filename_data, "w") as f:
            json.dump(cherrypy.request.json["paramData"], f)

        write_to_log("save_process to " + _repo_path + ", done", _category=EC_NOTIFICATION, _severity=SEV_DEBUG)

    @cherrypy.expose
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def load_definitions(self, **kwargs):
        """
        Load all definitions
        :param kwargs: Unused, but injected by check session
        """
        return {"namespaces": self.namespaces.as_dict(), "keywords": self.keywords}
