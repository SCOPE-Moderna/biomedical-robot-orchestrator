# the flowchart shows a decision to add to the instrument queue or not, but it should always add to the instrument queue
# is instrument free should be a decision that the instrument class makes, not the orchestrator

# if the queue is a property of each instrument, then the orchestrator will add to the queue, 
# and then once the task is popped off the queue, it will call the orchestrator again to do a bunch of database operations. 
# this doesn't seem to make much sense.

# is there a separation between the actual orchestrator class and code that is "running" the orchestrator?
# for example, what is calling the methods in the orchestrator class? Should the waiting be handled by the orchestrator itself,
# or the code that is "running" the orchestrator? what is actually included in the orchestrator method in this case?

# is the instrument class itself the one "running" the orchestrator? For example, once items are added to the queue and popped off,
# is the instrument calling some methods from the orchestrator to do the database checks? This could make sense because the instrument
# can only do one thing at a time (by popping things off its queue), so waiting won't be an issue, whereas if we bake waiting into
# the orchestrator, it might be hard to run things in parallel. 

# the queue could be a property of the orchestrator itself and this would streamline the "execution" method.
#  the gRPC calls technically "running" the orchestrator.

# Once the action is added to the instrument queue, how do we check that it's ready to execute? How often is the instrument checking
# whether something is in the queue? Does it just have a while true loop and keeps executing? Once it's ready to execute, 
# how do we communicate that to the orchestrator? How will waiting be implemented? Is the instrument class doing the waiting, or is
# the orchestrator method doing the waiting?

# how do we make sure that the grpc call received will get a return within the same function call if parts of this flow are 
# split among different parts of the code?

#asyncio can be used for waiting

# to let the orchestrator know when the item in the queue has been popped off, the instrument class should include an attribute
# that describes what task it is currently working on, and a method to obtain this information. If the instrument starts a task, how
# does it do the proper checks it needs before it executes? Does all of this code get ported into the instrument class?
# for example, say the xpeel pops a "peel" action off its queue. When the orchestrator adds things to the instrument queue, it can
# include information like what type of node it is (e.g. "execute"). When the xpeel calls the next thing in the queue, it can check this
# action type, and based on this, it can call a "do checks" function in the orchestrator that will do the proper database checks.
# the instrument will do the waiting or action based on the results of this, and it can keep calling database checks with asyncio 
# if it needs to wait. the problem with this is that once the action is completed, somehow the information needs to be compiled and sent
# back to node-red. this could be done in the instrument classes, but then it kind of defeats the purpose of the orchestrator. 

# putting the queues in the instrument classes makes popping things off the queue and running things one at a time easier, but it makes
# communication with the orchestrator and node-red more difficult or boiler-plate intensive. putting queues in the orchestrator makes
# communicating with node-red easier and streamlines the code, but checking if an instrument is free is harder.

# should the instrument also have an in_use_by? this could allow easy checking for whether the instrument is free or not.

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



