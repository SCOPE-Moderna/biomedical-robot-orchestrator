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

    async def check_queues(self):
        # NOTE: Infinite loop
        while True:
            # For each instrument
            for instr in (self.xpeel, self.ur3):

                # TODO: add ID property to instrument classes
                db_instr = Instrument.fetch_from_id(instr.id)

                # Get the first item from the queue if the instrument is not in use
                # NOTE: This assumes instrument queues are implemented in each instrument class. Each instance must have its own queue.
                # TODO: Implement instrument queues
                if db_instr.in_use_by is None or db_instr.in_use_by.status == 'completed':
                    if instr.q.qsize() > 0:
                        next_noderun_id = instr.q.get()
                        db_instr.set_in_use_by(next_noderun_id)

            # Wait before trying to get things from the queue again
            await asyncio.sleep(self.sleep_time)

    async def run_node(self, noderun_id: str, movement=False):

        # Using the noderun_id, fetch a NodeRun object
        noderun = NodeRun.fetch_from_id(noderun_id)

        # Get additional information about this type of node
        node_info = FlowsGraph.get_node(noderun.node_id)

        # Get the instrument associated with the node
        # TODO: hard code associations between node_ids and instruments
        instrument = getattr(self, (node_info['instrument']))

        # Add node_run_id to instrument queue
        # NOTE: This assumes instrument queues are implemented in each instrument class. Each instance must have its own queue.
        # TODO: Implement instrument queues
        instrument.q.put(noderun_id)

        # Set status of this node in the database to "waiting"
        noderun.set_status('waiting')

        # Wait for the node_run_id to be called from the queue
        # TODO: implement get_in_use_by in db.Instrument
        db_instrument = Instrument.fetch_from_id(instrument)
        while db_instrument.in_use_by != noderun_id:
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
                # NOTE: allowing an empty plate location to be considered "filled" could cause strange behavior. 
                # This functionality is allowed in order to be flexible for starting flows and pausing/restarting.
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
                if loc.in_use_by is None: # If destination location is empty
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

        # Set source and destination plates to in use by this node
        for loc in platelocation_source:
            loc.set_in_use_by(noderun_id)
        for loc in platelocation_destination:
            loc.set_in_use_by(noderun_id)

        # Run function on instrument
        function_result = getattr(instrument, node_info['function'])()

        # Complete Node Run
        noderun.complete(noderun_id)

        if movement is True:
            for loc in platelocation_source:
                loc.set_in_use_by(None)

        return function_result
