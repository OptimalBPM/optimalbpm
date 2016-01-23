from optimalbpm.broker.cherrypy.control import CherryPyControl
from optimalbpm.broker.cherrypy.process import CherryPyProcess

__author__ = 'nibo'


def cherrypy_admin(main_object):
    pass


def cherrypy_root(main_object):
    pass

def init_webserver(_root_object, _definitions):
    _root_object.process = CherryPyProcess(_definitions)
    _root_object.control = CherryPyControl(_root_object)

def messaging_init(socket):
    pass

def schema_init(schema_tools):
    pass