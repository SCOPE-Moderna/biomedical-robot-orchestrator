import type { NodeMessage } from "node-red";
import {
  XPeelStatusResponse,
  XPeelXPeelRequest,
} from "../../node_connector_pb2/xpeel";
import { RequestMetadata } from "../../node_connector_pb2/metadata";
import { BaseNode, OrchestratorMessageInFlow } from "../nodeAPI";

class XPeelXPeelNode extends BaseNode {
  async onInput(
    msg: OrchestratorMessageInFlow,
    requestMetadata: RequestMetadata,
  ): Promise<NodeMessage> {
    const peelRequest = new XPeelXPeelRequest({
      metadata: requestMetadata,
    });

    const response: XPeelStatusResponse = await new Promise(
      (resolve, reject) => {
        this.grpcClient.XPeelXPeel(peelRequest, (error, response) => {
          if (error) {
            reject(error);
          }
          resolve(response);
        });
      },
    );

    msg.payload = [
      response.error_code_1,
      response.error_code_2,
      response.error_code_3,
    ];

    return msg;
  }
}

module.exports = XPeelXPeelNode.exportable("xpeel-xpeel");
