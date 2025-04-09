import type { NodeMessage, NodeDef } from "node-red";
import { RequestMetadata } from "../../node_connector_pb2/metadata";
import { BaseNode, OrchestratorMessageInFlow } from "../nodeAPI";
import {
  UR3MoveToJointWaypointRequest,
  UR3MoveToJointWaypointResponse,
} from "../../node_connector_pb2/ur3";

interface UR3MoveToJointWaypointNodeDef extends NodeDef {
  waypoint_number: string;
  instrument_id: string;
}

class UR3MoveToJointWaypointNode extends BaseNode<UR3MoveToJointWaypointNodeDef> {
  async onInput(
    msg: OrchestratorMessageInFlow,
    requestMetadata: RequestMetadata,
  ): Promise<NodeMessage> {
    const waypointNumber = parseInt(this.config.waypoint_number);

    if (isNaN(waypointNumber)) {
      throw new Error("waypointNumber must be a number.");
    }

    const moveToJointWaypointRequest = new UR3MoveToJointWaypointRequest({
      waypoint_number: waypointNumber,
      metadata: requestMetadata,
    });

    const response: UR3MoveToJointWaypointResponse = await new Promise(
      (resolve, reject) => {
        this.grpcClient.UR3MoveToJointWaypoint(
          moveToJointWaypointRequest,
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
      success: response.success,
    };

    return msg;
  }
}

module.exports = UR3MoveToJointWaypointNode.exportable(
  "ur3-movetojointwaypoint",
);
