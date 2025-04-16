from __future__ import annotations

import asyncio
import logging

from backend.devices.device_abc import AbstractConnector
from backend.node_connector_pb2.xpeel_pb2 import XPeelStatusResponse

logger = logging.getLogger(__name__)


class XPeelConnector(AbstractConnector):
    def __init__(self, ip_addr, port):
        super().__init__(ip_addr, port)
        self.recv_queue: asyncio.Queue[XPeelMessage] = asyncio.Queue()

        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.reader_task: asyncio.Task | None = None

    async def connect_device(self) -> None:
        """
        Connect to the XPeel by opening a TCP socket.
        :return: None
        """
        self.reader, self.writer = await asyncio.open_connection(
            self.ip_addr, self.port
        )
        logger.info(f"Connected to XPeel on {self.ip_addr}:{self.port}")
        self.reader_task = asyncio.create_task(self._recv_loop())

    async def _recv_loop(self):
        """
        Async loop to receive messages from the socket.

        Whenever data is ready on the socket, messages are split by CRLF,
        then added to the queue, which is read from when `self.recv_type` is called.
        :return: None
        """
        while True:
            try:
                data = await self.reader.read(1024)
                if not data:
                    logger.debug("No data received")
                    continue

                decoded = data.decode()
                logger.debug(f"Raw data from XPeel: {decoded}")
                msgs = decoded.split("\r\n")

                for msg in msgs:
                    stripped = msg.strip()
                    if stripped:
                        await self.recv_queue.put(XPeelMessage(stripped))
                        logger.debug(f"XPeel message added to queue: {stripped}")
            except (BrokenPipeError, ConnectionResetError):
                logger.info("XPeel connection lost during read, reconnecting")
                await self.connect_device()
            except Exception as e:
                logger.error(f"XPeel recv loop error: {e}")
                break

    async def send(self, data: str) -> None:
        """
        Send a message to the XPeel. Sent immediately.

        :param data: Command to send to the XPeel. Do not append newlines - this is done automatically.
        :return: None - use self.recv_type() to get a response.
        """
        try:
            logger.debug(f"Sending data to XPeel: {data}")
            self.writer.write((data + "\r\n").encode())
            await self.writer.drain()
        except BrokenPipeError:
            logger.info("XPeel connection lost during write, reconnecting")
            await self.connect_device()
            await self.send(data)

    async def recv_type(self, cmd_type: str) -> XPeelMessage:
        logger.debug(f"Attempting to receive command of type {cmd_type} from XPeel")
        while True:
            msg = await self.recv_queue.get()
            logger.debug(
                f"Received from XPeel queue: {msg}, attempting to receive command with {cmd_type}"
            )

            if msg.type == cmd_type:
                return msg

    async def flush_msgs(self) -> None:
        """
        Flush messages from the queue. Should be called before sending a command,
        since the XPeel may send random ready/ack messages.
        :return: None
        """
        while not self.recv_queue.empty():
            await self.recv_queue.get()

    async def execute_command(
        self, command: str, return_cmd_type: str = "ready"
    ) -> XPeelMessage:
        """
        Send a `command` to the XPeel, and receive a message of `return_cmd_type` back.
        Recommended way to send a command to the XPeel.
        :param command: Command without appended newlines to send to the XPeel.
        :param return_cmd_type: Command type to wait for after sending `command`.
        :return: XPeelMessage of type `return_cmd_type`.
        """
        logger.debug(
            f"Attempting to execute command of type {return_cmd_type} from XPeel"
        )
        await self.flush_msgs()
        await self.send(command)
        return await self.recv_type(return_cmd_type)

    async def reset(self) -> XPeelMessage:
        return await self.execute_command("*reset")

    async def status(self) -> XPeelMessage:
        return await self.execute_command("*stat")

    async def peel(self, param: int, adhere: int) -> XPeelMessage:
        return await self.execute_command(f"*xpeel:{param}{adhere}")

    async def seal_check(self) -> XPeelMessage:
        return await self.execute_command("*sealcheck")

    async def tape_remaining(self) -> XPeelMessage:
        return await self.execute_command("*tapeleft", "tape")


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
            return XPeelStatusResponse(
                error_code_1=-1, error_code_2=-1, error_code_3=-1
            )
        int_payload = [int(x) for x in self.payload]
        return XPeelStatusResponse(
            error_code_1=int_payload[0],
            error_code_2=int_payload[1],
            error_code_3=int_payload[2],
        )

    def __repr__(self) -> str:
        return f"<XPeelMessage type={self.type} payload=({self.payload})>"
