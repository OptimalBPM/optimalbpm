"""
The constants module add constants for all the schemas defined in Optimal BPM
"""

import of.schemas.constants

__author__ = 'Nicklas Borjesson'

"""
TODO: These are only constant for this instance of the database (perhaps XOR-them together with environment Id?)
"""

# The processes node
id_processes = "000000010000010002e64d02"

"""
Schema definition constants

Note: A new schema must be added to a category
"""


# Schema category dict. Used by handlers.
of.schemas.constants.schema_categories.update({
    # Fragment category - Fragments used by other schemas
    "bpm://bpm_process_parameters.json": "fragment",
    "bpm://process_instance.json" : "fragment",
    # Message category - Messages between peers - forwarded by the broker to the destination if not itself
    "bpm://message_bpm_process_result.json": "message",
    "bpm://message_bpm_process_start.json": "message",
    "bpm://message_bpm_process_command.json": "message",
    "bpm://message_worker_process_command.json": "message",
    # Node category - Nodes in the node tree, cannot be messages
    "bpm://node_process.json": "node",
    "bpm://node_agent.json": "node",
    "bpm://node_processes.json": "node",
    # Log category - Log messages - written to the log collection by the broker
    "bpm://log_process_message.json": "log",
    # Process category - Process instance data - written to the process collection by the broker
    "bpm://process_bpm.json": "process",
    # Control category - Control messages for runtime entities
    "bpm://message_agent_control.json": "control"
})
# TODO: These should really be in some hook
of.schemas.constants.intercept_schema_ids = ["bpm://message_bpm_process_result.json"]

of.schemas.constants.peer_type__schema_id.update({"agent": "bpm://node_agent.json"})
