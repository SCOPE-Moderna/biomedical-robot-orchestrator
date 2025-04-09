from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

import logging
import sys
from concurrent import futures
from os import getenv
from pathlib import Path

import grpc
import asyncio


from flows.graph import FlowsGraph, Node
from node_connector_pb2 import (
    xpeel_pb2,
    node_connector_pb2,
    node_connector_pb2_grpc,
    ipc_template_pb2_grpc,
)
from xpeel import XPeel
from db.flow_runs import FlowRun
from db.conn import conn

from orchestrator import Orchestrator

from python_ipc_servicer import IpcConnectionServicer


logger = logging.getLogger(__name__)


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
    orchestrator = Orchestrator()

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
    async def XPeelStatus(self, request: xpeel_pb2.XPeelGeneralRequest, context):
        logger.info("Received XPeelStatus request")
        function_args = {}
        logger.info(f"Fetched excecuting FlowRun ID: {request.metadata.flow_run_id}")
        result = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "status",
            function_args,
        )
        logger.info(f"XPeelStatus response: {result}")
        return result.to_xpeel_status_response()

    async def XPeelReset(self, request: xpeel_pb2.XPeelGeneralRequest, context):
        logger.info("Received XPeelReset request")
        function_args = {}
        logger.info(f"Fetched excecuting FlowRun ID: {request.metadata.flow_run_id}")
        result = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "reset",
            function_args,
        )
        logger.info(f"XPeelReset response: {result}")
        return result.to_xpeel_status_response()

    async def XPeelXPeel(self, request: xpeel_pb2.XPeelXPeelRequest, context):
        logger.info(f"Received XPeelXPeel request: {request}")
        function_args = {"param": request.set_number, "adhere": request.adhere_time}
        logger.info(
            f"Fetched excecuting FlowRun ID: {request.metadata.flow_run_id}, {function_args}"
        )
        result = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "peel",
            function_args,
        )
        logger.info(f"XPeelXPeel response: {result}")
        return await result.to_xpeel_status_response()

    async def XPeelSealCheck(self, request, context):
        logger.info("Received XPeelSealCheck request")
        function_args = {}
        logger.info(f"Fetched excecuting FlowRun ID: {request.metadata.flow_run_id}")
        msg = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "seal_check",
            function_args,
        )
        has_seal = msg.type == "ready" and msg.payload[0] == "04"
        logger.info(f"XPeelSealCheck response: {has_seal}")
        return xpeel_pb2.XPeelSealCheckResponse(seal_detected=has_seal)

    async def XPeelTapeRemaining(self, request, context):
        logger.info("Received XPeelTapeRemaining request")
        function_args = {}
        logger.info(f"Fetched excecuting FlowRun ID: {request.metadata.flow_run_id}")
        msg = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "tape_remaining",
            function_args,
        )
        logger.info(f"XPeelTapeRemaining response: {msg}")
        return xpeel_pb2.XPeelTapeRemainingResponse(
            deseals_remaining=int(msg.payload[0]) * 10,
            take_up_spool_space_remaining=int(msg.payload[1]) * 10,
        )


async def serve():

    port = 50051

    logger.info(f"Starting gRPC server on port {port}")
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))

    ncs = NodeConnectorServicer()
    await ncs.orchestrator.connect_instruments()
    node_connector_pb2_grpc.add_NodeConnectorServicer_to_server(ncs, server)

    ipc_template_pb2_grpc.add_IpcCommunicationServiceServicer_to_server(
        IpcConnectionServicer(), server
    )
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    logger.info("gRPC server started")

    asyncio.create_task(NodeConnectorServicer.orchestrator.check_queues())

    await server.wait_for_termination()
    logger.info("gRPC server stopped")


if __name__ == "__main__":

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    graph = FlowsGraph(
        getenv("NODE_RED_DIR") or Path.joinpath(Path.home(), ".node-red").__str__()
    )

    logger.info(f"Connecting to database")
    logger.info(f"Connected to database")
    logger.info(f"Making test query")
    with conn.cursor() as cur:
        data = cur.execute("SELECT * FROM test_table").fetchall()
        print(data)
        logger.info(f"Test query successful")

    asyncio.run(serve())
