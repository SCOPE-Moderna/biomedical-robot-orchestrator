from __future__ import annotations

from .node_runs import NodeRun
from .conn import conn


class Instrument:
    def __init__(
            self,
            id: int,
            name: str,
            type: str,
            connection_method: str,
            connection_data: str | None,
            status: str,
            in_use_by: int | None,
    ):
        self.id = id
        self.name = name
        self.type = type
        self.connection_method = connection_method
        self.connection_data = connection_data
        self.status = status
        self.in_use_by = in_use_by

    @classmethod
    def fetch_from_id(cls, id: int) -> NodeRun:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM node_runs WHERE id = %s", (id,))
            row = cur.fetchone()
            return cls(*row)
        
    def set_in_use_by(self, node_run_id: int | None, node_run: NodeRun | None):
        if node_run is not None:
            node_run_id = node_run.id

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE instruments SET in_use_by = %s WHERE id = %s",
                (node_run_id, self.id),
            )