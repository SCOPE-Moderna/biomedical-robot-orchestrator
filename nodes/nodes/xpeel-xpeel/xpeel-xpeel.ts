import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import {
  NodeConnectorClient,
  Empty,
} from "../../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";
import { XPeelXPeelRequest } from "../../node_connector_pb2/xpeel";

interface XPeelXPeelNodeDef extends NodeDef {
  set_number: number;
  adhere_time: number;
}

const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

module.exports = function (RED: NodeAPI) {
  function XPeelXPeelNodeConstructor(
    this: Node,
    config: XPeelXPeelNodeDef,
  ): void {
    RED.nodes.createNode(this, config);

    this.on("input", async function (msg: NodeMessage, send, done) {
      const payload = (msg.payload as string | number).toString();
      service.XPeelXPeel(
        new XPeelXPeelRequest({
          set_number: config.set_number,
          adhere_time: config.adhere_time,
        }),
        (error, response) => {
          if (error) {
            console.log(error);
          }
          send([
            {
              payload: [
                response.error_code_1,
                response.error_code_2,
                response.error_code_3,
              ],
            },
          ]);
          done();
        },
      );
    });
  }

  RED.nodes.registerType("xpeel-xpeel", XPeelXPeelNodeConstructor);
};
