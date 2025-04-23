import nodeRed, { NodeMessage } from "node-red";
import {
  PingRequest,
  PingResponse,
} from "../../node_connector_pb2/node_connector";
import { BaseNode } from "../nodeAPI";

class GrpcPingNode extends BaseNode {
  async onInput(msg: nodeRed.NodeMessageInFlow): Promise<NodeMessage[]> {
    const payload = (msg.payload as string | number).toString();
    const pingRequest = new PingRequest({ message: payload });

    let response: PingResponse;
    try {
      response = await this.grpcClient.Ping(pingRequest);
      this.node.status({
        fill: "green",
        shape: "dot",
        text: response.message,
      });
    } catch (error) {
      this.node.error(error);
      this.node.status({
        fill: "red",
        shape: "dot",
        text: error.message,
      });
      // this sends TWO messages to the next node!
      return [{ payload: false }, { payload: error.message }];
    }

    return [{ payload: response.success }, { payload: response.message }];
  }
}

module.exports = GrpcPingNode.exportable("grpc-ping", { checkForRunId: false });
