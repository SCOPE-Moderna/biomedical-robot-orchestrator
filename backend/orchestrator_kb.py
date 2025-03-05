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
        self.sleep_time = 5 # Set async sleep time to 5 seconds


    async def run_execution_node(self, noderun_id: str):

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
            await asyncio.sleep(self.sleep_time)

        # Get plate locations associated with this node
        platelocation_source = PlateLocation.fetch_from_ids(node_info['source_plate_locations'])
        platelocation_destination = PlateLocation.fetch_from_ids(node_info['destination_plate_locations'])

        # Check that source plate locations are filled
        while True:

            # Track number of actively used plate locations
            source_in_progress_count = 0
            destination_in_progress_count = 0

            # For each source plate location
            for loc in platelocation_source:

                # If the plate location has never been used or if it was used but the operation is complete
                if loc.in_use_by is None or loc.in_use_by.status == 'completed':
                    continue

                # If the plate location has was used by a node that failed
                elif loc.in_use_by.status == 'failed':
                    raise ValueError(f"Status failed in node {loc.in_use_by} detected at plate location {loc}")
                
                # If the location is actively in use
                elif loc.in_use_by.status in ('in_progress', 'waiting', 'paused'):
                    in_progress_count += 1

                else:
                    raise ValueError(f"Unrecognized status {loc.in_use_by.status} in node {loc.in_use_by}")
                
            # For each destination plate location
            for loc in platelocation_destination:
                if loc.in_use_by is None:
                    continue
                elif loc.in_use_by.status == 'failed':
                    raise ValueError(f"Status failed in node {loc.in_use_by} detected at plate location {loc}")
                elif loc.in_use_by.status in ('completed', 'in_progress', 'waiting', 'paused'):
                    destination_in_progress_count += 1
                else:
                    raise ValueError(f"Unrecognized status {loc.in_use_by.status} in node {loc.in_use_by}")

            # If any of the plate locations were being used, wait for them to no longer be in use
            if source_in_progress_count > 0:
                while any(loc.in_use_by is not None and loc.in_use_by.status in ('in_progress', 'waiting', 'paused') for loc in platelocation_source):
                    await asyncio.sleep(self.sleep_time)
            elif destination_in_progress_count > 0:
                while any(loc.in_use_by is not None for loc in platelocation_destination):
                    await asyncio.sleep(self.sleep_time)
            else:
                break

        # Set Node Run status to "in_progress"
        noderun.set_status('in_progress')

        # Execute node function
        function_result = getattr(instrument, node_info['function'])()

        # Complete Node Run
        NodeRun.complete(noderun_id)

        return function_result
