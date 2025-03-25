from __future__ import annotations

import logging
import sys
from concurrent import futures

import grpc

from flows.graph import FlowsGraph
from node_connector_pb2 import xpeel_pb2, node_connector_pb2, node_connector_pb2_grpc
from xpeel import XPeel
from db.flow_runs import FlowRun
from db.conn import conn

from orchestrator import Orchestrator

logger = logging.getLogger(__name__)

xpeel = XPeel("192.168.0.201", 1628)


def flowmethod(func):
    async def wrapper(*args, **kwargs):
        # self = args[0]
        request: node_connector_pb2.GenericMessageWithRequestMetadata = args[1]
        # context = args[2]

        # Get FlowRun ID from args
        # args: self, request, context. we will require that requests have flow_id.
        if not request.HasField("metadata"):
            logger.error("Request does not have metadata", request)
            await func(*args, **kwargs, error="Request does not have metadata")
            return

        reqMetadata: node_connector_pb2.RequestMetadata = request.metadata
        run = FlowRun.fetch_from_id(int(reqMetadata.flow_run_id))
        if run.status != "in-progress":
            msg = f"FlowRun {run.id} is not running"
            logger.error(msg)
            await func(*args, **kwargs, error=msg)
            return

        # Check placement of current node in flow graph
        # if run.current_node_id !=
        # If current node is ahead of this node, skip call
        # If current node is one before this node, update current node to this node and execute
        # TODO: If current node is more than one behind this node, return error

        # query graph for current node
        current_node = graph.get_node(run.current_node_id)
        next_vestra_node = current_node.next_vestra_node()

        if not next_vestra_node:
            # end of flow
            pass

        result: node_connector_pb2.GenericMessageWithResponseMetadata = await func(
            *args, **kwargs
        )
        logger.info(f"{func.__name__} returned: {result}")

        return result

    return wrapper


class NodeConnectorServicer(node_connector_pb2_grpc.NodeConnectorServicer):
    orchestrator = None

    def Ping(self, request, context):
        logger.info(f"Received ping: {request.message}")
        return node_connector_pb2.PingResponse(
            message=f"Pong ({request.message})", success=True
        )

    def StartFlow(self, request: node_connector_pb2.StartFlowRequest, context):
        logger.info("Received StartFlow request")
        run = FlowRun.create(
            name=request.start_node_id, start_flow_node_id=request.start_node_id
        )
        logger.info(f"Starting run: {run.id}")
        response = node_connector_pb2.StartFlowResponse(
            success=True, run_id=str(run.id)
        )
        logger.info("Received StartFlow response")
        return response

    @flowmethod
    def XPeelStatus(self, request, context):
        logger.info("Received XPeelStatus request")
        msg = xpeel.status()
        logger.info(f"XPeelStatus response: {msg}")
        return msg.to_xpeel_status_response()

    async def XPeelReset(self, request, context):
        logger.info("Received XPeelReset request")
        function_args = {}  # Add any necessary arguments here
        noderun_id = request.metadata.flow_run_id
        logger.info(f"Fetched excecuting noderun ID: {noderun_id}")
        result = await NodeConnectorServicer.orchestrator.run_node(
            noderun_id, "reset", function_args
        )
        logger.info(f"XPeelReset response: {result}")
        return result.to_xpeel_status_response()

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
            take_up_spool_space_remaining=int(msg.payload[1]) * 10,
        )


async def serve():
    port = 50051

    logger.info(f"Starting gRPC server on port {port}")
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    orchestrator = Orchestrator(xpeel)
    NodeConnectorServicer.orchestrator = orchestrator
    node_connector_pb2_grpc.add_NodeConnectorServicer_to_server(
        NodeConnectorServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    logger.info("gRPC server started")

    await server.wait_for_termination()
    logger.info("gRPC server stopped")


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    graph = FlowsGraph("/home/aquarium/.node-red")

    logger.info(f"Connecting to database")
    logger.info(f"Connected to database")
    logger.info(f"Making test query")
    with conn.cursor() as cur:
        data = cur.execute("SELECT * FROM test_table").fetchall()
        print(data)
        logger.info(f"Test query successful")

    asyncio.run(serve())
    NodeConnectorServicer.orchestrator.check_queues()
