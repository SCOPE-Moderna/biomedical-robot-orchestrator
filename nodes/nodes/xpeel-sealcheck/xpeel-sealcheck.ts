import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import {
  NodeConnectorClient,
  Empty,
} from "../../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";

interface TestNodeDef extends NodeDef {}

const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

module.exports = function (RED: NodeAPI) {
  function XPeelSealCheckNodeConstructor(this: Node, config: TestNodeDef): void {
    RED.nodes.createNode(this, config);

    this.on("input", async function (msg: NodeMessage, send, done) {
      const payload = (msg.payload as string | number).toString();
      service.XPeelSealCheck(new Empty(), (error, response) => {
        if (error) {
          console.log(error);
        }
        send([
          {
            payload: {
              seal_detected: response.seal_detected
            },
          },
        ]);
        done();
      });
    });
  }

  RED.nodes.registerType("xpeel-sealcheck", XPeelSealCheckNodeConstructor);
};
