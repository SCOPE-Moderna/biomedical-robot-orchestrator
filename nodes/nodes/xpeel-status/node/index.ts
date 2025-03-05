import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import {
  NodeConnectorClient,
  Empty,
} from "../../../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";

interface TestNodeDef extends NodeDef {}

const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

module.exports = function (RED: NodeAPI) {
  function XPeelStatusNodeConstructor(this: Node, config: TestNodeDef): void {
    RED.nodes.createNode(this, config);

    this.on("input", async function (msg: NodeMessage, send, done) {
      // check if any XPeel device is available - check python xpeel queue

      // if no available:
      // set Node-RED status to variation on "waiting"
      // this.status({ fill: "gray", shape: "ring", text: "waiting to run." });
      // check status of device(s)

      // if available:
      // set xpeel queue to "in-use" & Node-RED status to "connected"
      // this.status({ fill: "green", shape: "ring", text: "running." });
      const payload = (msg.payload as string | number).toString();
      service.XPeelStatus(new Empty(), (error, response) => {
        if (error) {
          console.log(error);
          this.status({ fill: "red", shape: "ring", text: "error occurred." });
        }
        send([
          {
            payload: [
              response.error_code_1,
              response.error_code_2,
              response.error_code_3,
            ],
          },
        ]);
        done();
      });
    });
  }

  RED.nodes.registerType("xpeel-status", XPeelStatusNodeConstructor);
};
