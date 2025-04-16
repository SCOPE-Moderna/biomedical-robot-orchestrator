from __future__ import annotations

from typing import TYPE_CHECKING
import queue

if TYPE_CHECKING:
    from backend.devices.device_abc import ABCRobotCommand

from backend.node_connector_pb2 import ipc_template_pb2, ipc_template_pb2_grpc


client_incoming_queues = {}  # key = pid,
client_outgoing_queues = {}  # key = pid


class IpcConnectionServicer(ipc_template_pb2_grpc.IpcCommunicationServiceServicer):
    def ReportStatus(self, request_iterator, context):

        try:
            for status_update in request_iterator:
                client_pid = status_update.client_pid
                status_message = status_update.status_message

                print(f"received status_update: {status_message}")
                client_incoming_queues[client_pid].put(status_message)
                # TODO do something
        except Exception as e:
            print(f"Error reading from client {e}")
        response = ipc_template_pb2.StatusUpdateResponse()
        return response

    def GetCommand(self, request, context):

        client_pid = request.client_pid
        print(f"Client {client_pid} connected.")

        # Create a dedicated queue for this client's outgoing messages.
        response_queue = queue.Queue()
        update_queue = queue.Queue()
        client_incoming_queues[client_pid] = update_queue
        client_outgoing_queues[client_pid] = response_queue

        # Start a thread to process incoming messages from the client.
        try:
            print(f"Received from {client_pid}: {request}")
        except Exception as e:
            print(f"Error reading from client {client_pid}: {e}")

        # def read_client_messages():
        #     try:
        #         print(f"Received from {client_id}: {request}")
        #     except Exception as e:
        #         print(f"Error reading from client {client_id}: {e}")

        try:
            # Main loop: wait for messages in the response queue.
            while True:
                try:
                    # Block until a message is available.
                    message = response_queue.get(timeout=1.0)
                    yield message
                except queue.Empty:
                    # Optionally, check for termination conditions here.
                    pass
        finally:
            # Cleanup when the client disconnects.
            del client_outgoing_queues[client_pid]
            print(f"Client {client_pid} disconnected.")


###


def send_message_to_client(client_id, general_input: ABCRobotCommand):
    """
    Helper function to send a message to a specific client.
    """
    if client_id in client_outgoing_queues:

        function_input = generalized_function_input_helper(general_input)
        response_message = ipc_template_pb2.CommandResponse(
            FunctionInput=function_input
        )
        client_outgoing_queues[client_id].put(response_message)
        print(f"Sent to {client_id}")
    else:
        print(f"Client {client_id} is not connected.")


def generalized_function_input_helper(general_input: ABCRobotCommand):
    outgoing_message = ipc_template_pb2.GeneralizedFunctionInput()

    outgoing_message.x_position = general_input.x_position
    outgoing_message.y_position = general_input.y_position
    outgoing_message.waypoint_number = general_input.waypoint_number
    outgoing_message.string_input = general_input.string_input
    outgoing_message.ip_add = general_input.ip_add
    outgoing_message.sub_function_name = general_input.sub_function_name

    return outgoing_message
