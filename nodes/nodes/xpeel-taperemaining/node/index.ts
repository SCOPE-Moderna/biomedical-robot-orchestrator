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
  function XPeelTapeRemainingNodeConstructor(
    this: Node,
    config: TestNodeDef,
  ): void {
    RED.nodes.createNode(this, config);

    this.on("input", async function (msg: NodeMessage, send, done) {
      const payload = (msg.payload as string | number).toString();
      service.XPeelTapeRemaining(new Empty(), (error, response) => {
        if (error) {
          console.log(error);
        }
        send([
          {
            payload: {
              deseals_remaining: response.deseals_remaining,
              take_up_spool_space_remaining:
                response.take_up_spool_space_remaining,
            },
          },
        ]);
        done();
      });
    });
  }

  RED.nodes.registerType(
    "xpeel-taperemaining",
    XPeelTapeRemainingNodeConstructor,
  );
};
