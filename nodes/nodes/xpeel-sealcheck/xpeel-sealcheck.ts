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
  function XPeelSealCheckNodeConstructor(
    this: Node,
    config: TestNodeDef,
  ): void {
    RED.nodes.createNode(this, config);

    const request = new XPeelGeneralRequest({
      metadata: new RequestMetadata({
        executing_node_id: this.id,
        // @ts-ignore let's see if this works
        flow_run_id: msg.payload.__orchestrator_run_id,
      }),
    });

    this.on("input", async function (msg: NodeMessage, send, done) {
      const payload = (msg.payload as string | number).toString();
      service.XPeelSealCheck(request, (error, response) => {
        if (error) {
          console.log(error);
        }
        send([
          {
            payload: {
              seal_detected: response.seal_detected,
            },
          },
        ]);
        done();
      });
    });
  }

  RED.nodes.registerType("xpeel-sealcheck", XPeelSealCheckNodeConstructor);
};
