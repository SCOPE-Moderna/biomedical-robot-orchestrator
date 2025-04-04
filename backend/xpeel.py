from __future__ import annotations

import logging
import socket
from queue import SimpleQueue, Queue
import asyncio
from asyncio import Queue as AsyncQueue
from node_connector_pb2.xpeel_pb2 import XPeelStatusResponse

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


class XPeel:
    def __init__(self, addr, port):
        logger.info("XPEEL INIT")
        print("XPEEL INIT FROM PRINT")
        self.addr = addr
        self.port = port
        self.q = Queue()
        self.recv_queue = AsyncQueue()

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.addr, self.port)
        logger.info(f"Connected to {self.addr}:{self.port}")
        self.loop = asyncio.get_event_loop()
        self.reader_task = self.loop.create_task(self._async_recv_loop())

    async def _async_recv_loop(self):
        logger.info("Running async loop")
        while True:
            try:
                # data = await self.loop.sock_recv(self.sock_conn, 1024)
                data = await self.reader.read(1024)
                if not data:
                    logger.info("No data received.")
                    continue

                logger.debug("RAW DATA: " + data.decode())
                msgs = data.decode().split("\r\n")
                for msg in msgs:
                    stripped = msg.strip()
                    if stripped:
                        await self.recv_queue.put(stripped)
                        logger.debug(f"Message added to queue: {stripped}")
            except (BrokenPipeError, ConnectionResetError):
                logger.info("Connection lost, reconnecting...")
                await self.connect()
            except Exception as e:
                logger.error(f"Error in async recv loop: {e}")
                break

    async def send(self, data: str):
        try:
            logger.debug(f"Sending data: {data}")
            self.writer.write((data + "\r\n").encode())
            await self.writer.drain()
        except BrokenPipeError:
            logger.info("Connection lost, reconnecting...")
            await self.connect()
            await self.send(data)

    async def recv(self) -> str | None:
        """Retrieve a message from the asyncio queue."""
        msg = await self.recv_queue.get()
        logger.debug(
            f"recv: ({msg}) from queue, {self.recv_queue.qsize()} remaining in queue"
        )
        return msg

    async def wait_for_type(self, cmd_type: str | list[str]) -> XPeelMessage:
        if type(cmd_type) == str:
            cmd_type = [cmd_type]
        logger.debug(f"waiting for type {cmd_type}")
        while True:
            msg = XPeelMessage(await self.recv())
            logger.debug(f"waiting for type {cmd_type}, got {msg.type}")
            if msg.type in cmd_type:
                return msg

    async def flush_msgs(self) -> None:
        # empty message queue
        while not self.recv_queue.empty():
            await self.recv_queue.get()

    async def status(self) -> XPeelMessage:
        await self.flush_msgs()
        await self.send("*stat")
        return await self.wait_for_type("ready")

    async def reset(self) -> XPeelMessage:
        await self.flush_msgs()
        await self.send("*reset")
        return await self.wait_for_type("ready")

    async def seal_check(self) -> XPeelMessage:
        await self.flush_msgs()
        await self.send("*sealcheck")
        return await self.wait_for_type("ready")

    async def tape_remaining(self) -> XPeelMessage:
        await self.flush_msgs()
        await self.send("*tapeleft")
        return await self.wait_for_type("tape")

    async def peel(self, param, adhere) -> XPeelMessage:
        await self.flush_msgs()
        await self.send(f"*xpeel:{param}{adhere}")
        return await self.wait_for_type("ready")

    def disconnect(self):
        if self.writer:
            self.writer.close()
            asyncio.run(self.writer.wait_closed())
