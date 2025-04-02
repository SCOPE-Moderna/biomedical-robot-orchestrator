import { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import {
  StartFlowRequest,
  StartFlowResponse,
} from "../../node_connector_pb2/node_connector";
import { BaseNode, OrchestratorMessageInFlow } from "../nodeAPI";
import type { RequestMetadata } from "../../node_connector_pb2/metadata";

interface IStartFlowNode extends Node {
  flow_name: string;
}

class StartFlowNode extends BaseNode<IStartFlowNode> {
  async onInput(msg: OrchestratorMessageInFlow): Promise<NodeMessage> {
    if (msg.__orchestrator_run_id) {
      this.node.status({
        fill: "red",
        shape: "dot",
        text: "Node must be at the beginning of the flow!",
      });

      throw new Error(
        "This node is not designed to be used in the middle of a flow. It should be the first node in a flow.",
      );
    }

    const startRequest = new StartFlowRequest({
      start_node_id: this.node.id,
      flow_name: this.node.flow_name,
    });

    const response: StartFlowResponse = await new Promise((resolve, reject) => {
      this.grpcClient.StartFlow(startRequest, (error, response) => {
        if (error) {
          reject(error);
        }
        resolve(response);
      });
    });

    this.node.status({
      fill: "green",
      shape: "dot",
      text: `Run ID: ${response.run_id} started.`,
    });

    msg.payload = response.toObject();
    msg.__orchestrator_run_id = parseInt(response.run_id);

    return msg;
  }
}

module.exports = StartFlowNode.exportable("start-flow", {
  checkForRunId: false,
});
