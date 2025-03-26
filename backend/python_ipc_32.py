
import time
#needs to run 32 bit python
from node_connector_pb2 import ipc_template_pb2,ipc_template_pb2_grpc
import grpc

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = ipc_template_pb2_grpc.IpcCommunicationServiceStub(channel)
        
        request = ipc_template_pb2.CommandRequest(command="test command")
        response = stub.ExecuteCommand(request)
        stub.AnotherCommand
        print("Received response from gRPC:")
        print(response)

while True:
    print("32 bit python running")
    time.sleep(1)
