import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import {
  NodeConnectorClient,
  Empty,
} from "../../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";
import { XPeelGeneralRequest } from "../../node_connector_pb2/xpeel";
import { RequestMetadata } from "../../node_connector_pb2/metadata";

// interface XPeelResetNodeDef extends NodeDef {}
interface XPeelResetNode extends Node {
  onButtonClick: () => void;
}

const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

module.exports = function (RED: NodeAPI) {
  function XPeelResetNodeConstructor(
    this: XPeelResetNode,
    config: NodeDef,
  ): void {
    RED.nodes.createNode(this, config);
    const node = this as XPeelResetNode;

    this.on("input", async function (msg: NodeMessage, send, done) {
      // @ts-ignore
      if (!msg.__orchestrator_run_id) {
        this.status({
          fill: "red",
          shape: "dot",
          text: "Node must be part of a flow!",
        });
        done(
          new Error(
            "This node is not designed to be used outside of a flow. It should be called after a Start Flow node.",
          ),
        );
        return;
      }

      const resetRequest = new XPeelGeneralRequest({
        metadata: new RequestMetadata({
          executing_node_id: node.id,
          // @ts-ignore let's see if this works
          flow_run_id: msg.payload.__orchestrator_run_id,
        }),
      });

      this.warn(resetRequest.toObject());

      service.XPeelReset(resetRequest, (error, response) => {
        if (error) {
          console.log(error);
        }
        send([
          {
            // @ts-ignore let's see if this works
            __orchestrator_run_id: msg.payload.__orchestrator_run_id,
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

  RED.nodes.registerType("xpeel-reset", XPeelResetNodeConstructor);
};
