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

def init():
    # Schema category dict. Used by handlers.
    of.schemas.constants.schema_categories.update({
        # Fragment category - Fragments used by other schemas
        "ref://bpm.process.parameters.json": "fragment",
        "ref://bpm.procedd.bpm.json" : "fragment",
        # Message category - Messages between peers - forwarded by the broker to the destination if not itself
        "ref://bpm.message.bpm.process.result.json": "message",
        "ref://bpm.message.bpm.process.start.json": "message",
        "ref://bpm.message.bpm.process.command.json": "message",
        "ref://bpm.message.worker.process_command.json": "message",
        # Node category - Nodes in the node tree, cannot be messages
        "ref://of.node.process.json": "node",
        "ref://of.node.agent.json": "node",
        "ref://of.node.processes.json": "node",
        # Log category - Log messages - written to the log collection by the broker
        "ref://bpm.log.process.json": "log",
        # Process category - Process instance data - written to the process collection by the broker
        "ref://bpm.process.bpm.json": "process",
        # Control category - Control messages for runtime entities
        "ref://bpm.message.agent.control.json": "control"
    })

    of.schemas.constants.intercept_schema_ids = ["ref://bpm.message.bpm.process.result.json"]

    of.schemas.constants.peer_type__schema_id.update({"agent": "ref://of.node.agent.json"})
