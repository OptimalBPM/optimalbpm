"""
This module exposes the Optimal BPM Admin API as a web service through a CherryPy module
"""

import copy
import cherrypy

from mbe.cherrypy import aop_check_session
from mbe.constants import object_id_right_admin_everything
from mbe.groups import has_right
from plugins.optimalbpm.broker.control import Control
from plugins.optimalbpm.broker.messaging.factory import start_process_message

from of.broker.globals import states

__author__ = 'Nicklas Borjesson'


class CherryPyControl(object):
    """
    The CherryPyControl class is a plugin that provides process and agent control functions.
    All functionality that concerns running, stopping and restarting BPM functionality is gathered here.
    Each function:
    * checks credentials, rights and validates using AOP decorators
    * transforms the request and forwards to the counterparts in the Control class,
    """

    states = None

    def __init__(self, _root_object):
        self._control = Control(_root_object.database_access, _root_object.node._node, _root_object.monitor.queue, _root_object.stop_broker,
                                _root_object.address, _root_object.process_id)


    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def save_process_definition(self, **kwargs):
        has_right(object_id_right_admin_everything, kwargs["user"])
        return self._control.save_process_definition(cherrypy.request.json, kwargs["user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def load_process_definition(self, **kwargs):
        has_right(object_id_right_admin_everything, kwargs["user"])
        return self._control.load_process_definition(cherrypy.request.json, kwargs["user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def remove_process_definition(self, **kwargs):
        has_right(object_id_right_admin_everything, kwargs["user"])
        return self._control.remove_process_definition(cherrypy.request.json, kwargs["user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def get_process_definition_hash(self, **kwargs):
        has_right(object_id_right_admin_everything, kwargs["user"])
        return self._control.get_process_definition_hash(cherrypy.request.json, kwargs["user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def agent_control(self, **kwargs):
        return self._control.agent_control(cherrypy.request.json["address"],
                                                  cherrypy.request.json["command"],
                                                  cherrypy.request.json["reason"],
                                                  kwargs["user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def start_process(self, **kwargs):
        has_right(object_id_right_admin_everything, kwargs["user"])
        if "source_process_id" in cherrypy.request.json:
            _source_process_id = cherrypy.request.json["source_process_id"]
        else:
            _source_process_id = None

        _start_process_message = start_process_message(
            _user_id=kwargs["user"]["_id"],
            _process_definition_id=cherrypy.request.json["process_definition_id"],
            _destination=cherrypy.request.json["destination"],
            _globals=cherrypy.request.json["globals"],
            _reason=cherrypy.request.json["reason"],
            _message_id=cherrypy.request.json["message_id"],
            _source_process_id=_source_process_id
        )

        return self._control.start_process(_start_process_message=_start_process_message, _user=kwargs["user"])

    @cherrypy.expose
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def get_processes(self, **kwargs):
        print("Request for a list of processes")
        return self._control.get_processes(kwargs["user"])

    @cherrypy.expose
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def get_process_states(self, **kwargs):
        has_right(object_id_right_admin_everything, kwargs["user"])
        print("Request for a list of states")
        return list(copy.copy(states))

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    def get_process_history(self, **kwargs):
        has_right(object_id_right_admin_everything, kwargs["user"])
        print("Request for history of a process")
        _process_id = cherrypy.request.json["process_id"]
        return self._control.get_process_history(_process_id, kwargs["user"])
