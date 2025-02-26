import asyncio
from db import FlowRun, NodeRun, Instrument, PlateLocation
from flows.graph import FlowsGraph

# assuming the Node Run's id string will be passed here. (noderun_id)
def run_execution_node(noderun_id: str):

    # From the id, get the node_id
    # TODO: implement get_node_id in db.NodeRun
    node_id = NodeRun.get_node_id(noderun_id)

    # Get additional information about this type of node
    node_info = FlowsGraph.get_node(node_id)

    # Get the instrument associated with the node
    # TODO: hard code associations between node_ids and instruments
    instrument = globals().get(node_info['instrument'])

    # Add node_run_id to instrument queue
    # TODO: implement instrument queues
    instrument.q.put(noderun_id)

    # Set status of this node in the database to "waiting"
    # TODO: implement set_status in db.NodeRun
    NodeRun.set_status(noderun_id, 'waiting')

    # Wait for the node_run_id to be called from the queue
    # TODO: implement get_in_use_by in db.Instrument
    while Instrument.get_in_use_by(instrument) != noderun_id:
        asyncio.sleep(1)

    # Get plate locations associated with this node
    source_plate_locs = node_info['source_plate_locations']
    destination_plate_locs = node_info['destination_plate_locations']

    # Check that source plate locations are filled
    for loc_id in source_plate_locs:
        # TODO: implement get_in_use_by in db.PlateLocation
        in_use_by = PlateLocation.get_in_use_by(loc_id)
        # Check that the source plate location is loaded
        # TODO: Check other cases
        if in_use_by is None:
            raise ValueError(f"Source plate location {loc_id} never loaded")
        

    # Check that destination plate locations are available (only for movement nodes)
    for loc_id in destination_plate_locs:
        continue

    # Set Node Run status to "in_progress"
    NodeRun.set_status(noderun_id, 'in_progress')

    # Execute node function
    function_result = getattr(instrument, node_info['function'])()

    return function_result



