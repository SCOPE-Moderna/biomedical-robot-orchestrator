import { createRoot, Root } from "react-dom/client";
import React from "react";
import { GrpcPingUI } from "./components";

// Keep the root global so we can use it to unmount.
let root: Root;

RED.nodes.registerType("vestra:view-flows", {
  category: "orchestrator management",
  color: "#CA9258",
  inputs: 1,
  outputs: 1,
  icon: "envelope.svg",
  label: "View Flows",
  defaults: {},
  // oneditprepare = When the node is double-clicked and its UI opens.
  // Create the React root and mount a component.
  oneditprepare: () => {
    root = createRoot(document.getElementById("app"));
    root.render(<GrpcPingUI />);
  },
  // One of these events will be called when the UI closes.
  // When that happens, unmount the UI.
  oneditsave: () => root?.unmount(),
  oneditcancel: () => root?.unmount(),
  oneditdelete: () => root?.unmount(),
});
