"""
This module contains the Optimal Framework-hooks of Optimal BPM.
OF calls these hooks at different stages.

Created on Jan 23, 2016

@author: Nicklas Boerjesson
"""
import os
from plugins.optimalbpm.broker.cherrypy.control import CherryPyControl
from plugins.optimalbpm.broker.cherrypy.process import CherryPyProcess


from plugins.optimalbpm.schemas.constants import init

__author__ = 'nibo'


def init_broker_scope(_broker_scope, _settings):
    # Find the plugin directory
    _broker_scope["repository_parent_folder"] = _settings.get_path("broker/repositoryFolder", _default="broker_repositories")
    # Add our constants to the global scope
    init()




def after_admin_ui(_broker_scope, _admin_object):
    _admin_object.process = CherryPyProcess(_broker_scope["namespaces"], _broker_scope["repository_parent_folder"])
    _admin_object.control = CherryPyControl(_broker_scope)



def post_web_init(_broker_scope):
    # Set all things only if no others have

    _broker_scope["web_config"].update({
        "/": {
            "tools.staticdir.on": True,
            "tools.staticdir.dir": os.path.join(os.path.dirname(__file__), "root"),
            "tools.trailing_slash.on": True,
            "tools.staticdir.index": "index.html",
        }
    }
    )