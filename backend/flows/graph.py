from __future__ import annotations

import logging
import json
from os import path

from watchdog.events import FileSystemEventHandler, DirMovedEvent, FileMovedEvent
from watchdog.observers import Observer

from .types import RawNode

# Node types to ignore. Nodes without wires are ignored by default
IGNORE_NODE_TYPES = {"comment"}

logger = logging.getLogger(__name__)

observer = Observer()

class FlowsGraph:
    class FlowsJsonEventListener(FileSystemEventHandler):
        def __init__(self, on_flows_changed: callable[[dict], None]):
            self.on_flows_changed = on_flows_changed

        def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
            if event.dest_path.endswith("flows.json"):
                # print out the number of lines in flows.json
                with open(event.dest_path) as f:
                    json_file = json.load(f)
                    self.on_flows_changed(json_file)

    def __init__(self, node_red_dir: str):
        # self.graph is a dictionary of RawNodes, indexed by their id
        self.raw_graph: dict[str, RawNode] = {}
        # key: node id, value: nodes that forward to it
        self.input_graph: dict[str, list[RawNode]] = {}
        self.no_input_nodes: dict[str, None] = {}

        # read in the graph and process it
        logger.info("Reading and processing flows.json")
        with open(path.join(node_red_dir, "flows.json")) as f:
            json_file = json.load(f)
            self._on_flows_changed(json_file)
        logger.debug(f"no_input_nodes: {self.no_input_nodes}")
        logger.info(f"Successfully processed flows.json, {len(self.raw_graph)} nodes found")

        self.listener = self.FlowsJsonEventListener(self._on_flows_changed)
        observer.schedule(self.listener, path=node_red_dir, recursive=False)
        observer.start()

    def __del__(self):
        observer.stop()
        observer.join()

    def _on_flows_changed(self, json_file: list[RawNode]):
        logger.info("flows.json updated, processing")

        # clear the graph
        self.raw_graph = {}
        self.input_graph = {}
        self.no_input_nodes = {}
        # parse all nodes into RawNodes
        for node in json_file:
            if "wires" not in node or node["type"] in IGNORE_NODE_TYPES:
                continue

            self.raw_graph[node["id"]] = node

            if len(node["wires"]) > 0:
                for output_id in node["wires"]:
                    for input_id in output_id:
                        if input_id not in self.input_graph:
                            self.input_graph[input_id] = []

                        self.input_graph[input_id].append(node)

                        if input_id in self.no_input_nodes:
                            del self.no_input_nodes[input_id]

            # if the node has anything pointing into it,
            # remove from no_input_nodes
            if node["id"] in self.input_graph:
                if node["id"] in self.no_input_nodes:
                    del self.no_input_nodes[node["id"]]
            else:
                self.no_input_nodes[node["id"]] = None

        logger.debug(f"no_input_nodes: {self.no_input_nodes}")
        logger.info(f"flows.json update successful, {len(self.raw_graph)} nodes found")

    def get_node(self, node_id: str) -> Node | None:
        if node_id not in self.raw_graph:
            return None

        return Node(self, self.raw_graph[node_id])

    def __repr__(self):
        return f"<FlowsGraph num_nodes={len(self.raw_graph)}, no_input_nodes={self.no_input_nodes}>"

class Node:
    def __init__(self, graph: FlowsGraph, raw_node: RawNode):
        self.graph = graph
        self.raw_node = raw_node
        self.id = self.raw_node["id"]

    def next_nodes(self, output_index = 0) -> list[Node] | None:
        output_ids = self.raw_node["wires"][output_index]
        if len(output_ids) == 0:
            return None

        return [Node(self.graph, self.graph.raw_graph[output_id]) for output_id in output_ids]

    def __repr__(self) -> str:
        return f"<Node id={self.raw_node['id']} type={self.raw_node['type']}>"
