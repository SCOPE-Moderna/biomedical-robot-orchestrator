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

    this.onButtonClick = () => {
      const startRequest = new StartFlowRequest({
        start_node_id: this.id,
        flow_name: this.flow_name,
      });

      service.StartFlow(startRequest, (error, response) => {
        if (error) {
          console.log(error);
        }
        console.log(response);
      });
    };
  }

  RED.nodes.registerType("start-flow", StartFlowNodeConstructor);
};
