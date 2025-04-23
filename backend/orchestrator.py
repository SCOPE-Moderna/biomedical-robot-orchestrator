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
    """
    Class to manage the orchestration of instruments.

    This class is responsible for connecting to instruments, checking queues, and running node functions on the instruments.
    This class will be used as a singleton.
    """

    def __init__(self):
        """
        This constructor initializes the Orchestrator object and creates instances of all instruments.
        """
        self.sleep_time = 5  # Set async sleep time to 5 seconds

        self.instrument_dict = {}  # Dictionary to hold instrument instances
        for (
            db_instrument
        ) in Instrument.fetch_all():  # For each instrument in the database
            if db_instrument.enabled is True:  # If "enabled" is set to True
                class_obj = device_dict[
                    db_instrument.type
                ]  # Get instrument class from device_dict based on type

                if class_obj is None:  # If the class doesn't exist
                    raise ValueError(f"Class '{db_instrument.type}' not found")

                connection_info = db_instrument.connection_info
                # Create a new instance of the instrument class
                new_instance = class_obj(connection_info["ip"], connection_info["port"])
                # Add the new instance to the instrument dictionary
                self.instrument_dict[db_instrument.id] = new_instance

        logger.info(f"Orchestrator object created")

    async def connect_instruments(self):
        """
        Connect to all instruments in the instrument dictionary.
        """
        # Connect to all instruments
        for instr in self.instrument_dict.values():
            await instr.connect_device()

    async def check_queues(self):
        """
        Check the queues of all instruments and call the next node run if the instrument is not in use.
        """
        # NOTE: Infinite loop
        while True:
            # For each instrument
            for instr_id, instr in self.instrument_dict.items():

                db_instr = Instrument.fetch_from_id(
                    instr_id
                )  # Get the instrument from the database
                user = db_instr.get_user()  # Get the instrument user from the database
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
        """
        Run the functionality of a node on a specified instrument.

        Using the flow_run_id and executing_node_id, this method will create a new NodeRun object representing the
        current node run. It will then add the NodeRun to the correct instrument queue using instrument_id, and it will
        wait for the NodeRun to be called by the check_queues() loop. Once the NodeRun is called, it will check the
        plate locations associated with the node and wait for any required locations to free up. Then, it executes the
        function on the instrument, completes the NodeRun, and returns the function result from the instrument.

        :param flow_run_id: ID of the FlowRun to which the executing node belongs
        :param executing_node_id: ID of the node to be executed
        :param instrument_id: ID of the instrument to be used
        :param function_name: Name of the function to be executed on the instrument
        :param function_args: Dictionary of arguments to be passed to the instrument function
        :param movement: Boolean indicating if this node is a movement node
        :return: Result of the function executed on the instrument
        """
        logger.info(f"Running flow {flow_run_id}@{executing_node_id} in orchestrator")

        flowrun = FlowRun.fetch_from_id(flow_run_id)

        if flowrun.status == "completed":
            raise Exception(f"Flow run {flowrun.id} is marked as completed.")
        # Ensure that this node is next in the flow and should run.
        # If not, we'll just skip this node and return the last run's payload.
        last_flowrun_node = flows_graph.get_node(flowrun.current_node_id)
        if (
            last_flowrun_node.next_vestra_node() is not None
            and executing_node_id != last_flowrun_node.next_vestra_node().id
        ):
            # Skip this node, and return the value of the previous run.
            # Get value of previous node run
            logger.info(
                f"This node ({executing_node_id}) is not next from the FlowRun current node ({flowrun.current_node_id}). "
                f"Attempting to return the result from the previous run."
            )
            prev_noderun = NodeRun.fetch_from_flowrun_and_node(
                flow_run_id, executing_node_id
            )
            if prev_noderun is None:
                raise Exception(
                    f"Node is running out of order; couldn't find previous node run for node {executing_node_id} in flow run {flowrun.id}"
                )

            if prev_noderun.status == "completed":
                logger.info(
                    f"Found previous return value of type {type(prev_noderun.output_data)}, returning that"
                )

                return prev_noderun.output_data

            # If the previous run status isn't complete, then we'll re-run this node.
            logger.info(
                f"Re-running node {executing_node_id} in flow {flow_run_id} because it didn't complete previously"
            )
            noderun = prev_noderun
        else:
            # Using the noderun_id, fetch a NodeRun object
            noderun = NodeRun.create(flow_run_id, executing_node_id)

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
        # Initialize empty source and destination plate location lists
        platelocation_source = []
        platelocation_destination = []

        # If this node is an arm movement
        if movement is True:
            if "source_waypoint_number" in function_args:
                loc_id = instrument.plate_locations[
                    function_args["source_waypoint_number"]
                ]
                platelocation_source = PlateLocation.fetch_from_ids([loc_id])
            if "destination_waypoint_number" in function_args:
                loc_id = instrument.plate_locations[
                    function_args["destination_waypoint_number"]
                ]
                platelocation_destination = PlateLocation.fetch_from_ids([loc_id])

        # If this node executes without movement
        else:
            # Fetch plate location from instrument ID
            platelocation_source = PlateLocation.fetch_from_instrument_id(
                db_instrument.id
            )

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
                    loc.get_user() is not None and loc.get_user().status != "completed"
                    for loc in platelocation_source
                ):
                    await asyncio.sleep(self.sleep_time)
                    logger.info("Waiting for source plate locations to be filled")
            elif destination_in_progress_count > 0:
                while any(
                    loc.get_user() is not None for loc in platelocation_destination
                ):
                    await asyncio.sleep(self.sleep_time)
                    logger.info("Waiting for destination plate locations to clear up")
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
        function_result = await getattr(instrument, function_name)(**function_args)

        # Complete Node Run
        noderun.complete(function_result)
        logger.info(f"NodeRun {noderun.id} completed")

        # If this is the last node in the flow, complete the flow run
        graph_node = flows_graph.get_node(executing_node_id)
        if graph_node.next_vestra_node() is None:
            # Flow run complete
            flowrun.update_node(executing_node_id, "completed")

        # Clear the source plate locations if this node type is a movement
        if movement is True:
            for loc in platelocation_source:
                loc.set_in_use_by(None)

        return function_result
