# Adding Instrument Functions to the Orchestrator

This guide describes how to allow the orchestrator to run additional instrument functions once the node has been created in Node-RED and the corresponding RPC and TypeScript file has been set up. 

## Setting up `NodeConnectorServicer`
In `main.py`, the `NodeConnectorServicer` class is responsible for handling the gRPC calls from Node-RED and contains functions that match each gRPC request. 

In order to allow the orchestrator to run a new node type, we need to define a new method within `NodeConnectorServicer`. Let's walk through how to add a new instrument function, using the `XpeelXpeel` method as an example.

### Step 1: Define the New Method
In `main.py`, locate the `NodeConnectorServicer` class. Inside this class, define a new method that matches the gRPC request for the new instrument function. 

```python 
async def XPeelXPeel(self, request: xpeel_pb2.XPeelXPeelRequest, context):
```

The method must be asynchronous because `run_node`, which will be called in this method, is asynchronous. This is because it waits for the NodeRun to be called from the instrument queue before it executes. The name of the method must match the name of the RPC method defined in the `node_connector.proto` file. The method takes three parameters, which are `self`, `request`, and `context`. The `request` parameter contains the data sent from Node-RED.

### Step 2: Define the `function_args` Dictionary
Inside the new method, define a dictionary called `function_args` that contains the arguments for the instrument function. The keys of the dictionary should match the names of the parameters in the instrument function, and the values should be extracted from the `request` object. 

```python
function_args = {"param": request.set_number, "adhere": request.adhere_time}
```

The `peel` function in `xpeel.py`, which will be called by the orchestrator when this method runs, takes two parameters: `set_number` and `adhere_time`. The values for these parameters are extracted from the `request` object. If the instrument function doesn't take any parameters, leave the `function_args` dictionary empty.

### Step 3: Call the `run_node` Method

Next, call the `run_node` method from the orchestrator. The singleton orchestrator is a class object in the `NodeConnectorServicer` class, so it can be accessed as `NodeConnectorServicer.orchestrator`. The `run_node` method takes five parameters, which are the flow run ID, the executing node ID, the instrument name, the instrument function name, and the instrument function arguments. The first three parameters should be extracted from the `request` object, and the last two parameters should be a string representing the instrument function name and the `function_args` dictionary. 

```python
result = await NodeConnectorServicer.orchestrator.run_node(
    request.metadata.flow_run_id,
    request.metadata.executing_node_id,
    request.metadata.instrument_id,
    "peel",
    function_args,
)
```

### Step 4: Send the Response
Finally, return the result of the `run_node` method as a response to the gRPC request. 

```python
return xpeel_message_dict_to_xpeel_status_response(result)
```

This should be a gRPC response, but for the `XPeelXPeel` method, we process the data we receive from the orchestrator before returning the gRPC response.