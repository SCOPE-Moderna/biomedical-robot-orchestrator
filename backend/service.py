from __future__ import annotations

import logging
import sys
from concurrent import futures

import grpc

from flows.graph import FlowsGraph, Node
from node_connector_pb2 import xpeel_pb2, node_connector_pb2, node_connector_pb2_grpc
from xpeel import XPeel

from psycopg import connect, Connection

logger = logging.getLogger(__name__)

conn: Connection

xpeel = XPeel("192.168.0.201", 1628)


class NodeConnectorServicer(node_connector_pb2_grpc.NodeConnectorServicer):
    def Ping(self, request, context):
        logger.info(f"Received ping: {request.message}")
        return node_connector_pb2.PingResponse(message=f"Pong ({request.message})", success=True)

    def StartFlow(self, request: node_connector_pb2.StartFlowRequest, context):
        logger.info("Received StartFlow request")
        start_node = graph.get_node(request.start_node_id)
        forward_node_ids: set[str] = {start_node.id}
        if start_node is None:
            logger.error(f"Node {request.start_node_id} not found")
            return node_connector_pb2.StartFlowResponse(success=False, message=f"Start node (id {request.start_node_id}) not found")

        def all_future_nodes(node: Node):
            next_nodes = node.next_nodes()
            if next_nodes is None:
                return

            for next_node in next_nodes:
                forward_node_ids.add(next_node.id)
                all_future_nodes(next_node)

        logger.debug(f"All nodes in this run: {forward_node_ids}")
        logger.info("StartFlow response: success")
        return node_connector_pb2.StartFlowResponse(success=True, message="Flow started successfully", run_id="test-run-id")

    def XPeelStatus(self, request, context):
        logger.info("Received XPeelStatus request")
        msg = xpeel.status()
        logger.info(f"XPeelStatus response: {msg}")
        return msg.to_xpeel_status_response()

    def XPeelReset(self, request, context):
        logger.info("Received XPeelReset request")
        msg = xpeel.reset()
        logger.info(f"XPeelReset response: {msg}")
        return msg.to_xpeel_status_response()

    def XPeelXPeel(self, request: xpeel_pb2.XPeelXPeelRequest, context):
        logger.info(f"Received XPeelXPeel request: {request}")
        msg = xpeel.peel(request.set_number, request.adhere_time)
        logger.info(f"XPeelXPeel response: {msg}")
        return msg.to_xpeel_status_response()

    def XPeelSealCheck(self, request, context):
        logger.info("Received XPeelSealCheck request")
        msg = xpeel.seal_check()
        has_seal = msg.type == "ready" and msg.payload[0] == "04"
        logger.info(f"XPeelSealCheck response: {has_seal}")
        return xpeel_pb2.XPeelSealCheckResponse(seal_detected=has_seal)

    def XPeelTapeRemaining(self, request, context):
        logger.info("Received XPeelTapeRemaining request")
        msg = xpeel.tape_remaining()
        logger.info(f"XPeelTapeRemaining response: {msg}")
        return xpeel_pb2.XPeelTapeRemainingResponse(
            deseals_remaining=int(msg.payload[0]) * 10,
            take_up_spool_space_remaining=int(msg.payload[1]) * 10
        )

def serve():
    port = 50051

    logger.info(f"Starting gRPC server on port {port}")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_connector_pb2_grpc.add_NodeConnectorServicer_to_server(NodeConnectorServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("gRPC server started")

    server.wait_for_termination()
    logger.info("gRPC server stopped")


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    graph = FlowsGraph("/home/aquarium/.node-red")

    logger.info(f"Connecting to database")
    conn = connect("postgres://vestradb_user:veggie_straws@127.0.0.1:5432/vestradb")
    logger.info(f"Connected to database")
    logger.info(f"Making test query")
    with conn.cursor() as cur:
        data = cur.execute("SELECT * FROM test_table").fetchall()
        print(data)
        logger.info(f"Test query successful")

    conn.close()

    serve()
