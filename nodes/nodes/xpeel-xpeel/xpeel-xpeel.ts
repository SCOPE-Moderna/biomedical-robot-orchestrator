import type { NodeMessage } from "node-red";
import {
  XPeelStatusResponse,
  XPeelXPeelRequest,
} from "../../node_connector_pb2/xpeel";
import { RequestMetadata } from "../../node_connector_pb2/metadata";
import { BaseNode, BaseNodeDef, OrchestratorMessageInFlow } from "../nodeAPI";

interface XPeelNodeDef extends BaseNodeDef {
  set_number: string;
  adhere_time: string;
}

class XPeelXPeelNode extends BaseNode<XPeelNodeDef> {
  async onInput(
    msg: OrchestratorMessageInFlow,
    requestMetadata: RequestMetadata,
  ): Promise<NodeMessage> {
    const setNumber = parseInt(this.config.set_number);
    const adhereTime = parseInt(this.config.adhere_time);

    if (isNaN(setNumber) || isNaN(adhereTime)) {
      throw new Error("setNumber or adhereTime must be numbers.");
    }

    const peelRequest = new XPeelXPeelRequest({
      set_number: setNumber,
      adhere_time: adhereTime,
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
