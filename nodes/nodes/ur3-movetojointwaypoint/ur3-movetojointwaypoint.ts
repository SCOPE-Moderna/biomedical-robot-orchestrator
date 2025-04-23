import type { NodeMessage } from "node-red";
import { RequestMetadata } from "../../node_connector_pb2/metadata";
import { BaseNode, BaseNodeDef, OrchestratorMessageInFlow } from "../nodeAPI";
import { UR3MoveToJointWaypointRequest } from "../../node_connector_pb2/ur3";

interface UR3MoveToJointWaypointNodeDef extends BaseNodeDef {
  waypoint_number: string;
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

    const response = await this.grpcClient.UR3MoveToJointWaypoint(
      moveToJointWaypointRequest,
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
