"""
This process holds BPM-specific constants for the web socket error-codes
"""
__author__ = 'Nicklas Börjesson'


#: 4021 is a private value that indicates that a socket is closed because the agent is restarting down, this to prevent the socket from reconnecting to the broker or restarting
AGENT_RESTARTING = 4021
#: 4022 is a private value that indicates that a socket is closed because the agent is shutting down, this to prevent the socket from reconnecting to the broker  or restarting
AGENT_SHUTTING_DOWN = 4022