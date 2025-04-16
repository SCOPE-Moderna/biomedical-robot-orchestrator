import asyncio
import logging

from backend.db.flow_runs import FlowRun
from backend.db.instruments import Instrument
from backend.db.node_runs import NodeRun
from backend.db.plate_locations import PlateLocation
from backend.devices.devices import device_dict
from backend.flows.graph import flows_graph

logger = logging.getLogger(__name__)


class Orchestrator:

    def __init__(self):

        self.sleep_time = 5  # Set async sleep time to 5 seconds

        self.instrument_dict = {}
        for db_instrument in Instrument.fetch_all():
            if db_instrument.enabled is True:
                class_obj = device_dict[db_instrument.type]

                if class_obj is None:
                    raise ValueError(f"Class '{db_instrument.type}' not found")

                connection_info = db_instrument.connection_info
                new_instance = class_obj(connection_info["ip"], connection_info["port"])
                self.instrument_dict[db_instrument.id] = new_instance

        self.loc_created = PlateLocation.fetch_from_ids(["xpeel-tray"])[0]
        logger.info(f"Orchestrator object created")

    async def connect_instruments(self):
        # Connect to all instruments
        for instr in self.instrument_dict.values():
            await instr.connect_device()

    async def check_queues(self):
        # NOTE: Infinite loop
        while True:
            # For each instrument
            for instr_id, instr in self.instrument_dict.items():

                db_instr = Instrument.fetch_from_id(instr_id)
                user = db_instr.get_user()
                logger.info(
                    f"Instrument {instr_id} user: {user.id if user is not None else None}, status: {user.status if user is not None else None}"
                )

                # Get the first item from the queue if the instrument is not in use
                if user is None or user.status == "completed":
                    if instr.q.qsize() > 0:
                        logger.info("Calling next item from queue...")
                        next_noderun_id = instr.q.get()
                        db_instr.set_in_use_by(next_noderun_id)

            # Wait before trying to get things from the queue again
            await asyncio.sleep(self.sleep_time)

    async def run_node(
        self,
        flow_run_id: int,
        executing_node_id: str,
        instrument_id: int,
        function_name: str,
        function_args: dict,
        movement=False,
    ):
        logger.info(f"Running flow {flow_run_id}@{executing_node_id} in orchestrator")

        # Using the noderun_id, fetch a NodeRun object
        noderun = NodeRun.create(flow_run_id, executing_node_id)
        flowrun = FlowRun.fetch_from_id(flow_run_id)
        flowrun.update_node(executing_node_id, "waiting")

        # Get the instrument associated with the node
        instrument = self.instrument_dict.get(instrument_id)
        if instrument is None:
            raise ValueError(f"Couldn't find an instrument with ID {instrument}")

        # Add node_run_id to instrument queue
        instrument.q.put(noderun.id)

        # Set status of this node in the database to "waiting"
        noderun.set_status("waiting")

        # Wait for the node_run_id to be called from the queue
        db_instrument = Instrument.fetch_from_id(instrument_id)
        while db_instrument.in_use_by != noderun.id:
            logger.info(f"Waiting for node {executing_node_id} to run in {flow_run_id}")
            await asyncio.sleep(self.sleep_time)
            db_instrument = Instrument.fetch_from_id(instrument_id)

        # Get plate locations associated with this node
        # NOTE: Nodes like XPeel functions that don't move the plates should only have source plate locations
        # TODO: Get the correct plate locations based on the instrument or node
        # platelocation_source = PlateLocation.fetch_from_ids([self.loc_created.id])
        platelocation_source = []
        platelocation_destination = []

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
                elif user.status in ("in-progress", "waiting", "paused"):
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
                    "in-progress",
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
                    and loc.get_user().status in ("in-progress", "waiting", "paused")  # type: ignore
                    for loc in platelocation_source
                ):
                    await asyncio.sleep(self.sleep_time)
                    logger.info("Waiting for source plate locations to be filled")
                    # re-fetch source plate locations
                    # TODO: Populate fetch_from_ids with source associated with node type
                    platelocation_source = PlateLocation.fetch_from_ids(
                        [self.loc_created.id]
                    )
            elif destination_in_progress_count > 0:
                while any(
                    loc.in_use_by is not None for loc in platelocation_destination
                ):
                    await asyncio.sleep(self.sleep_time)
                    logger.info("Waiting for destination plate locations to clear up")
                    # re-fetch destination plate locations
                    # TODO: Populate fetch_from_ids with destination associated with node type
                    platelocation_destination = PlateLocation.fetch_from_ids(
                        [self.loc_created.id]
                    )

            else:
                break

        # Set Node Run status to "in-progress"
        logger.info(f"Setting status of NodeRun {noderun.id} to in-progress")
        noderun.set_status("in-progress")
        flowrun.update_node(executing_node_id, "in-progress")

        # Set source and destination plates to in use by this node
        for loc in platelocation_source:
            loc.set_in_use_by(noderun.id)
        for loc in platelocation_destination:
            loc.set_in_use_by(noderun.id)

        # Run function on instrument
        # TODO: Make sure the input is structured correctly
        function_result = await getattr(instrument, function_name)(**function_args)

        # Complete Node Run
        noderun.complete()
        logger.info(f"NodeRun {noderun.id} completed")

        # If this is the last node in the flow, complete the flow run
        graph_node = flows_graph.get_node(executing_node_id)
        if graph_node.next_vestra_node() is None:
            # Flow run complete
            flowrun.update_node(executing_node_id, "completed")

        if movement is True:
            for loc in platelocation_source:
                loc.set_in_use_by(None)

        return function_result
