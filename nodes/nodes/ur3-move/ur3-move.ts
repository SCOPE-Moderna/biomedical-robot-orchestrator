import type { NodeMessage } from "node-red";
import { RequestMetadata } from "../../node_connector_pb2/metadata";
import { BaseNode, BaseNodeDef, OrchestratorMessageInFlow } from "../nodeAPI";
import { UR3MoveRequest } from "../../node_connector_pb2/ur3";

interface UR3MoveNodeDef extends BaseNodeDef {
  source_waypoint_number: string;
  destination_waypoint_number: string;
  delay_between_movements: string;
}

class UR3MoveNode extends BaseNode<UR3MoveNodeDef> {
  async onInput(
    msg: OrchestratorMessageInFlow,
    requestMetadata: RequestMetadata,
  ): Promise<NodeMessage> {
    const srcWaypointNum = parseInt(this.config.source_waypoint_number);
    const dstWaypointNum = parseInt(this.config.destination_waypoint_number);
    const delayBetweenMovements = parseFloat(
      this.config.delay_between_movements,
    );

    if (isNaN(srcWaypointNum) || isNaN(srcWaypointNum)) {
      throw new Error(
        "Both the source and destination waypoint numbers must be numbers.",
      );
    }

    const request = new UR3MoveRequest({
      source_waypoint_number: srcWaypointNum,
      destination_waypoint_number: dstWaypointNum,
      delay_between_movements: !isNaN(delayBetweenMovements)
        ? delayBetweenMovements
        : 0,
      metadata: requestMetadata,
    });

    const response = await this.grpcClient.UR3Move(request);

    msg.payload = {
      success: response.metadata.success,
    };

    return msg;
  }
}

module.exports = UR3MoveNode.exportable("ur3-move");
