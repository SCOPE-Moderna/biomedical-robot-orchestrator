import type { NodeMessage } from "node-red";
import {
  XPeelGeneralRequest,
  XPeelTapeRemainingResponse,
} from "../../node_connector_pb2/xpeel";
import { RequestMetadata } from "../../node_connector_pb2/metadata";
import { BaseNode, OrchestratorMessageInFlow } from "../nodeAPI";

class XPeelTapeRemainingNode extends BaseNode {
  async onInput(
    msg: OrchestratorMessageInFlow,
    requestMetadata: RequestMetadata,
  ): Promise<NodeMessage> {
    const response: XPeelTapeRemainingResponse = await new Promise(
      (resolve, reject) => {
        this.grpcClient.XPeelTapeRemaining(
          new XPeelGeneralRequest({ metadata: requestMetadata }),
          (error, response) => {
            if (error) {
              reject(error);
            }
            resolve(response);
          },
        );
      },
    );

    msg.payload = {
      deseals_remaining: response.deseals_remaining,
      take_up_spool_space_remaining: response.take_up_spool_space_remaining,
    };

    return msg;
  }
}

module.exports = XPeelTapeRemainingNode.exportable("xpeel-taperemaining");
