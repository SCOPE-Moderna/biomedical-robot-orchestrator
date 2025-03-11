import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import {
  NodeConnectorClient,
  StartFlowRequest,
} from "../../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";

// interface StartFlowNodeDef extends NodeDef {
//   flow_name: string;
// }

interface StartFlowNode extends Node {
  onButtonClick: () => void;
  flow_name: string;
}

const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

module.exports = function (RED: NodeAPI) {
  function StartFlowNodeConstructor(
    this: StartFlowNode,
    config: NodeDef,
  ): void {
    RED.nodes.createNode(this, config);
    const node = this as StartFlowNode;

    this.on("input", async function (msg: NodeMessage, send, done) {
      // @ts-ignore
      if (msg.__orchestrator_run_id) {
        this.status({
          fill: "red",
          shape: "dot",
          text: "node must be at the beginning of the flow!",
        });
        done(
          new Error(
            "This node is not designed to be used in the middle of a flow. It should be the first node in a flow.",
          ),
        );
        return;
      }

      const startRequest = new StartFlowRequest({
        start_node_id: node.id,
        flow_name: node.flow_name,
      });

      this.warn(startRequest.toObject());

      service.StartFlow(startRequest, (error, response) => {
        if (error) {
          console.log(error);
          done(error);
          return;
        }
        this.status({
          fill: "green",
          shape: "dot",
          text: `run id: ${response.run_id}`,
        });
        // @ts-ignore
        this.send({
          __orchestrator_run_id: response.run_id,
          payload: response.toObject(),
        });
        done();
      });
    });
  }

  RED.nodes.registerType("start-flow", StartFlowNodeConstructor);
};
