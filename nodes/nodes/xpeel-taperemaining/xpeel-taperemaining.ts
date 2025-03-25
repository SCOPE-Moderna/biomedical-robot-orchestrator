import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import { NodeConnectorClient } from "../../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";
import { XPeelGeneralRequest } from "../../node_connector_pb2/xpeel";
import { RequestMetadata } from "../../node_connector_pb2/metadata";

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
      const request = new XPeelGeneralRequest({
        metadata: new RequestMetadata({
          executing_node_id: this.id,
          // @ts-ignore let's see if this works
          flow_run_id: msg.payload.__orchestrator_run_id,
        }),
      });

      service.XPeelTapeRemaining(request, (error, response) => {
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
