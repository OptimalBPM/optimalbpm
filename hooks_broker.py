from plugins.optimalbpm.broker.cherrypy.control import CherryPyControl
from plugins.optimalbpm.broker.cherrypy.process import CherryPyProcess

import plugins.optimalbpm.schemas.constants
plugins.optimalbpm.schemas.constants.init()
__author__ = 'nibo'


def cherrypy_admin(main_object):
    pass


def cherrypy_root(main_object):
    pass

def init_admin_ui(_root_object, _definitions):
    _root_object.process = CherryPyProcess(_definitions)
    _root_object.control = CherryPyControl(_root_object)

def messaging_init(socket):
    pass

def schema_init(schema_tools):
    pass