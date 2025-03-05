import asyncio
from db.flow_runs import FlowRun
from db.node_runs import NodeRun
from db.instruments import Instrument
from db.plate_locations import PlateLocation
from flows.graph import FlowsGraph
from test_scripts.device_abc import UR_Robot, XPeelConnector

class Orchestrator:

    def __init__(self):
        # FIXME: Make instruments initialize properly
        self.xpeel = XPeelConnector(addr, port) # TODO: set xpeel address and port
        self.ur3 = UR_Robot(addr, port) # TODO: set ur3 address and port


    def run_execution_node(self, noderun_id: str):

        # Using the noderun_id, fetch a NodeRun object
        noderun = NodeRun.fetch_from_id(noderun_id)

        # Get additional information about this type of node
        node_info = FlowsGraph.get_node(noderun.node_id)

        # Get the instrument associated with the node
        # TODO: hard code associations between node_ids and instruments
        instrument = getattr(self, (node_info['instrument']))

        # Add node_run_id to instrument queue
        # NOTE: This assumes instrument queues are implemented in each instrument class. Each instance must have its own queue.
        instrument.q.put(noderun_id)

        # Set status of this node in the database to "waiting"
        noderun.set_status('waiting')

        # Wait for the node_run_id to be called from the queue
        # TODO: implement get_in_use_by in db.Instrument
        while Instrument.get_in_use_by(instrument) != noderun_id:
            asyncio.sleep(5)

        # Get plate locations associated with this node
        platelocation_source = PlateLocation.fetch_from_ids(node_info['source_plate_locations'])
        platelocation_destination = PlateLocation.fetch_from_ids(node_info['destination_plate_locations'])

        # Check that source plate locations are filled
        for loc in platelocation_source:

            # Check that the source plate location is loaded
            # TODO: Check other cases
            if loc.in_use_by is None:
                raise ValueError(f"Source plate location {loc.id} never loaded")
            

        # Check that destination plate locations are available (only for movement nodes)
        for loc in platelocation_destination:
            continue

        # Set Node Run status to "in_progress"
        noderun.set_status('in_progress')

        # Execute node function
        function_result = getattr(instrument, node_info['function'])()

        # Complete Node Run
        NodeRun.complete(noderun_id)

        return function_result
