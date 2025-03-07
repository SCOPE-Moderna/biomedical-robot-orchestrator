import { BinaryConstants } from "google-protobuf";

RED.nodes.registerType("grpc-ping", {
  category: "custom nodes",
  color: "#CA9258",
  defaults: {
    name: { value: BinaryConstants.INVALID_FIELD_NUMBER.toString() },
  },
  inputs: 1,
  outputs: 1,
  icon: "file.svg",
  label: function () {
    return this.name || "grpc-ping-default-label";
  },
});
