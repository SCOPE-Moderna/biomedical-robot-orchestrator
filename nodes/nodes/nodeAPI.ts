import {
  NodeConnectorClient,
  StartFlowRequest,
} from "../node_connector_pb2/node_connector";
import * as grpc from "@grpc/grpc-js";
import type { Message } from "google-protobuf";

export const service = new NodeConnectorClient(
  "0.0.0.0:50051",
  grpc.credentials.createInsecure(),
  undefined,
);

import type {
  NodeAPI,
  NodeMessage,
  NodeDef,
  NodeMessageInFlow,
  Node,
} from "node-red";
import { RequestMetadata } from "../node_connector_pb2/metadata";

export interface BaseNodeOptions {
  // whether to check for an orchestrator run ID on input
  // default true
  checkForRunId: boolean;
}

const DefaultBaseNodeOptions: BaseNodeOptions = {
  checkForRunId: true,
};

export interface OrchestratorMessageInFlow extends NodeMessageInFlow {
  __orchestrator_run_id: number;
}

export interface OrchestratorMessage extends NodeMessage {
  __orchestrator_run_id: number;
}

export class BaseNode<
  TDef extends NodeDef = NodeDef,
  TNode extends Node = Node,
> {
  static type: string;
  static options: BaseNodeOptions;
  static RED: NodeAPI;

  grpcClient: NodeConnectorClient = service;

  node: TNode;
  config: TDef;

  constructor(config: TDef) {
    // @ts-ignore: we must use the constructor to access the RED instance
    // because RED is attached to the subclass' prototype in exportable
    // @ts-ignore
    this.constructor.RED.nodes.createNode(this as unknown as TNode, config);
    this.node = this as unknown as TNode;
    this.config = config;

    this.node.on(
      "input",
      async (msg: OrchestratorMessageInFlow, send, done) => {
        // check for run id
        if (this.getOptions().checkForRunId && !msg.__orchestrator_run_id) {
          this.node.status({
            fill: "red",
            shape: "dot",
            text: "This node must be after a start flow node (missing orchestrator run id).",
          });

          done(
            new Error(
              "This node must run as part of an orchestrator flow (after a start flow node) (missing orchestrator run id).",
            ),
          );
          return;
        } else {
          // Clear status
          this.node.status("");
        }

        try {
          const result = await this.onInput(
            msg,
            new RequestMetadata({
              executing_node_id: this.node.id,
              flow_run_id: msg.__orchestrator_run_id,
            }),
          );

          // Add orchestrator run ID to result message(s)
          if (this.getOptions().checkForRunId) {
            if (Array.isArray(result)) {
              for (const resultMsg of result) {
                if (Array.isArray(result)) {
                  for (const subMsg of result) {
                    // 2-d array of messages
                    (subMsg as OrchestratorMessage).__orchestrator_run_id =
                      msg.__orchestrator_run_id;
                  }
                } else {
                  // Array of messages
                  (resultMsg as OrchestratorMessage).__orchestrator_run_id =
                    msg.__orchestrator_run_id;
                }
              }
            } else {
              // Single message, add orchestrator run id
              (result as OrchestratorMessage).__orchestrator_run_id =
                msg.__orchestrator_run_id;
            }
          }

          send(result);
          done();
        } catch (e) {
          done(e);
        }
      },
    );
  }

  /**
   * Static function to export from module files.
   * Handles registering the node with Node-RED.
   *
   * @example ```ts
   * // Define class
   * class LowercaseNode extends BaseNode {
   *   // Override onInput function (can be async, too)
   *   onInput(msg: NodeMessage): NodeMessage {
   *     msg.payload = (msg.payload as string).toLowerCase();
   *     this.node.status({ fill: "blue", shape: "ring", text: "msg sent." });
   *     return msg;
   *   }
   * }
   *
   * // Export exportable function
   * module.exports = LowercaseNode.exportable("lower-case")
   * ```
   * @param type {string} The node's type in Node-RED, must be unique
   * @param options {Partial<BaseNodeOptions>} Options for the node
   */
  static exportable(
    type: string,
    options: Partial<BaseNodeOptions> = DefaultBaseNodeOptions,
  ): (RED: NodeAPI) => void {
    this.type = type;
    this.options =
      options === DefaultBaseNodeOptions
        ? DefaultBaseNodeOptions
        : { ...DefaultBaseNodeOptions, ...options };

    return (RED: NodeAPI) => {
      this.RED = RED;

      // @ts-ignore: the class system automatically attaches the 'this' parameter, which
      // is not technically a parameter of the constructor
      RED.nodes.registerType(this.type, this);
    };
  }

  getOptions(): BaseNodeOptions {
    // @ts-ignore - we must access the constructor for static properties
    return this.constructor.options;
  }

  /**
   * onInput handles input messages for the node.
   *
   * Input messages are passed to the node as a parameter, and the return value is sent to the next node in the flow.
   * Thrown errors are caught and passed to the done callback.
   *
   * @param {NodeMessage} msg - The input message to process.
   * @param requestMetadata {RequestMetadata} - RequestMetadata for gRPC objects
   * @returns {NodeMessage} - The processed message to send to the next node.
   */
  onInput(
    msg: NodeMessageInFlow,
    requestMetadata: RequestMetadata,
  ):
    | Promise<NodeMessage | (NodeMessage | NodeMessage[])[]>
    | (NodeMessage | (NodeMessage | NodeMessage[])[]) {
    // default implementation
    console.error(`onInput not implemented for ${this.constructor.name}!`);
    return msg;
  }
}
