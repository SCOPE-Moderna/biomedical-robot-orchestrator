import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";
import { NodeConnectorClient } from "../../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";
import { XPeelGeneralRequest } from "../../node_connector_pb2/xpeel";
import { RequestMetadata } from "../../node_connector_pb2/metadata";

interface TestNodeDef extends NodeDef {}

const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

module.exports = function (RED: NodeAPI) {
  function XPeelStatusNodeConstructor(this: Node, config: TestNodeDef): void {
    RED.nodes.createNode(this, config);

    this.on("input", async function (msg: NodeMessage, send, done) {
      // check if any XPeel device is available - check python xpeel queue

      // if no available:
      // set Node-RED status to variation on "waiting"
      // this.status({ fill: "gray", shape: "ring", text: "waiting to run." });
      // check status of device(s)

      // if available:
      // set xpeel queue to "in-use" & Node-RED status to "connected"
      // this.status({ fill: "green", shape: "ring", text: "running." });
      const payload = (msg.payload as string | number).toString();

      const request = new XPeelGeneralRequest({
        metadata: new RequestMetadata({
          executing_node_id: this.id,
          // @ts-ignore let's see if this works
          flow_run_id: msg.__orchestrator_run_id,
        }),
      });

      service.XPeelStatus(request, (error, response) => {
        if (error) {
          console.log(error);
          this.status({ fill: "red", shape: "ring", text: "error occurred." });
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
      });
    });
  }

  RED.nodes.registerType("xpeel-status", XPeelStatusNodeConstructor);
};
