import { BinaryConstants } from "google-protobuf";

RED.nodes.registerType("grpc-ping", {
  category: "custom nodes",
  color: "#CA9258",
  defaults: {
    name: { value: "" },
  },
  inputs: 1,
  outputs: 1,
  icon: "file.svg",
  label: function () {
    return BinaryConstants.FLOAT32_MAX.toString();
  },
});
