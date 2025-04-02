import type { NodeMessage } from "node-red";
import {
  XPeelGeneralRequest,
  XPeelSealCheckResponse,
} from "../../node_connector_pb2/xpeel";
import { RequestMetadata } from "../../node_connector_pb2/metadata";
import { BaseNode, OrchestratorMessageInFlow } from "../nodeAPI";

class XPeelSealCheckNode extends BaseNode {
  async onInput(
    msg: OrchestratorMessageInFlow,
    requestMetadata: RequestMetadata,
  ): Promise<NodeMessage> {
    const sealcheckRequest = new XPeelGeneralRequest({
      metadata: requestMetadata,
    });

    const response: XPeelSealCheckResponse = await new Promise(
      (resolve, reject) => {
        this.grpcClient.XPeelSealCheck(sealcheckRequest, (error, response) => {
          if (error) {
            reject(error);
          }
          resolve(response);
        });
      },
    );

    msg.payload = {
      seal_detected: response.seal_detected,
    };

    return msg;
  }
}

module.exports = XPeelSealCheckNode.exportable("xpeel-sealcheck");
