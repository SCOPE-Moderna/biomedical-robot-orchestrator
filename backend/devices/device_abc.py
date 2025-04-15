from __future__ import annotations

from typing import TypedDict, Callable, NotRequired
import logging
from abc import ABC, abstractmethod
from queue import Queue

from backend.ipc.python_ipc_servicer import send_message_to_client

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
