import type { NodeAPI, Node, NodeMessage, NodeDef } from "node-red";

interface TestNodeDef extends NodeDef {}

module.exports = function (RED: NodeAPI) {
  function LowerCaseNodeConstructor(this: Node, config: TestNodeDef): void {
    RED.nodes.createNode(this, config);

    this.on("input", function (msg: NodeMessage, send, done) {
      msg.payload = (msg.payload as string).toLowerCase() + "!";
      send(msg);
      done();
    });
  }

  RED.nodes.registerType("lower-case", LowerCaseNodeConstructor);
};
