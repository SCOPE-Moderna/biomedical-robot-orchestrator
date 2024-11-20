from __future__ import annotations

import socket
from queue import SimpleQueue
from node_connector_pb2.xpeel_pb2 import XPeelStatusResponse


class XPeelMessage:
    def __init__(self, msg):
        self.raw_msg: str = msg
        split_msg = msg[1:].split(":")
        self.type = split_msg[0]

        if len(split_msg) == 2:
            self.raw_payload = split_msg[1]
            self.payload: list[str] = self.raw_payload.split(",")

    def to_xpeel_status_response(self) -> XPeelStatusResponse | None:
        if self.type != "ready":
            return None
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
        self.sock_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock_conn.connect((addr, port))
        self.recv_queue = SimpleQueue()
        print(f"Connected on {addr}:{port}!")

    def send(self, data: str):
        self.sock_conn.sendall((data + "\r\n").encode())

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

    def wait_for_type(self, cmd_type: str) -> XPeelMessage:
        while True:
            msg = XPeelMessage(self.recv())
            if msg.type == cmd_type:
                return msg

    def status(self) -> XPeelMessage:
        self.send("*stat")
        return self.wait_for_type("ready")

    def reset(self) -> XPeelMessage:
        self.send("*reset")
        return self.wait_for_type("ready")

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
