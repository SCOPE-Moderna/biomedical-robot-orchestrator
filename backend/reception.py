import grpc
import logging
from concurrent import futures

from node_connector_pb2 import xpeel_pb2, node_connector_pb2, node_connector_pb2_grpc

from db import FlowRun #, NodeRun
from psycopg import connect, sql

conn = connect("postgres://vestradb_user:veggie_straws@127.0.0.1:5432/vestradb")
cur = conn.cursor()

class MiddlewareReception(node_connector_pb2_grpc.NodeConnectorServicer):
    def StartFlow(*args, **kwargs):
        self = args[0]
        request = args[1]
        context = args[2]

        start_node_id = request.start_node_id
        current_node_id = request.current_node_id
        flow_name = request.flow_name

        if not self._is_start_of_flow(start_node_id): # SC: is the node @ the start of a flow
            raise ValueError("Current node is not a starting node")

        try:
            flow_id = self._insert_new_flow_run(flow_name, start_node_id)
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return node_connector_pb2.StartFlowResponse(success=False, message="Could not start flow")

        return node_connector_pb2.StartFlowResponse(
            success=True,
            message=f"Flow {flow_name} started successfully.",
            flow_id=flow_id
        )

    def _is_start_of_flow(self, start_node_id):
        return True  # replace with actual check

    def _insert_new_flow_run(self, flow_name, start_node_id, current_node_id):
        conn = connect("postgres://vestradb_user:veggie_straws@127.0.0.1:5432/vestradb")
        curs = conn.cursor()

        # put new flow in db
        curs.execute("""
            INSERT INTO flow_runs (name, start_flow_node_id, current_node_id, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (flow_name, start_node_id, current_node_id, 'in_progress'))

        run_id = curs.fetchone()[0]

        conn.commit()
        curs.close()
        conn.close()

        return run_id

    def ContinueFlow(*args, **kwargs):
        self = args[0]
        request = args[1]
        context = args[2]

        # SC: is there an existing flow_id
        if not request.flow_id: # or whatever the flow_id attr is called
            raise ValueError("Request is missing 'flow_id'")
        

# if not a new flow:
    # retrieve flow from flow id recieved from orchestrator
    # SC: check if flow is 'in progress' and current node is consistent with current node id
        # throw err if not

