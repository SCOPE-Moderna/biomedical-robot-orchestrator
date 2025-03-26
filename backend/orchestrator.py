import asyncio
import logging
from db.node_runs import NodeRun
from db.instruments import Instrument
from db.plate_locations import PlateLocation


logger = logging.getLogger(__name__)


class Orchestrator:

    def __init__(self, xpeel):
        # FIXME: Make instruments initialize properly
        self.xpeel = xpeel  # XPeelConnector(addr, port, instr_id) # TODO: set xpeel address and port
        # self.ur3 = UR_Robot(addr, port, instr_id) # TODO: set ur3 address and port
        self.sleep_time = 5  # Set async sleep time to 5 seconds
        self.xpeel_created = Instrument.fetch_from_id(1)
        self.loc_created = PlateLocation.fetch_from_ids(["xpeel-tray"])[0]
        logger.info(f"Orchestrator object created")

    async def check_queues(self):
        # NOTE: Infinite loop
        while True:
            # For each instrument
            for instr in [self.xpeel]:  # , self.ur3):

                db_instr = Instrument.fetch_from_id(
                    self.xpeel_created.id
                )  # instr.instr_id)

                user = db_instr.get_user()
                logger.info(f"Instrument user: {user.id if user is not None else None}")

                # Get the first item from the queue if the instrument is not in use
                if user is None or user.status == "completed":
                    if instr.q.qsize() > 0:
                        next_noderun_id = instr.q.get()
                        db_instr.set_in_use_by(next_noderun_id)

            # Wait before trying to get things from the queue again
            await asyncio.sleep(self.sleep_time)

    async def run_node(
        self,
        flow_run_id: int,
        executing_node_id: str,
        function_name: str,
        function_args: dict,
        movement=False,
    ):  # function_name and function_args used for demo
        logger.info(f"Running flow {flow_run_id}@{executing_node_id} in orchestrator")

        # Using the noderun_id, fetch a NodeRun object
        noderun = NodeRun.create(flow_run_id, executing_node_id)

        # Get additional information about this type of node
        # node_info = FlowsGraph.get_node(noderun.node_id)

        # Get the instrument associated with the node
        # TODO: hard code associations between node_ids and instruments
        instrument = self.xpeel  # getattr(self, (node_info['instrument']))

        # Add node_run_id to instrument queue
        instrument.q.put(noderun.id)

        # Set status of this node in the database to "waiting"
        noderun.set_status("waiting")

        # Wait for the node_run_id to be called from the queue
        db_instrument = Instrument.fetch_from_id(self.xpeel_created.id)
        while db_instrument.in_use_by != noderun.id:
            logger.info(f"Waiting for node {executing_node_id} to run in {flow_run_id}")
            await asyncio.sleep(self.sleep_time)
            db_instrument = Instrument.fetch_from_id(self.xpeel_created.id)

        # Get plate locations associated with this node
        platelocation_source = PlateLocation.fetch_from_ids(
            {self.loc_created.id}
        )  # node_info['source_plate_locations'])
        platelocation_destination = PlateLocation.fetch_from_ids(
            {self.loc_created.id}
        )  # node_info['destination_plate_locations'])

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
                user = loc.get_user()
                if user is None or user.status == "completed":
                    continue

                # If the plate location has was used by a node that failed
                elif user.status == "failed":
                    raise ValueError(
                        f"Status failed in node {loc.in_use_by} detected at plate location {loc}"
                    )

                # If the location is actively in use
                elif user.status in ("in_progress", "waiting", "paused"):
                    source_in_progress_count += 1

                else:
                    raise ValueError(
                        f"Unrecognized status {user.status} in node {loc.in_use_by}"
                    )

            # For each destination plate location
            for loc in platelocation_destination:
                user = loc.get_user()
                if user is None:  # If destination location is empty
                    continue
                elif user.status == "failed":
                    raise ValueError(
                        f"Status failed in node {loc.in_use_by} detected at plate location {loc}"
                    )
                elif user.status in (
                    "completed",
                    "in_progress",
                    "waiting",
                    "paused",
                ):
                    destination_in_progress_count += 1
                else:
                    raise ValueError(
                        f"Unrecognized status {user.status} in node {loc.in_use_by}"
                    )

            # If any of the plate locations were being used, wait for them to no longer be in use
            if source_in_progress_count > 0:
                while any(
                    # TODO: fetch all the users (node_run_id) of the plate locations at once (in one query)
                    loc.in_use_by is not None
                    and loc.get_user().status in ("in_progress", "waiting", "paused")
                    for loc in platelocation_source
                ):
                    await asyncio.sleep(self.sleep_time)
            elif destination_in_progress_count > 0:
                while any(
                    loc.in_use_by is not None for loc in platelocation_destination
                ):
                    await asyncio.sleep(self.sleep_time)
            else:
                break

        # Set Node Run status to "in_progress"
        noderun.set_status("in_progress")

        # Set source and destination plates to in use by this node
        for loc in platelocation_source:
            loc.set_in_use_by(noderun.id)
        for loc in platelocation_destination:
            loc.set_in_use_by(noderun.id)

        # Run function on instrument
        # TODO: Make sure the input is structured correctly
        function_result = getattr(instrument, function_name)(
            **function_args
        )  # instrument.call_node_interface(node_info['function'], node_info['input_data'])

        # Complete Node Run
        noderun.complete()

        if movement is True:
            for loc in platelocation_source:
                loc.set_in_use_by(None)

        return function_result
