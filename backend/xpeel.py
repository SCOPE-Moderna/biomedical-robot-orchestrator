from __future__ import annotations

import logging
import socket
from queue import SimpleQueue, Queue
from node_connector_pb2.xpeel_pb2 import XPeelStatusResponse

import time

logger = logging.getLogger(__name__)


class XPeelMessage:
    def __init__(self, msg):

        self.raw_msg: str = msg
        split_msg = msg[1:].split(":")
        self.type = split_msg[0]

        if len(split_msg) == 2:
            self.raw_payload = split_msg[1]
            self.payload: list[str] = self.raw_payload.split(",")
        else:
            self.raw_payload = ""
            self.payload = []

    def to_xpeel_status_response(self) -> XPeelStatusResponse | None:
        if self.type != "ready":
            return XPeelStatusResponse(error_code_1=-1, error_code_2=-1, error_code_3=-1)
        int_payload = [int(x) for x in self.payload]
        return XPeelStatusResponse(
            error_code_1=int_payload[0],
            error_code_2=int_payload[1],
            error_code_3=int_payload[2],
        )

    def __repr__(self) -> str:
        return f"<XPeelMessage type={self.type} payload=({self.payload})>"


class XPeel:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self._connect()
        self.q = Queue()
        self.recv_queue = SimpleQueue()
        logger.info(f"Connected on {addr}:{port}!")

    def _connect(self):
        self.sock_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_conn.settimeout(5)
        self.sock_conn.connect((self.addr, self.port))

    def send(self, data: str):
        try:
            logger.debug(f"Sending data: {data}")
            self.sock_conn.sendall((data + "\r\n").encode())
        except BrokenPipeError:
            logger.info("Connection lost, reconnecting...")
            self._connect()
            self.send(data)

    def recv(self) -> str | None:
        if self.recv_queue.qsize() > 0:
            msg = self.recv_queue.get()
            logger.debug(f"recv: ({msg}) from queue, {self.recv_queue.qsize()} remaining in queue")
            return msg

        try:
            logger.debug("Attempting to receive data...")
            data = self.sock_conn.recv(1024).decode()
        except BrokenPipeError:
            self._connect()
            return self.recv()
        except TimeoutError:
            logger.debug("Timeout error, trying again...")
            return self.recv()

        if len(data) == 0:
            return

        # split data into list of strings
        msgs = data.split("\r\n")
        for msg in msgs:
            stripped = msg.strip()
            if len(stripped) > 0:
                self.recv_queue.put(stripped)

        msg = self.recv_queue.get()
        logger.debug(f"recv: from device, returning {msg}, {self.recv_queue.qsize()} in queue")
        return msg

    def wait_for_type(self, cmd_type: str | list[str]) -> XPeelMessage:
        if type(cmd_type) == str:
            cmd_type = [cmd_type]
        logger.debug(f"waiting for type {cmd_type}")
        while True:
            msg = XPeelMessage(self.recv())
            logger.debug(f"waiting for type {cmd_type}, got {msg.type}")
            if msg.type in cmd_type:
                return msg

    def status(self) -> XPeelMessage:
        self.send("*stat")
        return self.wait_for_type("ready")

    def reset(self) -> XPeelMessage:
        self.send("*reset")
        return self.wait_for_type(["ready"])

    def seal_check(self) -> XPeelMessage:
        self.send("*sealcheck")
        return self.wait_for_type("ready")

    def tape_remaining(self) -> XPeelMessage:
        self.send("*tapeleft")
        return self.wait_for_type("tape")

    def peel(self, param, adhere) -> XPeelMessage:
        self.send(f"*xpeel:{param}{adhere}")
        return self.wait_for_type("ready")

    def disconnect(self):
        self.sock_conn.close()
