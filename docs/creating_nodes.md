# Creating Nodes

This guide provides an in-depth guide for creating new nodes that will appear in Node-RED and process in the Orchestrator.

## What Do Nodes Do?

Each node represents one atomic piece of functionality for a device. For example, for an automated plate peeler, you might have the following nodes:

- Peel (with parameters)
- Reset
- Seal Check
- Status

Each node has a corresponding gRPC RPC method which tells the orchestrator that it has been called.

## Understanding Node Flow (What Happens When I Run a Node?)

When you run a flow in Node-RED, Node-RED runs each node in sequence. Our custom nodes all essentially call out to the Orchestrator and ask it to do a task.

1. The node is called in Node-RED
2. Node-RED executes the JavaScript/TypeScript file -> `onInput` function. All our custom nodes essentially call the Orchestrator via gRPC and ask it to do something.
3. Once a response is received - error or success - it will continue.

Nodes run **inside Node-RED**, meaning that when a flow is interrupted, it is up to the **Orchestrator** to resume it - we will cover this in depth later.

## Understanding Node Architecture

Nodes have four distinct pieces:

- The node "HTML" file provides Node-RED with the required information to display the node, show its configuration interface, and more.
- The node "JavaScript" (Vestra uses TypeScript) file is like the "backend" of the node, and tells Node-RED what to do when this node is called.
All our custom nodes essentially call out to the Orchestrator and make a specific call.
This is also called the "node definition".
- The gRPC RPC that represents that Node - find this in the `protos` directory
- The code that handles that gRPC RPC in the Orchestrator - this is in `backend/main.py`

### Node Types

Every node has a "type", which is how Node-RED keeps track of which node is which.

Vestra prepends ALL node types with `vestra:`, manually in the [Node Definition](#the-node-definition-the-html-file) and automatically in the TypeScript file.

### The Node Definition (the HTML file)

We recommend reading Node-RED's documentation [here](https://nodered.org/docs/creating-nodes/node-html) before continuing.

**This file MUST be named the same as the directory, with `.html` at the end.** Not doing so will cause issues with Vestra's node compilation tooling.

The Node HTML file contains three pieces.

- A JavaScript/TypeScript script that registers the node with Node-RED's **frontend**. This is called the **node definition**.
  - Vestra allows you to move this to a separate TypeScript file. **We recommend doing this for nodes with a complex UI.** See an example in `nodes/nodes/grpc-ping/grpc-ping.html`.
- HTML that defines the Node's interface (when you double click the node, this is what you see)
- HTML that defines the Node's help page

Vestra's tooling allows for the node's definition (the JavaScript part of the HTML) to be in a separate TypeScript file.
Doing so has many advantages, including type checking, the ability to use external libraries, and the ability to split your node's definition into multiple files.

See an example of moving the node's definition to a separate file in the `grpc-ping` node.

To do so, simply add this code at the beginning of the file:

```html
<script type="module" src="index.ts"></script>
```

Then, create `index.ts` and put your old code inside. Now, delete the old JavaScript code and its `<script>` tag.

#### Importing Code

If you would like to import code or make gRPC calls from the Node Definition, you **must** move the node's definition
to a separate file (see above).

All of the code in that file will run in the browser, unlike the code in the [TypeScript file](#the-typescriptjavascript-file),
which runs in Node.js.

Before Node-RED starts, we compile all modules, and the bundler (`vite`) will compile all imported code into a single
file that will run in the browser.

#### Using gRPC

To use gRPC in the node definitions, you **must** import from `../../node_connector_web_pb2`, **not** from
`../../node_connector_pb2` - those are not compatible with the browser.

From there, you can create a client and make calls.

```ts
import {
  NodeConnectorClient,
  PingRequest,
} from "../../node_connector_web_pb2/node_connector";
import { GetRunningFlowsRequest } from "../../node_connector_web_pb2/ui";

const client = new NodeConnectorClient("http://localhost:8080", null, null);
```

### The gRPC RPC

Note: This is not technically required to create a node, but most nodes have a 1:1 relationship with gRPC calls.

To structure communications and to make it easy to communicate between the orchestrator and the nodes, they communicate over gRPC.
The orchestrator hosts a gRPC server, and the nodes connect to it and make calls every time they're run by Node-RED.

Plenty of documentation for gRPC exists on the web - [here is a quick start guide](https://grpc.io/docs/languages/python/quickstart/#update-the-grpc-service).

In general, there is a 1:1 relationship between nodes and RPC calls, meaning that every time a node is created, an RPC call is created to support it.
Code is then added to the Orchestrator to handle the call and pass it to the Orchestrator.

To create the RPC:

1. Go to the `protos/` directory and create a file for the device, if one does not exist.
2. Create message types for the request and response. Think about the data that goes into and comes out of the device that the Orchestrator will need/return,
   then create both request and response types. Generally, message types are named `<Device><Functionality><Request/Response>`,
   so a reset of the XPeel would be named `XPeelResetRequest` / `XPeelResetResponse`.
3. Add the `metadata` field with field number 100: `RequestMetadata metadata = 100` or `ResponseMetadata metadata = 100`.
4. Optionally, add any other fields you'd like, starting with field number 1.
5. Go to `node_connector.proto`, and add an RPC to `service NodeConnector`.
6. Compile protos by running `make protos` from the root of this repository. Ensure that both Python and Node.js packages are installed, and that
   the protobuf compiler is installed on your machine.

### The TypeScript/JavaScript File

The TypeScript file is a confusing name, but Node-RED calls this the "JavaScript file", and Vestra uses TypeScript instead of JavaScript.

This is the code that runs in Node-RED's backend when the node is run. Most of our custom nodes simply make a gRPC call - see any of the XPeel nodes for an example.

**This file MUST be named the same as the directory, with `.ts` at the end.** Not doing so will cause issues with Vestra's node compilation tooling.

Ignore Node-RED's documentation on the JavaScript file, and create nodes like this:

1. If you've added configuration variables to your node, create an interface called `YourNodeTypeNodeDef` which extends `BaseNodeDef`:
    ```ts
    interface ExampleNodeDef extends BaseNodeDef {
        my_configuration_variable: string;
    }
    ```
    - Note that all numbers will be strings.
2.  Create a class that extends `BaseNode`, and add an `onInput` function - see an example node.
3. In the `onInput` function, make any calls you'd like and do any work, then return a message.
   - To make a gRPC call, use `this.grpcClient.<your call here>`.
4. At the end of the file, add `module.exports = ExampleNode.exportable("example-node")`
    - Replace `ExampleNode` with the name of your class
    - Replace `example-node` with your node's type - this must be the same as the name of the folder it's in.
      - `vestra:` will be automatically prepended to this if you don't add it

#### Importing Code

You may import off-the-shelf Node.js modules from NPM. To do so, just `yarn install` (if Node.js is installed and yarn doesn't work, `corepack install`).

### Orchestrator Handling the RPC

Now that the RPC has been created in proto, we can now add a function to the Orchestrator that will handle it.

In `main.py`, add a new method to `NodeConnectorServicer`, and name it the **exact same** as your RPC.
This function will take two parameters: `request` of the request type you specified in the RPC, and `context`, which we don't normally use.

It must return the response type specified in the RPC. Most of this code is simple.

Note that this guide does not cover adding devices and functionality to the Orchestrator.
Please refer to the add instruments tutorial for that.