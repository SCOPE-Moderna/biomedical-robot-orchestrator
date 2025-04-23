import { NodeMessage } from "node-red";
import { XPeelGeneralRequest } from "../../node_connector_pb2/xpeel";
import { RequestMetadata } from "../../node_connector_pb2/metadata";
import { BaseNode, OrchestratorMessageInFlow } from "../nodeAPI";

class XPeelResetNode extends BaseNode {
  async onInput(
    msg: OrchestratorMessageInFlow,
    requestMetadata: RequestMetadata,
  ): Promise<NodeMessage> {
    const resetRequest = new XPeelGeneralRequest({
      metadata: requestMetadata,
    });

    const response = await this.grpcClient.XPeelReset(resetRequest);

    msg.payload = [
      response.error_code_1,
      response.error_code_2,
      response.error_code_3,
    ];

    return msg;
  }
}

module.exports = XPeelResetNode.exportable("xpeel-reset");
