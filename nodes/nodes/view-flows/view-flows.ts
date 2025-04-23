import { NodeMessage } from "node-red";
import { BaseNode } from "../nodeAPI";
import {
  GetRunningFlowsRequest,
  GetRunningFlowsResponse,
} from "../../node_connector_pb2/ui";

class ViewFlowsNode extends BaseNode {
  async onInput(): Promise<NodeMessage> {
    let response: GetRunningFlowsResponse;
    try {
      response = await this.grpcClient.GetRunningFlows(
        new GetRunningFlowsRequest(),
      );
    } catch (error) {
      this.node.error(error);
      this.node.status({
        fill: "red",
        shape: "dot",
        text: error.message,
      });
      return {};
    }

    return { payload: response.flow_runs.map((run) => run.toObject()) };
  }
}

module.exports = ViewFlowsNode.exportable("view-flows", {
  checkForRunId: false,
});
