import { NodeMessage } from "node-red";
import {
  StartFlowRequest,
  StartFlowResponse,
} from "../../node_connector_pb2/node_connector";
import { BaseNode, BaseNodeDef, OrchestratorMessageInFlow } from "../nodeAPI";

interface StartFlowNodeDef extends BaseNodeDef {
  flow_name: string;
}

class StartFlowNode extends BaseNode<StartFlowNodeDef> {
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
      flow_name: this.config.flow_name,
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
