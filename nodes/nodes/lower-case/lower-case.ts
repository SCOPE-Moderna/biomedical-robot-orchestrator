import type { NodeMessage } from "node-red";
import { BaseNode } from "../nodeAPI";

class LowercaseNode extends BaseNode {
  onInput(msg: NodeMessage): NodeMessage {
    msg.payload = (msg.payload as string).toLowerCase() + "!!!";
    this.node.status({ fill: "blue", shape: "ring", text: "msg sent." });
    return msg;
  }
}

module.exports = LowercaseNode.exportable("lower-case", {
  checkForRunId: false,
});
