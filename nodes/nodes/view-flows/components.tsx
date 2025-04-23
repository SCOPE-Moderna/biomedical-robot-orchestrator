import {
  FlowRun,
  GetRunningFlowsRequest,
} from "../../node_connector_web_pb2/ui";
import React, { useEffect, useState } from "react";
import {
  NodeConnectorClient,
  PingRequest,
} from "../../node_connector_web_pb2/node_connector";

// Each node will need to create a client to talk to the gRPC server.
// Note that the port is 8080: this is our Envoy proxy that allows
// web apps to connect to gRPC.
const client = new NodeConnectorClient("http://localhost:8080", null, null);

// Simple component to display a table of flows.
function FlowsTable({ flows }: { flows: FlowRun[] }) {
  if (!flows) {
    return "No running flows found.";
  }

  return (
    <table style={{ border: "1px solid black" }}>
      <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Start Flow Node ID</th>
        <th>Current Node ID</th>
        <th>Started At</th>
        <th>Status</th>
      </tr>
      {flows.map((flow) => (
        <tr key={flow.id}>
          <td>{flow.id}</td>
          <td>{flow.name}</td>
          <td>{flow.start_flow_node_id}</td>
          <td>{flow.current_node_id}</td>
          <td>
            {new Date(
              flow.started_at.seconds * 1000 +
                Math.floor(flow.started_at.nanos / 1e6),
            ).toISOString()}
          </td>
          <td>{flow.status}</td>
        </tr>
      ))}
    </table>
  );
}

// Functional component that fetches and displays flows when mounted.
export function GrpcPingUI(): React.ReactElement {
  const [flows, setFlows] = useState<FlowRun[] | null>(null);
  const [flowsError, setFlowsError] = useState<string>("");

  useEffect(() => {
    client
      .GetRunningFlows(new GetRunningFlowsRequest(), null)
      .then((res) => res.flow_runs)
      .then(setFlows)
      .catch((e: Error) => setFlowsError(e.toString()));
  }, []);

  if (flowsError) {
    return (
      <>
        <p>Error fetching flows:</p>
        <code>{flowsError}</code>
      </>
    );
  }

  if (flows === null) {
    return <p>Loading flows...</p>;
  }

  return (
    <>
      <h1>Running Flows</h1>
      <FlowsTable flows={flows} />
    </>
  );
}
