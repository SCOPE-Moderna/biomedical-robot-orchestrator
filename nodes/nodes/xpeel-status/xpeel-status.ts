import type { NodeMessage } from "node-red";
import { BaseNode, OrchestratorMessageInFlow } from "../nodeAPI";

class XPeelStatusNode extends BaseNode {
  async onInput(msg: OrchestratorMessageInFlow): Promise<NodeMessage> {
    // check if any XPeel device is available - check python xpeel queue

    // if no available:
    // set Node-RED status to variation on "waiting"
    // this.node.status({ fill: "gray", shape: "ring", text: "waiting to run." });
    // check status of device(s)

    // if available:
    // set xpeel queue to "in-use" & Node-RED status to "connected"
    // this.node.status({ fill: "green", shape: "ring", text: "running." });
    const response = await this.grpcClient.XPeelStatusRequest();

    msg.payload = [
      response.error_code_1,
      response.error_code_2,
      response.error_code_3,
    ];

    return msg;
  }
}

module.exports = XPeelStatusNode.exportable("xpeel-status");
