"""
This module exposes the Optimal BPM Process API as a web service through a CherryPy module

Created on Nov 27, 2014

@author: Nicklas Borjesson
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import cherrypy

from mbe.cherrypy import aop_check_session
from mbe.constants import object_id_right_admin_everything
from mbe.groups import has_right
from optimalbpm.lib.translation.python.translator import ProcessTokens, core_language
import optimalbpm.schemas.constants

# TODO: Consider what the documentation in the top of each module should look like (OB1-42)

__author__ = 'Nicklas Borjesson'

script_dir = os.path.dirname(__file__)


class CherryPyProcess(object):
    """
    This is a CherryPy helper class that provides the API for processes.
    """
    # Cached python keywords
    keywords = None
    # Cached function definitions
    broker = None

    def __init__(self, _broker_object):
        """
        Initiates the class, loads keywords and definitions for the translation
        """
        self.broker = _broker_object
        self.keywords = ProcessTokens.load_keywords()
        # Load all of BPAL
        self.broker.definitions.load_definitions(core_language + [os.path.join(script_dir, "translation/features/fake_bpm_lib.json")])


        # TODO: Implement loading of third party definitions(OB1-109)

    # TODO: There should exist some special right for this like object_id_admin_process(OB1-144)


    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def load_process(self, **kwargs):
        """
        Parses a source file into a process structure and returns it to the client
        :param kwargs: A parameter object
        """
        has_right(object_id_right_admin_everything, kwargs["user"])

        # TODO: load specific process..._process_id = cherrypy.request.remote.processid(OB1-145)
        _tokens = ProcessTokens(_keywords=self.keywords, _definitions=self.broker.definitions)
        _verbs = _tokens.parse_file(
            os.path.expanduser("~/optimalframework/agent_repositories/000000010000010002e64d20/source.py"))
        _result = dict()
        _result["verbs"] = _tokens.verbs_to_json(_verbs)
        _result["raw"] = _tokens.raw
        _result["encoding"] = _tokens.encoding
        _result["name"] = "source.py"
        _result["documentation"] = _tokens.documentation

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
        # TODO: Document the structure of the process parameters, perhaps create a schema?(OB1-144)
        has_right(object_id_right_admin_everything, kwargs["user"])
        _tokens = ProcessTokens(_keywords=self.keywords, _definitions=self.broker.definitions)
        _verbs = _tokens.json_to_verbs(cherrypy.request.json["verbs"])
        _filename = os.path.expanduser("~/optimalframework/agent_repositories/000000010000010002e64d20/source_out.py")
        _tokens.encode_verbs(_verbs=_verbs, _header_raw=cherrypy.request.json["raw"],
                             _filename=_filename)
        print("save_process: Wrote to " + _filename)

    @cherrypy.expose
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def load_definitions(self, **kwargs):
        """
        Load all definitions
        :param kwargs: Unused, but injected by check session
        """
        return {"definitions": self.broker.definitions.as_dict(), "keywords": self.keywords}
