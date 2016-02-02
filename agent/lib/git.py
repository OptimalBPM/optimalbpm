"""
This module implements the GIT functionality of the agent
Currently unimplemented.
"""
from of.schemas.constants import zero_object_id

import dulwich

__author__ = 'Nicklas Borjesson'
# TODO: Implement GIT/dulwich on agent and broker (PROD-11)


class DulwichWrapper:
    #: The folder of the repository
    repo_folder = None

    @staticmethod
    def get_hash(self):
        pass

    @staticmethod
    def pull(self):
        pass


class DulwichMockup(DulwichWrapper):

    @staticmethod
    def get_hash(self):
        return zero_object_id

    @staticmethod
    def pull(self):
        # Do nothing?
        pass
