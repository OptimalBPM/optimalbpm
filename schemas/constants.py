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

Note: A new schema must be both given schemaId and be added to category
"""

# Fragment category - Fragments used by other schemas
schema_id_bpm_process_parameters = "e76afc2a-7159-48e4-a1ec-26a8af33c707"
schema_id_process_instance = "2eaba1b7-028f-4f32-af2e-e3b45e921ef7"  # Used in bpm_process,

# Message category - Messages between peers - forwarded by the broker to the destination if not itself
schema_id_message_bpm_process_result = "4ab55bc5-24f6-4325-8939-6143b3f1adf1"
schema_id_message_bpm_process_start = "bb442f6d-2095-4dbe-824f-fa12da6d53d4"
schema_id_message_bpm_process_command = "8bd9a1f4-146e-4e78-8bfd-fedf01236330"
schema_id_message_worker_process_command = "3b556de6-26c8-43ee-a732-7f81516510e6"

# Node category - Nodes in the node tree, cannot be messages

schema_id_node_process = "b8f7b679-bb6c-4ef9-af30-c50962dd8a54"
schema_id_node_agent = "daf49a9d-b6e7-43f5-81c7-e5a76a2f1bb9"
schema_id_node_processes = "688a51b8-c8e7-465f-8ec9-9ad132245143"

# Log category - Log messages - written to the log collection by the broker

schema_id_log_process_message = "5686821f-0a04-4c6d-8f3b-a1092712adf7"

# Process category - Process instance data - written to the process collection by the broker
schema_id_bpm_process_instance = "59ff4df0-ecda-4631-98d9-31060c5c8642"

# Control category - Control messages for runtime entities
schema_id_message_agent_control = "4487a7ca-2bc3-45b9-832f-41eaf05d0860"

# Schema category dict. Used by handlers.
of.schemas.constants.schema_categories.update({
    schema_id_bpm_process_parameters: "fragment",
    schema_id_process_instance: "fragment",

    schema_id_node_agent: "node",
    schema_id_node_processes: "node",


    schema_id_log_process_message: "log",

    schema_id_message_bpm_process_result: "message",
    schema_id_message_bpm_process_start: "message",
    schema_id_message_bpm_process_command: "message",
    schema_id_message_worker_process_command: "message",

    schema_id_bpm_process_instance: "process",

    schema_id_message_agent_control: "control"
})
# Results should be added
of.schemas.constants.intercept_schema_ids = [schema_id_message_bpm_process_result]

of.schemas.constants.peer_type__schema_id.update({"agent": schema_id_node_agent})
