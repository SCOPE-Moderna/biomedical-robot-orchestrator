from __future__ import annotations
from dotenv import load_dotenv

from backend.devices.xpeel import (
    xpeel_message_dict_to_xpeel_status_response,
    XPeelMessageDict,
)
from backend.node_connector_pb2.metadata_pb2 import ResponseMetadata

load_dotenv()

import logging
import sys
from concurrent import futures

import grpc
import asyncio


from backend.flows.graph import flows_graph
from backend.node_connector_pb2 import (
    ui_pb2,
    xpeel_pb2,
    node_connector_pb2,
    ur3_pb2,
    node_connector_pb2_grpc,
    ipc_template_pb2_grpc,
)
from backend.db.flow_runs import FlowRun
from backend.db.conn import conn

from backend.orchestrator import Orchestrator

from backend.ipc.python_ipc_servicer import IpcConnectionServicer


logger = logging.getLogger(__name__)


class NodeConnectorServicer(node_connector_pb2_grpc.NodeConnectorServicer):
    orchestrator = Orchestrator()

    def Ping(self, request, context):
        logger.info(f"Received ping: {request.message}")
        return node_connector_pb2.PingResponse(
            message=f"Pong ({request.message})", success=True
        )

    def GetRunningFlows(
        self, request: ui_pb2.GetRunningFlowsRequest, context
    ) -> ui_pb2.GetRunningFlowsResponse:
        flows = FlowRun.query(status="in-progress", order_by="id DESC")
        proto_flows = [run.to_proto() for run in flows]

        return ui_pb2.GetRunningFlowsResponse(flow_runs=proto_flows)

    def StartFlow(self, request: node_connector_pb2.StartFlowRequest, context):
        logger.info("Received StartFlow request")
        run = FlowRun.create(
            name=request.flow_name, start_flow_node_id=request.start_node_id
        )
        logger.info(f"Starting run: {run.id}")
        response = node_connector_pb2.StartFlowResponse(
            success=True, run_id=str(run.id)
        )
        logger.info("Received StartFlow response")
        return response

    async def XPeelStatus(self, request: xpeel_pb2.XPeelGeneralRequest, context):
        logger.info("Received XPeelStatus request")
        function_args = {}
        logger.info(f"Fetched executing FlowRun ID: {request.metadata.flow_run_id}")
        result: XPeelMessageDict = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "status",
            function_args,
        )
        logger.info(f"XPeelStatus response: {result}")
        return xpeel_message_dict_to_xpeel_status_response(result)

    async def XPeelReset(self, request: xpeel_pb2.XPeelGeneralRequest, context):
        logger.info("Received XPeelReset request")
        function_args = {}
        logger.info(f"Fetched executing FlowRun ID: {request.metadata.flow_run_id}")
        result: XPeelMessageDict = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "reset",
            function_args,
        )
        logger.info(f"XPeelReset response: {result}")
        return xpeel_message_dict_to_xpeel_status_response(result)

    async def XPeelXPeel(self, request: xpeel_pb2.XPeelXPeelRequest, context):
        logger.info(f"Received XPeelXPeel request: {request}")
        function_args = {"param": request.set_number, "adhere": request.adhere_time}
        logger.info(
            f"Fetched executing FlowRun ID: {request.metadata.flow_run_id}, {function_args}"
        )
        result: XPeelMessageDict = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "peel",
            function_args,
        )
        logger.info(f"XPeelXPeel response: {result}")
        return xpeel_message_dict_to_xpeel_status_response(result)

    async def XPeelSealCheck(self, request, context):
        logger.info("Received XPeelSealCheck request")
        function_args = {}
        logger.info(f"Fetched executing FlowRun ID: {request.metadata.flow_run_id}")
        msg: XPeelMessageDict = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "seal_check",
            function_args,
        )
        has_seal = msg["type"] == "ready" and msg["payload"][0] == "04"
        logger.info(f"XPeelSealCheck response: {has_seal}")
        return xpeel_pb2.XPeelSealCheckResponse(seal_detected=has_seal)

    async def XPeelTapeRemaining(self, request, context):
        logger.info("Received XPeelTapeRemaining request")
        function_args = {}
        logger.info(f"Fetched executing FlowRun ID: {request.metadata.flow_run_id}")
        msg: XPeelMessageDict = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "tape_remaining",
            function_args,
        )
        logger.info(f"XPeelTapeRemaining response: {msg}")
        return xpeel_pb2.XPeelTapeRemainingResponse(
            deseals_remaining=int(msg["payload"][0]) * 10,
            take_up_spool_space_remaining=int(msg["payload"][1]) * 10,
        )

    async def UR3MoveToJointWaypoint(
        self, request: ur3_pb2.UR3MoveToJointWaypointRequest, context
    ):
        logger.info("Received UR3MoveToJointWaypoint request")
        function_args = {"waypoint_number": request.waypoint_number}
        logger.info(f"Fetched executing FlowRun ID: {request.metadata.flow_run_id}")
        msg = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "move_to_joint_waypoint",
            function_args,
            movement=True,
        )
        logger.info(f"UR3MoveToJointWaypoint response: {msg}")
        return ur3_pb2.UR3MoveToJointWaypointResponse(success=True)

    async def UR3Move(self, request: ur3_pb2.UR3MoveRequest, context):
        logger.info("Received UR3Move request")

        function_args = {
            "source_waypoint_number": request.source_waypoint_number,
            "destination_waypoint_number": request.destination_waypoint_number,
            "delay_between_movements": request.delay_between_movements,
        }

        logger.info(f"Fetched executing FlowRun ID: {request.metadata.flow_run_id}")
        msg = await NodeConnectorServicer.orchestrator.run_node(
            request.metadata.flow_run_id,
            request.metadata.executing_node_id,
            request.metadata.instrument_id,
            "move",
            function_args,
            movement=True,
        )
        logger.info(f"UR3Move response: {msg}")
        return ur3_pb2.UR3MoveResponse(metadata=ResponseMetadata(success=True))


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

    logger.info(f"Connecting to database")
    logger.info(f"Connected to database")
    logger.info(f"Making test query")
    with conn.cursor() as cur:
        data = cur.execute("SELECT * FROM test_table").fetchall()
        print(data)
        logger.info(f"Test query successful")

    asyncio.run(serve())
