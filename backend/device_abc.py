from __future__ import annotations
from typing import TypedDict, Callable, NotRequired
import logging

# ABC
from abc import ABC, abstractmethod

# UR3
import rtde_receive
import rtde_control

# xpeel
import socket
from queue import SimpleQueue, Queue
from python_ipc_servicer import send_message_to_client

logger = logging.getLogger(__name__)


class GeneralizedInput(TypedDict):
    """
    GeneralizedInput contains all the possible inputs that can be sent to a device
    to control it.
    """

    x_position: NotRequired[int]
    y_position: NotRequired[int]
    waypoint_number: NotRequired[int]
    string_input: NotRequired[str]
    ip_add: NotRequired[str]
    sub_function_name: NotRequired[str]


class AbstractConnector(ABC):
    """
    AbstractConnector is the base class for all device connectors.

    It provides a common interface for all connectors and defines the
    methods that must be implemented by each connector.

    Children must implement connect_device() and all functions to be executed.
    """

    def __init__(self, ip_addr, port):
        self.ip_addr = ip_addr
        self.port = port
        self.q = Queue()
        self.connect_device()

    @abstractmethod
    def connect_device(self):
        pass

    def call_node_interface(self, node_name: str, relevant_data: GeneralizedInput):
        """
        The method with which the orchestrator will call the robot. It will send an "action" to perform.
        If the node function call has output then it will return it.
        """

        node_function: Callable[[AbstractConnector, GeneralizedInput], None] = getattr(
            self.__class__, node_name
        )

        data_output = node_function(self, relevant_data)

        if data_output:
            return data_output
        else:
            return None


class AbstractIPC(AbstractConnector):
    """
    AbstractConnector that uses IPC to connect to the device.
    """

    # OVERWRITE THIS
    client_pid = None

    def call_node_interface(self, node_name, relevant_data: GeneralizedInput):

        if self.client_pid:
            send_message_to_client(self.client_pid, relevant_data)
        else:
            raise Exception("Invalid client process ID. Did the connection succeed?")


class UrRobot(AbstractConnector):
    """
    Implementation of the UR3 robot as an AbstractConnector.
    """

    waypoint_J1 = [0.0, -1.3, 0.0, -1.3, 0.0, 0.0]
    waypoint_J2 = [
        0.0016515760216861963,
        -1.5747383276568812,
        0.002468585968017578,
        -1.5649493376361292,
        0.007608110550791025,
        0.0018253473099321127,
    ]
    waypoints = [waypoint_J1, waypoint_J2]

    # connect device implementation
    def connect_device(self):
        logger.debug("ur3: attempting receive interface connection")
        self.receive_interface = rtde_receive.RTDEReceiveInterface(self.ip_addr)

        logger.debug("ur3: attempting control interface connection")
        self.control_interface = rtde_control.RTDEControlInterface(self.ip_addr)

    # specific implementations
    def retrieve_state_joint(self, _: GeneralizedInput):
        return self.receive_interface.getActualQ()

    def general_control_call(self, general_input: GeneralizedInput):
        # check if this works TODO
        if "string_input" not in general_input:
            raise Exception("No string input provided")

        general_control_function = getattr(
            type(self.control_interface), general_input["string_input"]
        )

        return general_control_function(self.control_interface)

    def general_receive_call(self, general_input: GeneralizedInput):
        if "string_input" not in general_input:
            raise Exception("No string input provided")

        general_receive_function = getattr(
            type(self.receive_interface), general_input["string_input"]
        )

        return general_receive_function(self.control_interface)

    def retrieve_state_linear(self, general_input: GeneralizedInput):
        return self.receive_interface.getActualTCPPose()

    # NODE
    def move_j_waypoint(self, general_input):
        target = self.waypoints[general_input.waypoint_number]
        logger.log(f"ur3: moving to {target}")
        self.control_interface.moveJ(target, True)


class XPeelConnector(AbstractConnector):
    def __init__(self, ip_addr, port):
        super().__init__(ip_addr, port)
        self.sock_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv_queue = SimpleQueue()

    def connect_device(self):
        self.sock_conn.connect((self.ip_addr, self.port))
        logger.log(f"XPeel (ABC) Connected on {self.ip_addr}:{self.port}!")

    # helper method. not to be directly called
    def send(self, data: str):
        self.sock_conn.sendall((data + "\r\n").encode())

    # helper method. Not to be called
    def recv(self) -> str | None:
        if self.recv_queue.qsize() > 0:
            return self.recv_queue.get()

        data = self.sock_conn.recv(1024).decode()
        if len(data) == 0:
            return

        # split data into list of strings
        msgs = data.split("\r\n")
        for msg in msgs:
            self.recv_queue.put(msg.strip())

        return self.recv_queue.get()

    def waive_ack(self):
        while True:
            msg = self.recv()
            if msg is None or msg[1:4] == "ack":
                continue

            return msg

    def status(self, general_input):
        self.send("*stat")
        return self.recv()

    def reset(self, general_input):
        self.send("*reset")
        return self.waive_ack()

    def seal_check(self, general_input):
        self.send("*sealcheck")
        return self.waive_ack()

    def tape_remaining(self, general_input):
        self.send("*tapeleft")
        print("sent tape cmd")
        while True:
            msg = self.recv()
            if msg is not None and "tape" in msg[1:5]:
                return msg

    def disconnect(self, general_input):
        self.sock_conn.close()
