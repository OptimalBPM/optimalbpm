"""
This module exposes the Optimal BPM Admin API as a web service through a CherryPy module
"""

import copy
import cherrypy

from of.broker.cherrypy_api.node import aop_check_session
from of.common.logging import write_to_log
from of.schemas.constants import id_right_admin_everything
from of.common.security.groups import aop_has_right
from plugins.optimalbpm.broker.control import Control
from plugins.optimalbpm.broker.messaging.factory import start_process_message
import of.common.messaging.websocket
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
        self._control = Control(_root_object["database_access"], _root_object["web_root"].node._node, of.common.messaging.websocket.monitor.queue, _root_object["stop_broker"],
                                _root_object["address"], _root_object["process_id"])


    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    @aop_has_right([id_right_admin_everything])
    def save_process_definition(self, **kwargs):
        return self._control.save_process_definition(cherrypy.request.json, kwargs["_user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    @aop_has_right([id_right_admin_everything])
    def load_process_definition(self, **kwargs):
        return self._control.load_process_definition(cherrypy.request.json, kwargs["_user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    @aop_has_right([id_right_admin_everything])
    def remove_process_definition(self, **kwargs):
        return self._control.remove_process_definition(cherrypy.request.json, kwargs["_user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    @aop_has_right([id_right_admin_everything])
    def get_process_definition_hash(self, **kwargs):
        return self._control.get_process_definition_hash(cherrypy.request.json, kwargs["_user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    @aop_has_right([id_right_admin_everything])
    def agent_control(self, **kwargs):
        write_to_log("Got an agent control call, command "+ cherrypy.request.json["command"] +
                     ", reason: " + cherrypy.request.json["reason"] +
                     ", address: " + cherrypy.request.json["address"] +
                     str(cherrypy.request.json))
        return self._control.agent_control(cherrypy.request.json["address"],
                                                  cherrypy.request.json["command"],
                                                  cherrypy.request.json["reason"],
                                                  kwargs["_user"])

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    @aop_has_right([id_right_admin_everything])
    def start_process(self, **kwargs):
        if "source_process_id" in cherrypy.request.json:
            _source_process_id = cherrypy.request.json["source_process_id"]
        else:
            _source_process_id = None

        _start_process_message = start_process_message(
            _user_id=kwargs["_user"]["_id"],
            _process_definition_id=cherrypy.request.json["process_definition_id"],
            _destination=cherrypy.request.json["destination"],
            _globals=cherrypy.request.json["globals"],
            _reason=cherrypy.request.json["reason"],
            _message_id=cherrypy.request.json["message_id"],
            _source_process_id=_source_process_id
        )

        return self._control.start_process(_start_process_message=_start_process_message, _user=kwargs["_user"])

    @cherrypy.expose
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    @aop_has_right([id_right_admin_everything])
    def get_processes(self, **kwargs):
        return self._control.get_processes(kwargs["_user"])

    @cherrypy.expose
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    @aop_has_right([id_right_admin_everything])
    def get_process_states(self, **kwargs):
        return list(copy.copy(states))

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(content_type='application/json')
    @aop_check_session
    @aop_has_right([id_right_admin_everything])
    def get_process_history(self, **kwargs):
        _process_id = cherrypy.request.json["process_id"]
        return self._control.get_process_history(_process_id, kwargs["_user"])
