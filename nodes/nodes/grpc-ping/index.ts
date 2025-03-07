import { plural } from "pluralize";

RED.nodes.registerType("grpc-ping", {
  category: "custom nodes",
  color: "#CA9258",
  defaults: {
    name: { value: plural("node") },
  },
  inputs: 1,
  outputs: 1,
  icon: "file.svg",
  label: function () {
    return this.name || plural("default");
  },
});
