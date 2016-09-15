"""
This module  holds BPM-specific constants for the web socket status codes
(see https://tools.ietf.org/html/rfc6455#section-7.4.1)

Created on Jan 23, 2016

@author: Nicklas Boerjesson

"""
__author__ = 'Nicklas Börjesson'


#: 4021 is a private value that indicates that a socket is closed because the agent is restarting down, this to prevent the socket from reconnecting to the broker or restarting
AGENT_RESTARTING = 4021
#: 4022 is a private value that indicates that a socket is closed because the agent is shutting down, this to prevent the socket from reconnecting to the broker  or restarting
AGENT_SHUTTING_DOWN = 4022