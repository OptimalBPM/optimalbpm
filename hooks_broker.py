from plugins.optimalbpm.broker.cherrypy.control import CherryPyControl
from plugins.optimalbpm.broker.cherrypy.process import CherryPyProcess


import plugins.optimalbpm.schemas.constants

__author__ = 'nibo'


def init_globals(_broker_scope):
    # Add our constants to the global scope
    plugins.optimalbpm.schemas.constants.init()


def after_admin_ui(_broker_scope, _admin_object):
    _admin_object.process = CherryPyProcess(_broker_scope["namespaces"], _broker_scope["repository_parent_folder"])
    _admin_object.control = CherryPyControl(_broker_scope)
