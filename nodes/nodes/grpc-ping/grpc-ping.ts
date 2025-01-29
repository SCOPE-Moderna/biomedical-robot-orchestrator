import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import {
  NodeConnectorClient,
  PingRequest,
  PingResponse,
} from "../../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";

interface TestNodeDef extends NodeDef {}

const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

module.exports = function (RED: NodeAPI) {
  function GRPCPingNodeConstructor(this: Node, config: TestNodeDef): void {
    RED.nodes.createNode(this, config);

    this.on("input", async function (msg: NodeMessage, send, done) {
      const payload = (msg.payload as string | number).toString();
      const pingRequest = new PingRequest({ message: payload });
      service.Ping(pingRequest, (error, response) => {
        if (error) {
          console.log(error);
          this.status({ fill: "red", shape: "ring", text: "error." });
        }
        send([{ payload: response.success }, { payload: response.message }]);
        this.status({ fill: "green", shape: "dot", text: "response success." });
        done();
      });
    });
  }

  RED.nodes.registerType("grpc-ping", GRPCPingNodeConstructor);
};
