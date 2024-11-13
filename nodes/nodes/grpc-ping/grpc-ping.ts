import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import {
  NodeConnectorClient,
  PingRequest,
  PingResponse,
} from "../../service_pb2/service";
import * as grpc from "@grpc/grpc-js";

interface TestNodeDef extends NodeDef {}

const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

module.exports = function (RED: NodeAPI) {
  function GRPCPingNodeConstructor(this: Node, config: TestNodeDef): void {
    RED.nodes.createNode(this, config);

    this.on("input", async function (msg: NodeMessage, send, done) {
      const payload = (msg.payload as string | number).toString();
      const pingRequest = new PingRequest({ message: payload });
      service.Ping(pingRequest, (error, response) => {
        if (error) {
          console.log(error);
        }
        send([{ payload: response.success }, { payload: response.message }]);
        done();
      });
    });
  }

  RED.nodes.registerType("grpc-ping", GRPCPingNodeConstructor);
};
