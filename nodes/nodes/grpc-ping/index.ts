window.RED.nodes.registerType("lower-case", {
  category: "custom nodes",
  color: "#CA9258",
  defaults: {
    name: { value: "" },
  },
  inputs: 1,
  outputs: 1,
  icon: "file.svg",
  label: function () {
    return this.name || "lower-case";
  },
});
