import {
  NodeConnectorClient,
  PingRequest,
} from "../../node_connector_web_pb2/node_connector";

// Each node will need to create a client to talk to the gRPC server.
// Note that the port is 8080: this is our Envoy proxy that allows
// web apps to connect to gRPC.
const client = new NodeConnectorClient("http://localhost:8080", null, null);

async function onButtonPress() {
  const request = new PingRequest({
    message: `message from the FRONTEND sent at ${new Date().toISOString()}!`,
  });
  const response = await client.Ping(request, null);

  RED.notifications.notify(
    `Received ping response with success ${response.success}: ${response.message}`,
  );
}

RED.nodes.registerType("vestra:grpc-ping", {
  category: "custom nodes",
  color: "#CA9258",
  defaults: {
    name: { value: "gRPC Ping" },
  },
  inputs: 1,
  outputs: 1,
  icon: "file.svg",
  label: function () {
    return this.name;
  },
  button: {
    onclick: onButtonPress,
  },
});
