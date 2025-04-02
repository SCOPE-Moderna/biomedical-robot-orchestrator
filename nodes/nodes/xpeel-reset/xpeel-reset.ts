import nodeRed, { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import { NodeConnectorClient } from "../../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";
import {
  XPeelGeneralRequest,
  XPeelStatusResponse,
} from "../../node_connector_pb2/xpeel";
import { RequestMetadata } from "../../node_connector_pb2/metadata";
import { BaseNode, OrchestratorMessageInFlow } from "../nodeAPI";

// interface XPeelResetNodeDef extends NodeDef {}
interface XPeelResetNode extends Node {
  onButtonClick: () => void;
}

const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

class XPeelResetNode extends BaseNode {
  async onInput(
    msg: OrchestratorMessageInFlow,
    requestMetadata: RequestMetadata,
  ): Promise<NodeMessage> {
    const resetRequest = new XPeelGeneralRequest({
      metadata: requestMetadata,
    });

    const response: XPeelStatusResponse = await new Promise(
      (resolve, reject) => {
        this.grpcClient.XPeelReset(resetRequest, (error, response) => {
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

module.exports = XPeelResetNode.exportable("xpeel-reset");
