import logging
from concurrent import futures
import grpc
from service_pb2 import service_pb2_grpc, service_pb2


class NodeConnector(service_pb2_grpc.NodeConnectorServicer):
    def Ping(self, request, context):
        return service_pb2.PingResponse(message=f"Pong ({request.message})", success=True)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_NodeConnectorServicer_to_server(NodeConnector(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
