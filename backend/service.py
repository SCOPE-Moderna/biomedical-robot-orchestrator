from __future__ import annotations

import logging
import sys
from concurrent import futures

import grpc

from node_connector_pb2 import xpeel_pb2, node_connector_pb2, node_connector_pb2_grpc
from xpeel import XPeel

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, DirCreatedEvent, FileCreatedEvent, DirDeletedEvent, \
    FileDeletedEvent, DirMovedEvent, FileMovedEvent

logger = logging.getLogger(__name__)

xpeel = XPeel("192.168.0.201", 1628)


class NodeConnectorServicer(node_connector_pb2_grpc.NodeConnectorServicer):
    def Ping(self, request, context):
        logger.info(f"Received ping: {request.message}")
        return node_connector_pb2.PingResponse(message=f"Pong ({request.message})", success=True)

    def XPeelStatus(self, request, context):
        logger.info("Received XPeelStatus request")
        msg = xpeel.status()
        logger.info(f"XPeelStatus response: {msg}")
        return msg.to_xpeel_status_response()

    def XPeelReset(self, request, context):
        logger.info("Received XPeelReset request")
        msg = xpeel.reset()
        logger.info(f"XPeelReset response: {msg}")
        return msg.to_xpeel_status_response()

    def XPeelXPeel(self, request: xpeel_pb2.XPeelXPeelRequest, context):
        logger.info(f"Received XPeelXPeel request: {request}")
        msg = xpeel.peel(request.set_number, request.adhere_time)
        logger.info(f"XPeelXPeel response: {msg}")
        return msg.to_xpeel_status_response()

    def XPeelSealCheck(self, request, context):
        logger.info("Received XPeelSealCheck request")
        msg = xpeel.seal_check()
        has_seal = msg.type == "ready" and msg.payload[0] == "04"
        logger.info(f"XPeelSealCheck response: {has_seal}")
        return xpeel_pb2.XPeelSealCheckResponse(seal_detected=has_seal)

    def XPeelTapeRemaining(self, request, context):
        logger.info("Received XPeelTapeRemaining request")
        msg = xpeel.tape_remaining()
        logger.info(f"XPeelTapeRemaining response: {msg}")
        return xpeel_pb2.XPeelTapeRemainingResponse(
            deseals_remaining=int(msg.payload[0]) * 10,
            take_up_spool_space_remaining=int(msg.payload[1]) * 10
        )

observer = Observer()

def serve():
    port = 50051

    logger.info(f"Starting gRPC server on port {port}")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_connector_pb2_grpc.add_NodeConnectorServicer_to_server(NodeConnectorServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    watch()
    server.start()
    server.wait_for_termination()
    logger.info("gRPC server stopped")
    observer.stop()

class MyEventHandler(FileSystemEventHandler):
    # def on_modified(self, event):
    #     if event.src_path.endswith("flows.json"):
    #         logger.info(f"flows.json modified: {event.src_path}")
    #     else:
    #         logger.info(f"modified: {event.src_path}")
    #
    # def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
    #     logger.info(f"created: {event.src_path}")
    #
    # def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
    #     logger.info(f"deleted: {event.src_path}")

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        if event.dest_path.endswith("flows.json"):
            logger.info(f"flows.json moved: {event.dest_path}")

            # print out the number of lines in flows.json
            with open(event.dest_path) as f:
                lines = f.readlines()
                logger.info(f"flows.json line count: {len(lines)}")
        else:
            logger.info(f"moved: {event.dest_path}")

def watch():
    event_handler = MyEventHandler()
    observer.schedule(event_handler, path='/home/aquarium/.node-red', recursive=False)
    observer.start()
    observer.join()


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    serve()
