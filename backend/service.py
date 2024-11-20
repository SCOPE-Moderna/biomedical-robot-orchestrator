import logging
from concurrent import futures
import grpc
from node_connector_pb2 import xpeel_pb2, node_connector_pb2, node_connector_pb2_grpc
from xpeel import XPeel

xpeel = XPeel("192.168.0.201", 1628)


class NodeConnector(node_connector_pb2_grpc.NodeConnectorServicer):
    def Ping(self, request, context):
        return node_connector_pb2.PingResponse(message=f"Pong ({request.message})", success=True)

    def XPeelStatus(self, request, context):
        return xpeel.status().to_xpeel_status_response()

    def XPeelReset(self, request, context):
        return xpeel.reset().to_xpeel_status_response()

    def XPeelXPeel(self, request: xpeel_pb2.XPeelXPeelRequest, context):
        return xpeel.peel(request.set_number, request.adhere_time).to_xpeel_status_response()

    def XPeelSealCheck(self, request, context):
        msg = xpeel.seal_check()
        has_seal = msg.type == "ready" and msg.payload[0] == "04"
        return xpeel_pb2.XPeelSealCheckResponse(seal_detected=has_seal)

    def XPeelTapeRemaining(self, request, context):
        msg = xpeel.tape_remaining()
        if msg.type != "tape":
            return xpeel_pb2.XPeelTapeRemainingResponse(
                deseals_remaining=-1,
                take_up_spool_space_remaining=-1
            )

        return xpeel_pb2.XPeelTapeRemainingResponse(
            deseals_remaining=int(msg.payload[0]) * 10,
            take_up_spool_space_remaining=int(msg.payload[1]) * 10
        )


def serve():
    port = 50051

    print(f"Starting gRPC server on port {port}")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_connector_pb2_grpc.add_NodeConnectorServicer_to_server(NodeConnector(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
