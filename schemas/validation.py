"""
This module holds Optimal BPM-specific JSON schema functionality
"""
import os

from of.schemas.validation import general_uri_handler

__author__ = 'Nicklas Borjesson'

script_dir = os.path.dirname(__file__)


def bpm_uri_handler(_uri):
    """
    This function is given as call back to JSON schema tools to handle ref://bpm. namespace references

    :param uri: The uri to handle
    :return: The schema
    """

    # TODO: MAKE EVERYTHING USE CACHE INSTEAD
    if _uri[0:8] == "ref://bpm":
        return general_uri_handler(_uri, script_dir)