import logging
from concurrent import futures
import grpc
from node_connector_pb2 import xpeel_pb2, node_connector_pb2, node_connector_pb2_grpc

class NodeConnector(node_connector_pb2_grpc.NodeConnectorServicer):
    def Ping(self, request, context):
        return node_connector_pb2.PingResponse(message=f"Pong ({request.message})", success=True)

    def XPeelStatus(self, request, context):
        return xpeel_pb2.XPeelStatusResponse(
            error_code_1=00,
            error_code_2=00,
            error_code_3=00,
        )

    def XPeelReset(self, request, context):
        return xpeel_pb2.XPeelStatusResponse(
            error_code_1=10,
            error_code_2=20,
            error_code_3=30,
        )

    def XPeelXPeel(self, request, context):
        return xpeel_pb2.XPeelStatusResponse(
            error_code_1=40,
            error_code_2=50,
            error_code_3=60,
        )

    def XPeelSealCheck(self, request, context):
        return xpeel_pb2.XPeelSealCheckResponse(seal_detected=False)

    def XPeelTapeRemaining(self, request, context):
        return xpeel_pb2.XPeelTapeRemainingResponse(
            deseals_remaining=100,
            take_up_spool_space_remaining=100
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
